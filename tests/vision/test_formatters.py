import pytest
from src.pipeline.vision.formatter import Formatter
from src.pipeline.vision.types import Block, FormattedOutput
from .fixtures.marker_samples import (
    SAMPLE_TEXT_BLOCK, 
    SAMPLE_EQUATION_BLOCK, 
    SAMPLE_FIGURE_BLOCK,
    SAMPLE_INLINE_MATH_BLOCK
)


class MockMarkerBlock:
    """Mock object that mimics Marker block structure"""
    def __init__(self, id, block_type, html, bbox, polygon, children=None, section_hierarchy=None, images=None, **kwargs):
        self.id = id
        self.block_type = block_type
        self.html = html
        self.bbox = bbox
        self.polygon = polygon
        self.children = children
        self.section_hierarchy = section_hierarchy or {}
        self.images = images or {}
        
        # Add any additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestFormatter:
    
    def test_extract_raw_content_equation(self):
        """Test LaTeX extraction from equation blocks"""
        block = MockMarkerBlock(**SAMPLE_EQUATION_BLOCK)
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should extract LaTeX from math tags
        assert raw_content == "x^2 + y^2 = 1"
    
    def test_extract_raw_content_text(self):
        """Test text extraction from text blocks"""
        block = MockMarkerBlock(**SAMPLE_TEXT_BLOCK)
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should extract clean text, removing HTML tags
        expected = "Question: Which function is monotonic in range [0, pi]?"
        assert raw_content == expected
    
    def test_extract_raw_content_inline_math(self):
        """Test text with inline math preservation"""
        block = MockMarkerBlock(**SAMPLE_INLINE_MATH_BLOCK)
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should preserve both text and inline LaTeX
        expected = "Solve for y: y^2 + 3y - 4 = 0 when x = 2"
        assert raw_content == expected
    
    def test_extract_raw_content_figure(self):
        """Test figure block handling"""
        block = MockMarkerBlock(**SAMPLE_FIGURE_BLOCK)
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should return placeholder for figure with no caption
        assert raw_content == "[Figure]"
    
    def test_create_ui_block(self):
        """Test conversion of Marker block to Block"""
        block = MockMarkerBlock(**SAMPLE_TEXT_BLOCK)
        
        ui_block = Formatter.create_ui_block(block)
        
        # Verify Block structure
        assert isinstance(ui_block, Block)
        assert ui_block.id == "/page/0/Text/1"
        assert ui_block.block_type == "Text"
        assert ui_block.html_content == SAMPLE_TEXT_BLOCK["html"]
        assert ui_block.raw_content == "Question: Which function is monotonic in range [0, pi]?"
        assert ui_block.bbox == SAMPLE_TEXT_BLOCK["bbox"]
        assert ui_block.polygon == SAMPLE_TEXT_BLOCK["polygon"]
    
    def test_latex_extraction_from_html(self):
        """Test LaTeX extraction helper function"""
        html_inline = '<p>Text with <math display="inline">x^2</math> here</p>'
        html_block = '<p><math display="block">\\frac{a}{b}</math></p>'
        
        result_inline = Formatter._extract_latex_from_html(html_inline)
        result_block = Formatter._extract_latex_from_html(html_block)
        
        assert result_inline == "x^2"
        assert result_block == "\\frac{a}{b}"
    
    def test_text_with_math_extraction(self):
        """Test text extraction that preserves inline math"""
        html = '<p block-type="Text">Solve <math display="inline">ax^2 + bx + c = 0</math> for x</p>'
        
        result = Formatter._extract_text_with_math(html)
        
        assert result == "Solve ax^2 + bx + c = 0 for x"
    
    def test_extract_image_dimensions(self):
        """Test image dimensions extraction"""
        class MockMarkerResult:
            def __init__(self):
                self.metadata = {}
                self.children = []  # Add children attribute
        
        mock_result = MockMarkerResult()
        dimensions = Formatter.extract_image_dimensions(mock_result)
        
        # Should return default dimensions
        assert dimensions == (800, 600)
        assert isinstance(dimensions, tuple)
        assert len(dimensions) == 2


class TestFormatterIntegration:
    
    def test_format_for_ui_interaction_structure(self):
        """Test the main formatting function structure"""
        # Mock a complete Marker result
        class MockMarkerResult:
            def __init__(self):
                self.metadata = {"test": "data"}
                self.children = [MockMarkerPage()]
        
        class MockMarkerPage:
            def __init__(self):
                self.children = [
                    MockMarkerBlock(**SAMPLE_TEXT_BLOCK),
                    MockMarkerBlock(**SAMPLE_EQUATION_BLOCK)
                ]
        
        mock_result = MockMarkerResult()
        
        ui_output = Formatter.format_for_ui_interaction(mock_result)
        
        # Verify FormattedOutput structure
        assert isinstance(ui_output, FormattedOutput)
        assert len(ui_output.blocks) == 2
        assert ui_output.image_dimensions == (800, 600)
        assert "total_blocks" in ui_output.processing_metadata
        assert ui_output.processing_metadata["total_blocks"] == 2
        
        # Verify individual blocks
        text_block = ui_output.blocks[0]
        equation_block = ui_output.blocks[1]
        
        assert text_block.block_type == "Text"
        assert equation_block.block_type == "Equation"
        # The equation block should extract LaTeX from HTML since no direct latex attribute
        assert equation_block.raw_content == "x^2 + y^2 = 1"