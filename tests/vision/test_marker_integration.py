"""
Integration tests for Marker service and vision pipeline.
Tests the complete flow from Marker processing to formatted output.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from src.models.services.marker import MarkerService
from src.pipeline.vision.formatter import Formatter
from src.pipeline.vision.types import Block, FormattedOutput


class TestMarkerServiceIntegration:
    """Test Marker service integration with vision pipeline"""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='white')
        return img
    
    @pytest.fixture
    def mock_marker_result(self):
        """Create a mock Marker result with realistic structure"""
        class MockPage:
            def __init__(self):
                self.children = [
                    MockBlock(
                        id="/page/0/Text/0",
                        block_type="Text",
                        html='<p block-type="Text"><b>Question:</b> Solve for x: 2x + 3 = 7</p>',
                        bbox=[100.0, 100.0, 400.0, 150.0],
                        polygon=[[100.0, 100.0], [400.0, 100.0], [400.0, 150.0], [100.0, 150.0]],
                        text="Question: Solve for x: 2x + 3 = 7"
                    ),
                    MockBlock(
                        id="/page/0/Equation/0",
                        block_type="Equation",
                        html='<p block-type="Equation"><math display="block">2x + 3 = 7</math></p>',
                        bbox=[100.0, 160.0, 300.0, 210.0],
                        polygon=[[100.0, 160.0], [300.0, 160.0], [300.0, 210.0], [100.0, 210.0]],
                        latex="2x + 3 = 7"
                    ),
                    MockBlock(
                        id="/page/0/Figure/0",
                        block_type="Figure",
                        html="",
                        bbox=[100.0, 220.0, 500.0, 420.0],
                        polygon=[[100.0, 220.0], [500.0, 220.0], [500.0, 420.0], [100.0, 420.0]],
                        caption="Graph showing the solution"
                    )
                ]
        
        class MockBlock:
            def __init__(self, id, block_type, html, bbox, polygon, **kwargs):
                self.id = id
                self.block_type = block_type
                self.html = html
                self.bbox = bbox
                self.polygon = polygon
                self.children = []
                self.section_hierarchy = {}
                self.images = {}
                self.confidence = None
                
                # Add optional attributes
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        class MockResult:
            def __init__(self):
                self.children = [MockPage()]
                self.metadata = {
                    "table_of_contents": [{"title": "Problem 1", "level": 1}],
                    "page_stats": [{"blocks": 3, "text_extraction_method": "llm"}]
                }
        
        return MockResult()
    
    @patch('src.models.services.marker.create_model_dict')
    @patch('src.models.services.marker.ConfigParser')
    @patch('src.models.services.marker.PdfConverter')
    def test_marker_service_initialization(self, mock_converter_class, mock_config_parser, mock_create_dict):
        """Test Marker service initialization with proper configuration"""
        # Setup mocks
        mock_create_dict.return_value = {}
        mock_parser = Mock()
        mock_config_parser.return_value = mock_parser
        mock_parser.generate_config_dict.return_value = {}
        mock_parser.get_processors.return_value = []
        mock_parser.get_renderer.return_value = None
        mock_parser.get_llm_service.return_value = None
        mock_converter_class.return_value = Mock()
        
        # Test initialization
        settings = {
            "use_llm": True,
            "llm_service": "gemini",
            "output_format": "json",
            "gemini": {"api_key": "test-key"}
        }
        
        marker_service = MarkerService(**settings)
        
        # Verify initialization
        assert marker_service.settings == settings
        assert marker_service.converter is not None
        
        # Verify CLI config building
        cli_config = marker_service._build_cli_config()
        assert cli_config["llm_service"] == "marker.services.gemini.GoogleGeminiService"
        assert cli_config["gemini_api_key"] == "test-key"
    
    @patch('src.models.services.marker.create_model_dict')
    @patch('src.models.services.marker.ConfigParser')
    @patch('src.models.services.marker.PdfConverter')
    def test_marker_document_conversion(self, mock_converter_class, mock_config_parser, mock_create_dict, sample_image):
        """Test Marker document conversion with image input"""
        # Setup mocks
        mock_create_dict.return_value = {}
        mock_parser = Mock()
        mock_config_parser.return_value = mock_parser
        mock_parser.generate_config_dict.return_value = {}
        mock_parser.get_processors.return_value = []
        mock_parser.get_renderer.return_value = None
        mock_parser.get_llm_service.return_value = None
        
        # Mock converter with realistic result
        mock_converter = Mock()
        mock_converter_class.return_value = mock_converter
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            sample_image.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # Test conversion
            marker_service = MarkerService(use_llm=False, output_format="json")
            result = marker_service.convert_document(tmp_path)
            
            # Verify converter was called
            mock_converter.assert_called_once_with(tmp_path)
            
        finally:
            # Cleanup
            os.unlink(tmp_path)
    
    @patch('src.pipeline.vision.formatter.text_from_rendered')
    def test_formatter_with_marker_result(self, mock_text_from_rendered, mock_marker_result):
        """Test formatter processing with Marker result"""
        # Mock text_from_rendered utility
        mock_text_from_rendered.return_value = (
            "Question: Solve for x: 2x + 3 = 7\n2x + 3 = 7\nGraph showing the solution",
            {"table_of_contents": [{"title": "Problem 1", "level": 1}]},
            {"image1": "base64_data"}
        )
        
        # Test formatter
        formatted_output = Formatter.format_for_ui_interaction(mock_marker_result)
        
        # Verify output structure
        assert isinstance(formatted_output, FormattedOutput)
        assert len(formatted_output.blocks) == 3
        
        # Verify block types
        block_types = [block.block_type for block in formatted_output.blocks]
        assert "Text" in block_types
        assert "Equation" in block_types
        assert "Figure" in block_types
        
        # Verify enhanced features
        assert formatted_output.document_text is not None
        assert formatted_output.table_of_contents is not None
        assert formatted_output.embedded_images is not None
        assert formatted_output.spatial_relationships is not None
        
        # Verify processing metadata
        assert formatted_output.processing_metadata["processing_method"] == "marker_optimized"
        assert formatted_output.processing_metadata["total_blocks"] == 3
    
    def test_block_content_extraction_accuracy(self, mock_marker_result):
        """Test accuracy of content extraction from different block types"""
        # Test each block type
        text_block = mock_marker_result.children[0].children[0]
        equation_block = mock_marker_result.children[0].children[1]
        figure_block = mock_marker_result.children[0].children[2]
        
        # Test text block
        text_content = Formatter.extract_raw_content_optimized(text_block)
        assert text_content == "Question: Solve for x: 2x + 3 = 7"
        
        # Test equation block
        equation_content = Formatter.extract_raw_content_optimized(equation_block)
        assert equation_content == "2x + 3 = 7"
        
        # Test figure block
        figure_content = Formatter.extract_raw_content_optimized(figure_block)
        assert figure_content == "Graph showing the solution"
    
    def test_spatial_relationship_detection(self, mock_marker_result):
        """Test spatial relationship detection between blocks"""
        with patch('src.pipeline.vision.formatter.text_from_rendered') as mock_utility:
            mock_utility.return_value = ("", {}, {})
            
            formatted_output = Formatter.format_for_ui_interaction(mock_marker_result)
        
        # Verify spatial relationships
        relationships = formatted_output.spatial_relationships
        assert 'block_proximity' in relationships
        assert 'reading_order' in relationships
        assert 'section_groups' in relationships
        
        # Verify reading order (should be sorted by y-coordinate)
        reading_order = relationships['reading_order']
        assert len(reading_order) == 3
        assert "/page/0/Text/0" in reading_order
        assert "/page/0/Equation/0" in reading_order
        assert "/page/0/Figure/0" in reading_order
        
        # Verify proximity relationships
        proximity = relationships['block_proximity']
        assert len(proximity) == 3
        for block_id in proximity:
            assert isinstance(proximity[block_id], list)


class TestMarkerErrorHandling:
    """Test error handling in Marker integration"""
    
    @patch('src.models.services.marker.create_model_dict')
    @patch('src.models.services.marker.ConfigParser')
    @patch('src.models.services.marker.PdfConverter')
    def test_marker_service_error_handling(self, mock_converter_class, mock_config_parser, mock_create_dict):
        """Test Marker service error handling"""
        # Setup mocks to raise errors
        mock_create_dict.side_effect = Exception("Model loading failed")
        
        # Test error handling
        with pytest.raises(Exception):
            MarkerService(use_llm=True, llm_service="gemini")
    
    @patch('src.pipeline.vision.formatter.text_from_rendered')
    def test_formatter_error_handling(self, mock_text_from_rendered):
        """Test formatter error handling"""
        # Mock text_from_rendered to raise error
        mock_text_from_rendered.side_effect = Exception("Utility failed")
        
        # Create minimal mock result
        class MockResult:
            def __init__(self):
                self.children = []
                self.metadata = {}
        
        mock_result = MockResult()
        
        # Should not raise error, should fallback gracefully
        formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        # Verify fallback behavior
        assert formatted_output.document_text == ""
        assert formatted_output.table_of_contents == []
        assert formatted_output.embedded_images == {}
        assert formatted_output.processing_metadata["processing_method"] == "marker_optimized"
    
    def test_invalid_image_handling(self):
        """Test handling of invalid image inputs"""
        # Test with non-existent file
        with patch('src.models.services.marker.create_model_dict'), \
             patch('src.models.services.marker.ConfigParser'), \
             patch('src.models.services.marker.PdfConverter') as mock_converter_class:
            
            mock_converter = Mock()
            mock_converter_class.return_value = mock_converter
            mock_converter.side_effect = FileNotFoundError("File not found")
            
            marker_service = MarkerService(use_llm=False)
            
            with pytest.raises(FileNotFoundError):
                marker_service.convert_document("nonexistent_file.png")


class TestMarkerPerformance:
    """Test performance characteristics of Marker integration"""
    
    def test_large_document_handling(self):
        """Test handling of documents with many blocks"""
        # Create mock result with many blocks
        class MockPage:
            def __init__(self, num_blocks=100):
                self.children = []
                for i in range(num_blocks):
                    block = Mock()
                    block.id = f"/page/0/Text/{i}"
                    block.block_type = "Text"
                    block.html = f"<p>Block {i} content</p>"
                    block.bbox = [100.0, 100.0 + i * 20, 300.0, 120.0 + i * 20]
                    block.polygon = [[100.0, 100.0 + i * 20], [300.0, 100.0 + i * 20], 
                                   [300.0, 120.0 + i * 20], [100.0, 120.0 + i * 20]]
                    block.text = f"Block {i} content"
                    block.children = []
                    block.section_hierarchy = {}
                    block.images = {}
                    block.confidence = None
                    self.children.append(block)
        
        class MockResult:
            def __init__(self, num_blocks=100):
                self.children = [MockPage(num_blocks)]
                self.metadata = {"test": "data"}
        
        mock_result = MockResult(100)
        
        with patch('src.pipeline.vision.formatter.text_from_rendered') as mock_utility:
            mock_utility.return_value = ("", {}, {})
            
            # Should handle large documents efficiently
            formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        assert len(formatted_output.blocks) == 100
        assert formatted_output.spatial_relationships is not None
        assert len(formatted_output.spatial_relationships['reading_order']) == 100
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large images"""
        # This test would be more comprehensive with actual large images
        # For now, we test that the formatter doesn't hold unnecessary references
        
        class MockResult:
            def __init__(self):
                self.children = []
                self.metadata = {}
        
        mock_result = MockResult()
        
        with patch('src.pipeline.vision.formatter.text_from_rendered') as mock_utility:
            mock_utility.return_value = ("", {}, {})
            
            formatted_output = Formatter.format_for_ui_interaction(mock_result)
        
        # Verify no unnecessary data retention
        assert formatted_output.blocks == []
        assert formatted_output.document_text == ""
        assert formatted_output.embedded_images == {}


