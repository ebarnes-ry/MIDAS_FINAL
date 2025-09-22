import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.pipeline.vision.vision import VisionPipeline
from src.pipeline.vision.types import VisionInput, UserSelection, FormattedOutput, VisionFinalOutput, Block
from src.models.manager import ModelManager


class TestVisionPipelineInitialization:
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key", "GOOGLE_API_KEY": "fake-key"})
    def test_vision_pipeline_initialization(self):
        """Test that VisionPipeline initializes properly with ModelManager"""
        config_path = Path("src/config/config.yaml")
        if not config_path.exists():
            pytest.skip("Config file not found")
        
        model_manager = ModelManager(config_path)
        vision_pipeline = VisionPipeline(model_manager)
        
        # Verify pipeline initialized correctly
        assert vision_pipeline.model_manager is model_manager
        assert vision_pipeline.marker_service is not None
        assert hasattr(vision_pipeline.marker_service, 'convert_document')
        
        # Verify VLM contextualizer initialized
        assert vision_pipeline.visual_contextualizer is not None
        assert hasattr(vision_pipeline.visual_contextualizer, 'analyze')


class TestVisionPipelineIntegration:
    
    @pytest.fixture
    def sample_image_path(self):
        """Use the same image we tested with Marker"""
        return "./benchmarks/data/samples/input_cases/one_problem/multi_choice_diagram.png"
    
    @pytest.fixture
    def vision_pipeline(self):
        """Create vision pipeline with mocked environment"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key", "GOOGLE_API_KEY": "fake-key"}):
            config_path = Path("src/config/config.yaml")
            if not config_path.exists():
                pytest.skip("Config file not found")
            
            model_manager = ModelManager(config_path)
            return VisionPipeline(model_manager)
    
    def test_process_input_basic_flow(self, vision_pipeline, sample_image_path):
        """Test the basic document processing flow"""
        vision_input = VisionInput(
            file_path=sample_image_path,
            file_type="image"
        )
        
        # This should run Marker and format the output
        ui_output = vision_pipeline.process_input(vision_input)
        
        # Verify the output structure
        assert isinstance(ui_output, FormattedOutput)
        assert isinstance(ui_output.blocks, list)
        assert len(ui_output.blocks) > 0  # Should have extracted some blocks
        
        # Verify each block has the required structure
        for block in ui_output.blocks:
            assert hasattr(block, 'id')
            assert hasattr(block, 'block_type')
            assert hasattr(block, 'html_content')
            assert hasattr(block, 'raw_content')
            assert hasattr(block, 'bbox')
            assert hasattr(block, 'polygon')
        
        # Verify processing metadata
        assert "total_blocks" in ui_output.processing_metadata
        assert ui_output.processing_metadata["total_blocks"] == len(ui_output.blocks)
    
    def test_process_selection_basic_flow(self, vision_pipeline, sample_image_path):
        """Test user selection processing"""
        # First get the UI output
        vision_input = VisionInput(file_path=sample_image_path, file_type="image")
        ui_output = vision_pipeline.process_input(vision_input)
        
        # Simulate user selection and editing
        if ui_output.blocks:
            user_selection = UserSelection(
                selected_block_ids=[ui_output.blocks[0].id],
                edited_latex="Which function is monotonic in range [0, π]?",
                original_image_path=sample_image_path
            )
            
            # Process the user selection
            final_output = vision_pipeline.process_selection(user_selection, ui_output)
            
            # Verify the final output
            assert isinstance(final_output, VisionFinalOutput)
            assert final_output.problem_statement == user_selection.edited_latex
            assert "selected_blocks" in final_output.source_metadata
            assert final_output.source_metadata["selected_blocks"] == user_selection.selected_block_ids
    
    def test_marker_integration_with_real_image(self, vision_pipeline, sample_image_path):
        """Test that Marker actually processes the image and returns expected content"""
        vision_input = VisionInput(file_path=sample_image_path, file_type="image")
        ui_output = vision_pipeline.process_input(vision_input)
        
        # Based on our previous Marker test, we expect specific content
        block_types = [block.block_type for block in ui_output.blocks]
        raw_contents = [block.raw_content for block in ui_output.blocks]
        
        # Should have extracted the question text
        question_found = any("monotonic" in content.lower() for content in raw_contents)
        assert question_found, f"Expected to find question text in: {raw_contents}"
        
        # Should have different block types
        assert len(set(block_types)) > 1, f"Expected multiple block types, got: {block_types}"
    
    def test_end_to_end_flow(self, vision_pipeline, sample_image_path):
        """Test complete end-to-end flow"""
        # Step 1: Process input document
        vision_input = VisionInput(file_path=sample_image_path, file_type="image")
        ui_output = vision_pipeline.process_input(vision_input)
        
        assert len(ui_output.blocks) > 0
        
        # Step 2: User selects and edits content
        text_blocks = [b for b in ui_output.blocks if b.block_type == "Text"]
        if text_blocks:
            selected_block = text_blocks[0]
            
            user_selection = UserSelection(
                selected_block_ids=[selected_block.id],
                edited_latex=f"Modified: {selected_block.raw_content}",
                original_image_path=sample_image_path
            )
            
            # Step 3: Process selection
            final_output = vision_pipeline.process_selection(user_selection, ui_output)
            
            # Verify complete flow
            assert final_output.problem_statement.startswith("Modified:")
            assert final_output.source_metadata["processing_method"] == "marker"
            assert final_output.source_metadata["total_available_blocks"] == len(ui_output.blocks)


@pytest.mark.integration
class TestVisionPipelineRealProcessing:
    """Integration tests that require actual processing"""
    
    @pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="GOOGLE_API_KEY not set")
    def test_with_real_marker_processing(self):
        """Test with real Marker processing enabled"""
        config_path = Path("src/config/config.yaml")
        if not config_path.exists():
            pytest.skip("Config file not found")
        
        model_manager = ModelManager(config_path)
        vision_pipeline = VisionPipeline(model_manager)
        
        sample_image = "./benchmarks/data/samples/input_cases/one_problem/multi_choice_diagram.png"
        vision_input = VisionInput(file_path=sample_image, file_type="image")
        
        # This should work with real Marker + LLM
        ui_output = vision_pipeline.process_input(vision_input)
        
        # Verify we got meaningful results
        assert len(ui_output.blocks) > 0
        
        # Print results for manual verification
        print(f"Processed {len(ui_output.blocks)} blocks:")
        for i, block in enumerate(ui_output.blocks[:3]):  # Show first 3
            print(f"Block {i}: {block.block_type} - {block.raw_content[:100]}")
        
        assert any("question" in block.raw_content.lower() for block in ui_output.blocks)


class TestVisionPipelineVLMIntegration:
    """Test VLM integration in the vision pipeline"""
    
    @pytest.fixture
    def vision_pipeline(self):
        """Create vision pipeline with mocked environment"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key", "GOOGLE_API_KEY": "fake-key"}):
            config_path = Path("src/config/config.yaml")
            if not config_path.exists():
                pytest.skip("Config file not found")
            
            model_manager = ModelManager(config_path)
            return VisionPipeline(model_manager)
    
    def test_process_selection_without_visual_blocks(self, vision_pipeline):
        """Test that VLM is not called when no visual blocks are present"""
        # Setup input with no visual blocks
        user_selection = UserSelection(
            selected_block_ids=["text_1"],
            edited_latex="What is 2 + 2?",
            original_image_path="./benchmarks/data/samples/input_cases/one_problem/multi_choice_diagram.png"
        )

        ui_output = FormattedOutput(
            blocks=[
                # Only text blocks, no Figure/Picture blocks
                Block(
                    id="text_1",
                    block_type="Text",
                    html_content="<p>Question text</p>",
                    raw_content="What is 2 + 2?",
                    bbox=[0, 0, 100, 20],
                    polygon=[[0,0],[100,0],[100,20],[0,20]],
                    confidence=0.9
                )
            ],
            image_dimensions=(800, 600),
            processing_metadata={"total_blocks": 1}
        )

        # Create a mock source image
        from PIL import Image
        mock_image = Image.new('RGB', (800, 600), color='white')
        result = vision_pipeline.process_selection(user_selection, ui_output, mock_image)
        
        # Verify VLM was not called (visual_context should be None)
        assert result.visual_context is None
        assert result.source_metadata["vlm_analysis_performed"] is False
        assert result.problem_statement == "What is 2 + 2?"
    
    @patch('src.pipeline.vision.vlm.VisualContextualizer.analyze')
    def test_process_selection_with_visual_blocks_mock(self, mock_analyze, vision_pipeline):
        """Test that VLM is called when visual blocks are present"""
        from src.pipeline.vision.types import VisualContext
        
        # Mock VLM response
        mock_visual_context = VisualContext(
            elements=[],
            contains_essential_info=True,
            summary="Graph showing two functions with different monotonicity"
        )
        mock_analyze.return_value = mock_visual_context
        
        # Setup input with visual blocks
        user_selection = UserSelection(
            selected_block_ids=["figure_1"],
            edited_latex="Which function is monotonic in range [0, π]?",
            original_image_path="./benchmarks/data/samples/input_cases/one_problem/multi_choice_diagram.png"
        )
        
        ui_output = FormattedOutput(
            blocks=[
                Block(
                    id="figure_1",
                    block_type="Figure",  # This should trigger VLM
                    html_content="",
                    raw_content="[Figure]",
                    bbox=[0, 0, 400, 300],
                    polygon=[[0,0],[400,0],[400,300],[0,300]],
                    confidence=0.8
                )
            ],
            image_dimensions=(800, 600),
            processing_metadata={"total_blocks": 1}
        )
        
        result = vision_pipeline.process_selection(user_selection, ui_output)
        
        # Verify VLM was called
        mock_analyze.assert_called_once_with(user_selection, ui_output)
        
        # Verify result contains visual context
        assert result.visual_context is not None
        assert result.visual_context.relevance_score == 0.85
        assert "monotonicity" in result.visual_context.description
        assert result.source_metadata["vlm_analysis_performed"] is True
    
    def test_vlm_contextualizer_visual_detection(self, vision_pipeline):
        """Test VLM visual block detection logic"""
        # Test with Figure block
        ui_output_with_figure = FormattedOutput(
            blocks=[
                Block(
                    id="figure_1",
                    block_type="Figure",
                    html_content="",
                    raw_content="[Figure]",
                    bbox=[0, 0, 400, 300],
                    polygon=[[0,0],[400,0],[400,300],[0,300]],
                    confidence=0.8
                )
            ],
            image_dimensions=(800, 600),
            processing_metadata={"total_blocks": 1}
        )
        
        should_analyze = vision_pipeline.visual_contextualizer.should_analyze_visually(ui_output_with_figure)
        assert should_analyze is True
        
        # Test with only text blocks
        ui_output_text_only = FormattedOutput(
            blocks=[
                Block(
                    id="text_1",
                    block_type="Text",
                    html_content="<p>Question</p>",
                    raw_content="Question text",
                    bbox=[0, 0, 100, 20],
                    polygon=[[0,0],[100,0],[100,20],[0,20]],
                    confidence=0.9
                )
            ],
            image_dimensions=(800, 600),
            processing_metadata={"total_blocks": 1}
        )
        
        should_analyze = vision_pipeline.visual_contextualizer.should_analyze_visually(ui_output_text_only)
        assert should_analyze is False
    
    def test_end_to_end_with_vlm_disabled(self, vision_pipeline):
        """Test complete end-to-end flow when VLM is not needed"""
        # Process input (no VLM here)
        vision_input = VisionInput(
            file_path="./benchmarks/data/samples/input_cases/one_problem/multi_choice_diagram.png",
            file_type="image"
        )
        ui_output = vision_pipeline.process_input(vision_input)
        
        # Simulate user selection of text-only content
        text_blocks = [b for b in ui_output.blocks if b.block_type == "Text"]
        if text_blocks:
            user_selection = UserSelection(
                selected_block_ids=[text_blocks[0].id],
                edited_latex="Modified problem statement",
                original_image_path="./benchmarks/data/samples/input_cases/one_problem/multi_choice_diagram.png"
            )
            
            # Create UI output with only text blocks to disable VLM
            text_only_output = FormattedOutput(
                blocks=text_blocks,
                image_dimensions=ui_output.image_dimensions,
                processing_metadata={"total_blocks": len(text_blocks)}
            )
            
            final_output = vision_pipeline.process_selection(user_selection, text_only_output)
            
            # Verify VLM was not used
            assert final_output.visual_context is None
            assert final_output.source_metadata["vlm_analysis_performed"] is False
            assert final_output.problem_statement == "Modified problem statement"