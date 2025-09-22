"""
Core VLM functionality tests - focused on schema, prompt loading, and basic functionality
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.pipeline.vision.vlm import VisualContextualizer, VisualContextOutput, VisualElement
from src.pipeline.vision.types import UserSelection, UIFormattedOutput, UIBlock
from src.models.manager import ModelManager
from src.prompts.resolver import build_payload


class TestVLMSchemas:
    """Test VLM Pydantic schemas and validation"""
    
    def test_visual_element_schema(self):
        """Test VisualElement schema validation"""
        element = VisualElement(
            type="function_graph",
            description="Blue decreasing curve",
            mathematical_properties={"monotonicity": "decreasing"}
        )
        
        assert element.type == "function_graph"
        assert element.description == "Blue decreasing curve"
        assert element.mathematical_properties["monotonicity"] == "decreasing"
    
    def test_visual_context_output_schema(self):
        """Test VisualContextOutput schema validation"""
        elements = [
            VisualElement(type="coordinate_system", description="2D plane"),
            VisualElement(type="function_graph", description="Blue curve")
        ]
        
        output = VisualContextOutput(
            natural_description="Two function graphs on coordinate plane",
            visual_elements=elements,
            mathematical_relevance="Functions show different monotonicity",
            confidence=0.85
        )
        
        assert output.confidence == 0.85
        assert len(output.visual_elements) == 2
        assert "monotonicity" in output.mathematical_relevance
    
    def test_visual_context_output_json_serialization(self):
        """Test that schema can serialize/deserialize JSON properly"""
        output = VisualContextOutput(
            natural_description="Test description",
            visual_elements=[],
            mathematical_relevance="Test relevance",
            confidence=0.9
        )
        
        json_str = output.model_dump_json()
        parsed = VisualContextOutput.model_validate_json(json_str)
        
        assert parsed.natural_description == "Test description"
        assert parsed.confidence == 0.9


class TestVLMPromptIntegration:
    """Test VLM prompt loading and payload building"""
    
    def test_prompt_card_loading(self):
        """Test that VLM prompt can be loaded from filesystem"""
        task_cfg = {"prompt": "vision/visual_context@v1"}
        vars_dict = {
            "problem_statement": "Test problem",
            "selected_blocks_info": "Test blocks",
            "spatial_context": "Test spatial context"
        }
        
        payload = build_payload(task_cfg, vars_dict)
        
        # Verify payload structure
        assert "messages" in payload
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        
        # Verify variables were substituted
        user_content = payload["messages"][1]["content"]
        assert "Test problem" in user_content
        assert "Test blocks" in user_content
        
        # Verify schema hint was added
        system_content = payload["messages"][0]["content"]
        assert "JSON" in system_content  # Schema hint should mention JSON


class TestVisualContextualizer:
    """Test VisualContextualizer class functionality"""
    
    @pytest.fixture
    def mock_model_manager(self):
        """Create a mock ModelManager"""
        return MagicMock(spec=ModelManager)
    
    @pytest.fixture
    def visual_contextualizer(self, mock_model_manager):
        """Create VisualContextualizer with mock dependencies"""
        return VisualContextualizer(mock_model_manager)
    
    def test_visual_block_detection_positive(self, visual_contextualizer):
        """Test that visual blocks are correctly detected"""
        ui_output = UIFormattedOutput(
            blocks=[
                UIBlock(
                    id="text_1", 
                    block_type="Text", 
                    html_content="<p>Question</p>",
                    raw_content="Question text",
                    bbox=[0, 0, 100, 20],
                    polygon=[[0,0],[100,0],[100,20],[0,20]],
                    confidence=0.9
                ),
                UIBlock(
                    id="figure_1",
                    block_type="Figure", 
                    html_content="",
                    raw_content="[Figure]",
                    bbox=[0, 20, 400, 300],
                    polygon=[[0,20],[400,20],[400,300],[0,300]],
                    confidence=0.8
                )
            ],
            image_dimensions=(800, 600),
            processing_metadata={"total_blocks": 2}
        )
        
        result = visual_contextualizer.should_analyze_visually(ui_output)
        assert result is True
    
    def test_visual_block_detection_negative(self, visual_contextualizer):
        """Test that non-visual blocks don't trigger analysis"""
        ui_output = UIFormattedOutput(
            blocks=[
                UIBlock(
                    id="text_1",
                    block_type="Text",
                    html_content="<p>Question</p>",
                    raw_content="Question text", 
                    bbox=[0, 0, 100, 20],
                    polygon=[[0,0],[100,0],[100,20],[0,20]],
                    confidence=0.9
                ),
                UIBlock(
                    id="equation_1",
                    block_type="Equation",
                    html_content="<math>x^2</math>",
                    raw_content="x^2",
                    bbox=[0, 20, 50, 40],
                    polygon=[[0,20],[50,20],[50,40],[0,40]],
                    confidence=0.95
                )
            ],
            image_dimensions=(800, 600),
            processing_metadata={"total_blocks": 2}
        )
        
        result = visual_contextualizer.should_analyze_visually(ui_output)
        assert result is False
    
    def test_analyze_skip_when_no_visual_blocks(self, visual_contextualizer):
        """Test that analysis is skipped when no visual blocks present"""
        user_selection = UserSelection(
            selected_block_ids=["text_1"],
            edited_latex="Test problem",
            original_image_path="/fake/path.png"
        )
        
        ui_output = UIFormattedOutput(
            blocks=[
                UIBlock(
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
        
        result = visual_contextualizer.analyze(user_selection, ui_output)
        assert result is None
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key", "GOOGLE_API_KEY": "fake-key"})
    def test_analyze_with_mock_vlm_response(self, visual_contextualizer):
        """Test analysis flow with mocked VLM response"""
        # Setup test data
        user_selection = UserSelection(
            selected_block_ids=["figure_1"],
            edited_latex="Which function is monotonic?",
            original_image_path="./benchmarks/data/samples/input_cases/one_problem/multi_choice_diagram.png"
        )
        
        ui_output = UIFormattedOutput(
            blocks=[
                UIBlock(
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
        
        # Mock VLM response
        mock_vlm_output = VisualContextOutput(
            natural_description="Graph showing two functions on coordinate plane",
            visual_elements=[
                VisualElement(
                    type="function_graph",
                    description="Blue decreasing curve",
                    mathematical_properties={"monotonicity": "decreasing"}
                )
            ],
            mathematical_relevance="Blue function is monotonic decreasing",
            confidence=0.9
        )
        
        mock_response = MagicMock()
        mock_response.parsed = mock_vlm_output
        visual_contextualizer.model_manager.chat.return_value = mock_response
        
        # Test analysis
        result = visual_contextualizer.analyze(user_selection, ui_output)
        
        # Verify result
        assert result is not None
        assert result.relevance_score == 0.9
        assert "Blue function is monotonic decreasing" in result.description
        assert "function_graph: Blue decreasing curve" in result.description
        
        # Verify VLM was called correctly
        visual_contextualizer.model_manager.chat.assert_called_once()
        call_args = visual_contextualizer.model_manager.chat.call_args
        
        assert call_args[1]["task"] == "vision"
        assert call_args[1]["json_mode"] is True
        assert call_args[1]["response_format"] == VisualContextOutput


class TestVLMTimeout:
    """Test VLM timeout and retry behavior"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key", "GOOGLE_API_KEY": "fake-key"})
    def test_vlm_timeout_graceful_failure(self):
        """Test that VLM timeouts don't crash the pipeline"""
        mock_manager = MagicMock(spec=ModelManager)
        mock_manager.chat.side_effect = TimeoutError("VLM request timed out")
        
        contextualizer = VisualContextualizer(mock_manager)
        
        user_selection = UserSelection(
            selected_block_ids=["figure_1"],
            edited_latex="Test problem",
            original_image_path="/fake/path.png"
        )
        
        ui_output = UIFormattedOutput(
            blocks=[
                UIBlock(
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
        
        # Should return None gracefully, not raise exception
        result = contextualizer.analyze(user_selection, ui_output)
        assert result is None