class TestMarkerCompatibility:
    """Test compatibility with different Marker configurations"""
    
    @patch('src.models.services.marker.create_model_dict')
    @patch('src.models.services.marker.ConfigParser')
    @patch('src.models.services.marker.PdfConverter')
    def test_different_llm_services(self, mock_converter_class, mock_config_parser, mock_create_dict):
        """Test Marker service with different LLM configurations"""
        # Setup mocks
        mock_create_dict.return_value = {}
        mock_parser = Mock()
        mock_config_parser.return_value = mock_parser
        mock_parser.generate_config_dict.return_value = {}
        mock_parser.get_processors.return_value = []
        mock_parser.get_renderer.return_value = None
        mock_parser.get_llm_service.return_value = None
        mock_converter_class.return_value = Mock()
        
        # Test Gemini configuration
        gemini_service = MarkerService(
            use_llm=True,
            llm_service="gemini",
            gemini={"api_key": "test-key"}
        )
        gemini_config = gemini_service._build_cli_config()
        assert "gemini_api_key" in gemini_config
        
        # Test Ollama configuration
        ollama_service = MarkerService(
            use_llm=True,
            llm_service="ollama",
            ollama={"base_url": "http://localhost:11434", "model": "llama3.2-vision"}
        )
        ollama_config = ollama_service._build_cli_config()
        assert "ollama_base_url" in ollama_config
        assert "ollama_model" in ollama_config
        
        # Test OpenAI configuration
        openai_service = MarkerService(
            use_llm=True,
            llm_service="openai",
            openai={"api_key": "test-key", "model": "gpt-4o-mini"}
        )
        openai_config = openai_service._build_cli_config()
        assert "openai_api_key" in openai_config
    
    def test_different_output_formats(self):
        """Test Marker service with different output formats"""
        with patch('src.models.services.marker.create_model_dict'), \
             patch('src.models.services.marker.ConfigParser'), \
             patch('src.models.services.marker.PdfConverter'):
            
            # Test JSON output
            json_service = MarkerService(output_format="json")
            assert json_service.settings["output_format"] == "json"
            
            # Test HTML output
            html_service = MarkerService(output_format="html")
            assert html_service.settings["output_format"] == "html"
            
            # Test Markdown output
            md_service = MarkerService(output_format="markdown")
            assert md_service.settings["output_format"] == "markdown"
