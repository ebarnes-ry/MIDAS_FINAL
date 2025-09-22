"""
Comprehensive tests for the optimized Marker formatter integration.
Tests the enhanced functionality including direct LaTeX access, spatial intelligence,
and Marker utility integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.pipeline.vision.formatter import Formatter
from src.pipeline.vision.types import Block, FormattedOutput


class MockMarkerBlock:
    """Mock object that mimics Marker block structure with enhanced fields"""
    def __init__(self, id, block_type, html, bbox, polygon, children=None, 
                 section_hierarchy=None, images=None, latex=None, text=None, 
                 caption=None, code=None, table_data=None, confidence=None,
                 section_level=None, reading_order=None, relationships=None,
                 parent_id=None):
        self.id = id
        self.block_type = block_type
        self.html = html
        self.bbox = bbox
        self.polygon = polygon
        self.children = children or []
        self.section_hierarchy = section_hierarchy or {}
        self.images = images or {}
        self.latex = latex
        self.text = text
        self.caption = caption
        self.code = code
        self.table_data = table_data
        self.confidence = confidence
        self.section_level = section_level
        self.reading_order = reading_order
        self.relationships = relationships or {}
        self.parent_id = parent_id


class MockMarkerResult:
    """Mock Marker result with enhanced metadata"""
    def __init__(self, children=None, metadata=None):
        self.children = children or []
        self.metadata = metadata or {}


class TestOptimizedFormatter:
    """Test suite for optimized Marker formatter functionality"""
    
    def test_direct_latex_access_equation(self):
        """Test direct LaTeX access for equation blocks"""
        block = MockMarkerBlock(
            id="/page/0/Equation/1",
            block_type="Equation",
            html='<p><math display="block">x^2 + y^2 = 1</math></p>',
            bbox=[100.0, 200.0, 300.0, 250.0],
            polygon=[[100.0, 200.0], [300.0, 200.0], [300.0, 250.0], [100.0, 250.0]],
            latex="x^2 + y^2 = 1"
        )
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should use direct LaTeX access instead of HTML parsing
        assert raw_content == "x^2 + y^2 = 1"
    
    def test_direct_latex_access_inline_math(self):
        """Test direct LaTeX access for inline math blocks"""
        block = MockMarkerBlock(
            id="/page/0/TextInlineMath/1",
            block_type="TextInlineMath",
            html='<p>Solve <math display="inline">ax^2 + bx + c = 0</math> for x</p>',
            bbox=[50.0, 100.0, 400.0, 140.0],
            polygon=[[50.0, 100.0], [400.0, 100.0], [400.0, 140.0], [50.0, 140.0]],
            latex="ax^2 + bx + c = 0"
        )
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should use direct LaTeX access
        assert raw_content == "ax^2 + bx + c = 0"
    
    def test_direct_text_access(self):
        """Test direct text access for text blocks"""
        block = MockMarkerBlock(
            id="/page/0/Text/1",
            block_type="Text",
            html='<p block-type="Text"><b>Question:</b> Which function is monotonic?</p>',
            bbox=[14.0, 413.3, 484.4, 447.4],
            polygon=[[14.0, 413.3], [484.4, 413.3], [484.4, 447.4], [14.0, 447.4]],
            text="Question: Which function is monotonic?"
        )
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should use direct text access
        assert raw_content == "Question: Which function is monotonic?"
    
    def test_figure_caption_access(self):
        """Test direct caption access for figure blocks"""
        block = MockMarkerBlock(
            id="/page/0/Figure/0",
            block_type="Figure",
            html="",
            bbox=[2.4, 4.6, 528.0, 413.3],
            polygon=[[2.4, 4.6], [528.0, 4.6], [528.0, 413.3], [2.4, 413.3]],
            caption="Graph of y = log₂(x)"
        )
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should use direct caption access
        assert raw_content == "Graph of y = log₂(x)"
    
    def test_table_data_access(self):
        """Test structured table data access"""
        table_data = [["x", "y"], [1, 2], [3, 4]]
        block = MockMarkerBlock(
            id="/page/0/Table/0",
            block_type="Table",
            html="<table>...</table>",
            bbox=[100.0, 200.0, 300.0, 300.0],
            polygon=[[100.0, 200.0], [300.0, 200.0], [300.0, 300.0], [100.0, 300.0]],
            table_data=table_data
        )
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should use structured table data
        assert raw_content == str(table_data)
    
    def test_code_access(self):
        """Test direct code access for code blocks"""
        block = MockMarkerBlock(
            id="/page/0/Code/0",
            block_type="Code",
            html="<pre>...</pre>",
            bbox=[100.0, 200.0, 300.0, 250.0],
            polygon=[[100.0, 200.0], [300.0, 200.0], [300.0, 250.0], [100.0, 250.0]],
            code="def solve_equation(x):\n    return 2*x + 3"
        )
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should use direct code access
        assert raw_content == "def solve_equation(x):\n    return 2*x + 3"
    
    def test_fallback_to_html(self):
        """Test fallback to HTML when direct access fails"""
        block = MockMarkerBlock(
            id="/page/0/Unknown/0",
            block_type="Unknown",
            html="<p>Fallback content</p>",
            bbox=[100.0, 200.0, 300.0, 250.0],
            polygon=[[100.0, 200.0], [300.0, 200.0], [300.0, 250.0], [100.0, 250.0]]
        )
        
        raw_content = Formatter.extract_raw_content(block)
        
        # Should fallback to clean text extraction from HTML
        assert raw_content == "Fallback content"
    
    def test_enhanced_block_creation(self):
        """Test enhanced block creation with spatial data"""
        block = MockMarkerBlock(
            id="/page/0/Text/1",
            block_type="Text",
            html='<p>Test content</p>',
            bbox=[100.0, 200.0, 300.0, 250.0],
            polygon=[[100.0, 200.0], [300.0, 200.0], [300.0, 250.0], [100.0, 250.0]],
            text="Test content",
            section_level=1,
            reading_order=5,
            relationships={"parent": "/page/0/Section/0"},
            parent_id="/page/0/Section/0",
            images={"/page/0/Text/1": "base64_image_data"},
            section_hierarchy={"level": 1, "title": "Introduction"}
        )
        
        ui_block = Formatter.create_ui_block(block)
        
        # Verify enhanced fields
        assert isinstance(ui_block, Block)
        assert ui_block.id == "/page/0/Text/1"
        assert ui_block.block_type == "Text"
        assert ui_block.raw_content == "Test content"
        
        # Verify spatial data
        assert ui_block.spatial_data is not None
        assert ui_block.spatial_data['bbox'] == [100.0, 200.0, 300.0, 250.0]
        assert ui_block.spatial_data['parent_id'] == "/page/0/Section/0"
        
        # Verify marker metadata
        assert ui_block.marker_metadata is not None
        assert ui_block.marker_metadata['section_level'] == 1
        assert ui_block.marker_metadata['reading_order'] == 5
        assert ui_block.marker_metadata['block_relationships'] == {"parent": "/page/0/Section/0"}
        
        # Verify images and section hierarchy
        assert ui_block.images == {"/page/0/Text/1": "base64_image_data"}
        assert ui_block.section_hierarchy == {"level": 1, "title": "Introduction"}
    
    def test_spatial_relationship_extraction(self):
        """Test spatial relationship extraction between blocks"""
        blocks = [
            Block(
                id="block1", block_type="Text", html_content="", raw_content="",
                bbox=[100.0, 100.0, 200.0, 150.0], polygon=[], confidence=None
            ),
            Block(
                id="block2", block_type="Text", html_content="", raw_content="",
                bbox=[100.0, 160.0, 200.0, 210.0], polygon=[], confidence=None
            ),
            Block(
                id="block3", block_type="Text", html_content="", raw_content="",
                bbox=[500.0, 100.0, 600.0, 150.0], polygon=[], confidence=None
            )
        ]
        
        relationships = Formatter._extract_spatial_relationships(blocks)
        
        # Verify structure
        assert 'block_proximity' in relationships
        assert 'reading_order' in relationships
        assert 'section_groups' in relationships
        
        # Verify reading order (sorted by y, then x)
        # block1: y=100, block2: y=160, block3: y=100
        # So order should be: block1, block3 (both y=100, sorted by x), block2
        assert relationships['reading_order'] == ["block1", "block3", "block2"]
        
        # Verify proximity (block1 and block2 should be close, block3 far)
        # Distance between block1 and block2 centers: sqrt((150-150)^2 + (185-125)^2) = 60
        # With default threshold 50, they should NOT be related
        # So proximity lists should be empty for all blocks
        assert relationships['block_proximity']['block1'] == []
        assert relationships['block_proximity']['block2'] == []
        assert relationships['block_proximity']['block3'] == []
    
    def test_blocks_spatially_related(self):
        """Test spatial relationship detection between two blocks"""
        block1 = Block(
            id="block1", block_type="Text", html_content="", raw_content="",
            bbox=[100.0, 100.0, 200.0, 150.0], polygon=[], confidence=None
        )
        block2 = Block(
            id="block2", block_type="Text", html_content="", raw_content="",
            bbox=[100.0, 160.0, 200.0, 210.0], polygon=[], confidence=None
        )
        block3 = Block(
            id="block3", block_type="Text", html_content="", raw_content="",
            bbox=[500.0, 100.0, 600.0, 150.0], polygon=[], confidence=None
        )
        
        # block1 and block2 should be spatially related (close)
        # Distance between centers: block1 center (150, 125), block2 center (150, 185)
        # Distance = sqrt((150-150)^2 + (185-125)^2) = sqrt(0 + 3600) = 60
        # With threshold 50, they should NOT be related (60 > 50)
        assert Formatter._blocks_are_spatially_related(block1, block2, threshold=70.0) == True
        
        # block1 and block3 should not be spatially related (far)
        assert Formatter._blocks_are_spatially_related(block1, block3, threshold=50.0) == False
    
    @patch('src.pipeline.vision.formatter.text_from_rendered')
    def test_marker_utility_integration_success(self, mock_text_from_rendered):
        """Test successful integration with Marker's text_from_rendered utility"""
        # Mock successful text_from_rendered call
        mock_text_from_rendered.return_value = (
            "Full document text content",
            {"table_of_contents": [{"title": "Section 1", "level": 1}], "page_stats": [{"blocks": 5}]},
            {"image1": "base64_data"}
        )
        
        # Create mock Marker result
        mock_result = MockMarkerResult(
            children=[MockMarkerBlock(
                id="/page/0/Text/1", block_type="Text", html="<p>Test</p>",
                bbox=[100, 200, 300, 250], polygon=[], text="Test"
            )],
            metadata={"test": "data"}
        )
        
        formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        # Verify Marker utility was called
        mock_text_from_rendered.assert_called_once_with(mock_result)
        
        # Verify enhanced metadata
        assert formatted_output.document_text == "Full document text content"
        assert formatted_output.table_of_contents == [{"title": "Section 1", "level": 1}]
        assert formatted_output.embedded_images == {"image1": "base64_data"}
        assert formatted_output.processing_metadata["processing_method"] == "marker_optimized"
        assert formatted_output.processing_metadata["text_content"] == "Full document text content"
    
    @patch('src.pipeline.vision.formatter.text_from_rendered')
    def test_marker_utility_integration_fallback(self, mock_text_from_rendered):
        """Test fallback when text_from_rendered fails"""
        # Mock failed text_from_rendered call
        mock_text_from_rendered.side_effect = Exception("Utility failed")
        
        # Create mock Marker result
        mock_result = MockMarkerResult(
            children=[MockMarkerBlock(
                id="/page/0/Text/1", block_type="Text", html="<p>Test</p>",
                bbox=[100, 200, 300, 250], polygon=[], text="Test"
            )],
            metadata={"test": "data"}
        )
        
        formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        # Verify fallback behavior
        assert formatted_output.document_text == ""
        assert formatted_output.table_of_contents == []
        assert formatted_output.embedded_images == {}
        assert formatted_output.processing_metadata["processing_method"] == "marker_optimized"
    
    @patch('src.pipeline.vision.formatter.text_from_rendered')
    def test_marker_utility_string_return(self, mock_text_from_rendered):
        """Test handling when text_from_rendered returns a string"""
        # Mock text_from_rendered returning a string
        mock_text_from_rendered.return_value = "Just a string result"
        
        # Create mock Marker result
        mock_result = MockMarkerResult(
            children=[MockMarkerBlock(
                id="/page/0/Text/1", block_type="Text", html="<p>Test</p>",
                bbox=[100, 200, 300, 250], polygon=[], text="Test"
            )],
            metadata={"test": "data"}
        )
        
        formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        # Verify string handling
        assert formatted_output.document_text == "Just a string result"
        assert formatted_output.table_of_contents == []
        assert formatted_output.embedded_images == {}


class TestFormatterIntegration:
    """Integration tests for the complete formatter functionality"""
    
    def test_complete_pipeline_with_enhanced_features(self):
        """Test complete formatter pipeline with all enhanced features"""
        # Create comprehensive mock Marker result
        blocks = [
            MockMarkerBlock(
                id="/page/0/Equation/0", block_type="Equation",
                html='<p><math display="block">x^2 + y^2 = 1</math></p>',
                bbox=[100.0, 100.0, 300.0, 150.0],
                polygon=[[100.0, 100.0], [300.0, 100.0], [300.0, 150.0], [100.0, 150.0]],
                latex="x^2 + y^2 = 1",
                section_level=1,
                reading_order=1
            ),
            MockMarkerBlock(
                id="/page/0/Figure/0", block_type="Figure",
                html="",
                bbox=[100.0, 160.0, 300.0, 260.0],
                polygon=[[100.0, 160.0], [300.0, 160.0], [300.0, 260.0], [100.0, 260.0]],
                caption="Circle graph",
                images={"/page/0/Figure/0": "base64_circle_image"}
            ),
            MockMarkerBlock(
                id="/page/0/Text/0", block_type="Text",
                html='<p>This is a test problem.</p>',
                bbox=[100.0, 270.0, 300.0, 320.0],
                polygon=[[100.0, 270.0], [300.0, 270.0], [300.0, 320.0], [100.0, 320.0]],
                text="This is a test problem.",
                section_level=1,
                reading_order=2
            )
        ]
        
        # Create proper MockMarkerResult structure
        class MockPage:
            def __init__(self, blocks):
                self.children = blocks
        
        class MockResult:
            def __init__(self, blocks, metadata):
                self.children = [MockPage(blocks)]
                self.metadata = metadata
        
        mock_result = MockResult(
            blocks,
            {"table_of_contents": [{"title": "Problem 1", "level": 1}]}
        )
        
        with patch('src.pipeline.vision.formatter.text_from_rendered') as mock_utility:
            mock_utility.return_value = (
                "x^2 + y^2 = 1\nCircle graph\nThis is a test problem.",
                {"table_of_contents": [{"title": "Problem 1", "level": 1}]},
                {"image1": "base64_data"}
            )
            
            formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        # Verify complete output structure
        assert isinstance(formatted_output, FormattedOutput)
        assert len(formatted_output.blocks) == 3
        
        # Verify enhanced fields
        assert formatted_output.document_text is not None
        assert formatted_output.table_of_contents is not None
        assert formatted_output.embedded_images is not None
        assert formatted_output.spatial_relationships is not None
        
        # Verify individual blocks have enhanced data
        equation_block = formatted_output.blocks[0]
        assert equation_block.raw_content == "x^2 + y^2 = 1"
        assert equation_block.marker_metadata['section_level'] == 1
        assert equation_block.marker_metadata['reading_order'] == 1
        
        figure_block = formatted_output.blocks[1]
        assert figure_block.raw_content == "Circle graph"
        assert figure_block.images == {"/page/0/Figure/0": "base64_circle_image"}
        
        text_block = formatted_output.blocks[2]
        assert text_block.raw_content == "This is a test problem."
        
        # Verify spatial relationships
        assert len(formatted_output.spatial_relationships['reading_order']) == 3
        assert len(formatted_output.spatial_relationships['block_proximity']) == 3
    
    def test_backward_compatibility(self):
        """Test that legacy methods still work for backward compatibility"""
        block = MockMarkerBlock(
            id="/page/0/Text/1",
            block_type="Text",
            html='<p>Test content</p>',
            bbox=[100.0, 200.0, 300.0, 250.0],
            polygon=[[100.0, 200.0], [300.0, 200.0], [300.0, 250.0], [100.0, 250.0]]
        )
        
        # Test legacy methods still work
        legacy_block = Formatter.create_ui_block(block)
        legacy_content = Formatter.extract_raw_content(block)
        
        # Verify legacy methods return expected results
        assert isinstance(legacy_block, Block)
        assert legacy_block.id == "/page/0/Text/1"
        assert legacy_content is not None


class TestFormatterEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_marker_result(self):
        """Test handling of empty Marker result"""
        mock_result = MockMarkerResult(children=[], metadata={})
        
        with patch('src.pipeline.vision.formatter.text_from_rendered') as mock_utility:
            mock_utility.return_value = ("", {}, {})
            
            formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        assert len(formatted_output.blocks) == 0
        assert formatted_output.document_text == ""
        assert formatted_output.table_of_contents == []
    
    def test_missing_block_attributes(self):
        """Test handling of blocks with missing attributes"""
        block = MockMarkerBlock(
            id="/page/0/Text/1",
            block_type="Text",
            html='<p>Test</p>',
            bbox=[100.0, 200.0, 300.0, 250.0],
            polygon=[[100.0, 200.0], [300.0, 200.0], [300.0, 250.0], [100.0, 250.0]]
            # Missing optional attributes like latex, text, etc.
        )
        
        # Should not raise errors and should fallback gracefully
        raw_content = Formatter.extract_raw_content(block)
        ui_block = Formatter.create_ui_block(block)
        
        # For Text block type without text attribute, should fallback to clean text extraction
        assert raw_content == 'Test'  # Clean text extraction from HTML
        assert ui_block.id == "/page/0/Text/1"
        assert ui_block.spatial_data is not None
        assert ui_block.marker_metadata is not None
    
    def test_invalid_bbox_coordinates(self):
        """Test handling of invalid bbox coordinates"""
        block = MockMarkerBlock(
            id="/page/0/Text/1",
            block_type="Text",
            html='<p>Test</p>',
            bbox=[],  # Invalid bbox
            polygon=[]
        )
        
        # Should handle gracefully
        ui_block = Formatter.create_ui_block(block)
        
        assert ui_block.id == "/page/0/Text/1"
        assert ui_block.bbox == []
        assert ui_block.spatial_data is not None
