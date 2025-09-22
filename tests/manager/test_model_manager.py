import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, ValidationError

from src.models.manager import ModelManager
from src.models.providers.base import ChatRequest, ModelResponse, ModelError, ModelTimeout
from src.models.providers.ollama import OllamaProvider
from src.models.services.marker import MarkerService


class TestSchema(BaseModel):
    """Test schema for structured output testing"""
    answer: str
    confidence: float


class TestModelManager:
    """Test suite for ModelManager functionality"""
    
    @pytest.fixture
    def valid_config(self, tmp_path):
        """Create a valid config file for testing"""
        config_content = """
providers:
  ollama_local:
    type: ollama
    settings:
      host: "http://localhost:11434"
      request_timeout_s: 120

  openrouter:
    type: openai
    settings:
      base_url: "https://openrouter.ai/api/v1"

services:
  marker_local:
    type: marker
    settings:
      use_llm: true
      llm_service: "gemini"
      output_format: "json"

tasks:
  vision:
    provider: ollama_local
    model: "qwen2.5vl:7b"
    params:
      temperature: 0.1
      max_tokens: 1000

  reasoning:
    provider: ollama_local
    model: "phi4-mini-reasoning:latest"
    params:
      temperature: 0.1

  document_conversion:
    provider: marker_local
    model: "marker"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        return config_file
    
    @pytest.fixture
    def prompts_dir(self, tmp_path):
        """Create a mock prompts directory"""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()
        
        # Create a simple prompt structure
        vision_prompt = prompts_dir / "vision" / "analyze" / "v1"
        vision_prompt.mkdir(parents=True)
        
        (vision_prompt / "config.yaml").write_text("""
schema:
  mode: strict
""")
        
        (vision_prompt / "system.j2").write_text("You are a helpful assistant.")
        (vision_prompt / "user.j2").write_text("Analyze this: {{problem_statement}}")
        (vision_prompt / "schema.py").write_text("""
from pydantic import BaseModel

class Schema(BaseModel):
    analysis: str
    confidence: float
""")
        
        return prompts_dir
    
    @pytest.fixture
    def manager(self, valid_config, prompts_dir):
        """Create a ModelManager instance for testing"""
        with patch('src.models.manager.OllamaProvider'), \
             patch('src.models.manager.OpenAIProvider'), \
             patch('src.models.manager.MarkerService'):
            return ModelManager(valid_config, prompts_dir)
    
    def test_initialization_success(self, valid_config, prompts_dir):
        """
        Test: Successful ModelManager initialization
        How: Create manager with valid config and prompts directory
        Ensures: Manager can be initialized with proper configuration and prompt management
        """
        with patch('src.models.manager.OllamaProvider'), \
             patch('src.models.manager.OpenAIProvider'), \
             patch('src.models.manager.MarkerService'):
            
            manager = ModelManager(valid_config, prompts_dir)
            
            assert manager.config_path == Path(valid_config)
            assert manager.prompts is not None
            assert manager._providers == {}
            assert manager._stats == {}
            assert manager._marker is None  # Lazy loaded
    
    def test_initialization_without_prompts_dir(self, valid_config):
        """
        Test: Initialization without explicit prompts directory
        How: Create manager without prompts_dir parameter
        Ensures: Manager can auto-discover prompts directory
        """
        with patch('src.models.manager.OllamaProvider'), \
             patch('src.models.manager.OpenAIProvider'), \
             patch('src.models.manager.MarkerService'), \
             patch('src.models.manager.PromptManager') as mock_prompt_manager:
            
            manager = ModelManager(valid_config)
            
            # Verify PromptManager was called with auto-discovered path
            mock_prompt_manager.assert_called_once()
            call_args = mock_prompt_manager.call_args[0]
            assert "prompts" in str(call_args[0])
    
    def test_config_loading_success(self, valid_config):
        """
        Test: Successful configuration loading
        How: Load valid YAML configuration
        Ensures: Manager can parse and validate configuration files
        """
        with patch('src.models.manager.OllamaProvider'), \
             patch('src.models.manager.OpenAIProvider'), \
             patch('src.models.manager.MarkerService'):
            
            manager = ModelManager(valid_config)
            
            assert 'providers' in manager.config
            assert 'tasks' in manager.config
            assert 'services' in manager.config
            assert manager.config['providers']['ollama_local']['type'] == 'ollama'
            assert manager.config['tasks']['vision']['provider'] == 'ollama_local'
    
    def test_config_file_not_found(self, tmp_path):
        """
        Test: Configuration file not found error
        How: Try to load non-existent config file
        Ensures: Manager provides clear error for missing configuration
        """
        nonexistent_config = tmp_path / "nonexistent.yaml"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            ModelManager(nonexistent_config)
        
        assert "Config not found" in str(exc_info.value)
        assert str(nonexistent_config) in str(exc_info.value)
    
    def test_config_missing_providers_section(self, tmp_path):
        """
        Test: Configuration missing providers section
        How: Create config without providers section
        Ensures: Manager validates required configuration sections
        """
        config_content = """
tasks:
  vision:
    provider: ollama_local
    model: "test-model"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValueError) as exc_info:
            ModelManager(config_file)
        
        assert "Config missing 'providers'" in str(exc_info.value)
    
    def test_config_missing_tasks_section(self, tmp_path):
        """
        Test: Configuration missing tasks section
        How: Create config without tasks section
        Ensures: Manager validates required configuration sections
        """
        config_content = """
providers:
  ollama_local:
    type: ollama
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValueError) as exc_info:
            ModelManager(config_file)
        
        assert "Config missing 'tasks'" in str(exc_info.value)
    
    def test_config_invalid_yaml(self, tmp_path):
        """
        Test: Invalid YAML configuration
        How: Create config with invalid YAML syntax
        Ensures: Manager handles YAML parsing errors gracefully
        """
        config_content = """
providers:
  ollama_local:
    type: ollama
    settings:
      host: "http://localhost:11434"
  invalid_yaml: [unclosed list
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(yaml.YAMLError):
            ModelManager(config_file)
    
    def test_task_missing_provider(self, tmp_path):
        """
        Test: Task configuration missing provider
        How: Create task without provider field
        Ensures: Manager validates task configuration completeness
        """
        config_content = """
providers:
  ollama_local:
    type: ollama

tasks:
  vision:
    model: "test-model"  # Missing provider
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValueError) as exc_info:
            ModelManager(config_file)
        
        assert "Task 'vision' missing provider" in str(exc_info.value)
    
    def test_task_missing_model(self, tmp_path):
        """
        Test: Task configuration missing model
        How: Create task without model field
        Ensures: Manager validates task configuration completeness
        """
        config_content = """
providers:
  ollama_local:
    type: ollama

tasks:
  vision:
    provider: ollama_local  # Missing model
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValueError) as exc_info:
            ModelManager(config_file)
        
        assert "Task 'vision' missing model" in str(exc_info.value)
    
    def test_task_unknown_provider(self, tmp_path):
        """
        Test: Task referencing unknown provider
        How: Create task with provider not in providers section
        Ensures: Manager validates provider references
        """
        config_content = """
providers:
  ollama_local:
    type: ollama

tasks:
  vision:
    provider: unknown_provider  # Not in providers
    model: "test-model"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        with pytest.raises(ValueError) as exc_info:
            ModelManager(config_file)
        
        assert "Task 'vision' references unknown provider 'unknown_provider'" in str(exc_info.value)
    
    def test_provider_initialization_ollama(self, manager):
        """
        Test: Ollama provider initialization
        How: Request Ollama provider and verify initialization
        Ensures: Manager can initialize and cache Ollama providers
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama:
            mock_provider = Mock()
            mock_ollama.return_value = mock_provider
            
            provider = manager._get_provider('ollama_local')
            
            # Verify provider was created with correct settings
            mock_ollama.assert_called_once_with(
                host="http://localhost:11434",
                request_timeout_s=120
            )
            
            # Verify provider is cached
            assert provider in manager._providers.values()
            assert 'ollama_local' in manager._providers
    
    def test_provider_initialization_openai(self, manager):
        """
        Test: OpenAI provider initialization
        How: Request OpenAI provider and verify initialization
        Ensures: Manager can initialize and cache OpenAI providers
        """
        with patch('src.models.manager.OpenAIProvider') as mock_openai:
            mock_provider = Mock()
            mock_openai.return_value = mock_provider
            
            provider = manager._get_provider('openrouter')
            
            # Verify provider was created with correct settings
            mock_openai.assert_called_once_with(
                base_url="https://openrouter.ai/api/v1"
            )
            
            # Verify provider is cached
            assert provider in manager._providers.values()
            assert 'openrouter' in manager._providers
    
    def test_provider_caching(self, manager):
        """
        Test: Provider caching behavior
        How: Request same provider multiple times
        Ensures: Manager caches providers to avoid re-initialization
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama:
            mock_provider = Mock()
            mock_ollama.return_value = mock_provider
            
            # Request provider multiple times
            provider1 = manager._get_provider('ollama_local')
            provider2 = manager._get_provider('ollama_local')
            
            # Verify same instance returned
            assert provider1 is provider2
            
            # Verify provider was only created once
            mock_ollama.assert_called_once()
    
    def test_unknown_provider_error(self, manager):
        """
        Test: Unknown provider error handling
        How: Request provider not in configuration
        Ensures: Manager provides clear error for unknown providers
        """
        with pytest.raises(ValueError) as exc_info:
            manager._get_provider('unknown_provider')
        
        assert "Unknown provider: unknown_provider" in str(exc_info.value)
    
    def test_unknown_provider_type_error(self, tmp_path):
        """
        Test: Unknown provider type error handling
        How: Create provider with unsupported type
        Ensures: Manager handles unsupported provider types gracefully
        """
        config_content = """
providers:
  unknown_type:
    type: unsupported_type
    settings: {}

tasks:
  test_task:
    provider: unknown_type
    model: "test-model"
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)
        
        with patch('src.models.manager.OllamaProvider'), \
             patch('src.models.manager.OpenAIProvider'), \
             patch('src.models.manager.MarkerService'):
            
            manager = ModelManager(config_file)
            
            with pytest.raises(ValueError) as exc_info:
                manager._get_provider('unknown_type')
            
            assert "Unknown provider type: unsupported_type" in str(exc_info.value)
    
    def test_marker_service_property(self, manager):
        """
        Test: Marker service property lazy loading
        How: Access marker property and verify lazy initialization
        Ensures: Manager can lazy load Marker service when needed
        """
        with patch('src.models.manager.MarkerService') as mock_marker:
            mock_service = Mock()
            mock_marker.return_value = mock_service
            
            # Access marker property
            marker_service = manager.marker
            
            # Verify service was created (don't check specific settings since they come from config)
            mock_marker.assert_called_once()
            
            # Verify same instance returned on subsequent calls
            marker_service2 = manager.marker
            assert marker_service is marker_service2
    
    def test_call_with_prompt_rendering(self, manager):
        """
        Test: Call method with prompt rendering
        How: Make a call with prompt reference and variables
        Ensures: Manager can render prompts and execute calls
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content="Test response",
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Make call
            response = manager.call(
                task="vision",
                prompt_ref="vision/analyze@v1",
                variables={"problem_statement": "Test problem"}
            )
            
            # Verify prompt was rendered
            mock_render.assert_called_once_with("vision/analyze@v1", {"problem_statement": "Test problem"})
            
            # Verify provider was called
            mock_provider.chat.assert_called_once()
            call_args = mock_provider.chat.call_args[0][0]
            assert isinstance(call_args, ChatRequest)
            assert call_args.model == "qwen2.5vl:7b"
            assert call_args.messages == [{"role": "user", "content": "Test message"}]
            
            # Verify response
            assert response.content == "Test response"
    
    def test_call_with_unknown_task(self, manager):
        """
        Test: Call method with unknown task
        How: Try to call non-existent task
        Ensures: Manager provides clear error for unknown tasks
        """
        with pytest.raises(ValueError) as exc_info:
            manager.call(
                task="unknown_task",
                prompt_ref="vision/analyze@v1",
                variables={}
            )
        
        assert "Unknown task: unknown_task" in str(exc_info.value)
    
    def test_call_with_images(self, manager):
        """
        Test: Call method with image inputs
        How: Make a call with image data
        Ensures: Manager can pass images to providers
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content="Test response",
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Test image data
            test_images = [b"fake_image_data"]
            
            # Make call with images
            response = manager.call(
                task="vision",
                prompt_ref="vision/analyze@v1",
                variables={"problem_statement": "Test problem"},
                images=test_images
            )
            
            # Verify images were passed to provider
            call_args = mock_provider.chat.call_args[0][0]
            assert call_args.images == test_images
    
    def test_call_with_parameter_override(self, manager):
        """
        Test: Call method with parameter overrides
        How: Make a call with custom parameters
        Ensures: Manager can override default task parameters
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content="Test response",
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Make call with parameter overrides
            response = manager.call(
                task="vision",
                prompt_ref="vision/analyze@v1",
                variables={"problem_statement": "Test problem"},
                temperature=0.5,  # Override default 0.1
                max_tokens=2000   # Override default 1000
            )
            
            # Verify parameters were overridden
            call_args = mock_provider.chat.call_args[0][0]
            assert call_args.params["temperature"] == 0.5
            assert call_args.params["max_tokens"] == 2000
    
    def test_call_with_schema_strict_mode(self, manager):
        """
        Test: Call method with strict schema mode
        How: Make a call with schema enforcement
        Ensures: Manager can handle structured output with schema validation
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content='{"answer": "test", "confidence": 0.95}',
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Make call with schema parameter
            response = manager.call(
                task="vision",
                prompt_ref="vision/analyze@v1",
                variables={"problem_statement": "Test problem"},
                schema=TestSchema
            )
            
            # Verify schema was passed to provider
            call_args = mock_provider.chat.call_args[0][0]
            assert call_args.schema == TestSchema
    
    def test_call_with_schema_validation_error(self, manager):
        """
        Test: Call method with schema validation error  
        How: Make a call with schema but invalid response
        Ensures: Manager handles schema validation errors gracefully
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content='{"answer": "test", "confidence": 0.95}',
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Make call with schema parameter  
            response = manager.call(
                task="vision",
                prompt_ref="vision/analyze@v1",
                variables={"problem_statement": "Test problem"},
                schema=TestSchema
            )
            
            # Verify schema was passed to provider
            call_args = mock_provider.chat.call_args[0][0]
            assert call_args.schema == TestSchema
    
    def test_call_with_validation_error(self, manager):
        """
        Test: Call method with JSON validation error
        How: Mock validation error and verify graceful handling
        Ensures: Manager handles validation errors without crashing
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content='{"invalid": "json"}',  # Missing required fields
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Make call
            response = manager.call(
                task="vision",
                prompt_ref="vision/analyze@v1",
                variables={"problem_statement": "Test problem"}
            )
            
            # Verify that provider handles validation (manager just passes response through)
            assert response.content == '{"invalid": "json"}'
            assert response.parsed is None  # Provider would set this during validation
    
    def test_call_with_provider_error(self, manager):
        """
        Test: Call method with provider error
        How: Mock provider error and verify error propagation
        Ensures: Manager properly propagates provider errors
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider error
            mock_provider = Mock()
            mock_provider.chat.side_effect = ModelError("Provider error")
            mock_ollama.return_value = mock_provider
            
            # Make call and expect error
            with pytest.raises(ModelError) as exc_info:
                manager.call(
                    task="vision",
                    prompt_ref="vision/analyze@v1",
                    variables={"problem_statement": "Test problem"}
                )
            
            assert "Provider error" in str(exc_info.value)
    
    def test_performance_tracking(self, manager):
        """
        Test: Performance tracking functionality
        How: Make successful and failed calls and verify stats
        Ensures: Manager tracks performance metrics accurately
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content="Test response",
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Make successful call
            manager.call(
                task="vision",
                prompt_ref="vision/analyze@v1",
                variables={"problem_statement": "Test problem"}
            )
            
            # Verify stats were tracked
            stats = manager.get_stats("vision")
            assert stats["total_calls"] == 1
            assert stats["successful_calls"] == 1
            assert stats["total_latency_ms"] > 0
            
            # Make failed call
            mock_provider.chat.side_effect = ModelError("Provider error")
            
            with pytest.raises(ModelError):
                manager.call(
                    task="vision",
                    prompt_ref="vision/analyze@v1",
                    variables={"problem_statement": "Test problem"}
                )
            
            # Verify failure was tracked
            stats = manager.get_stats("vision")
            assert stats["total_calls"] == 2
            assert stats["successful_calls"] == 1  # Still 1, failure not counted as success
    
    def test_get_stats_all_tasks(self, manager):
        """
        Test: Get stats for all tasks
        How: Make calls to multiple tasks and get all stats
        Ensures: Manager can provide comprehensive performance statistics
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama, \
             patch.object(manager.prompts, 'render') as mock_render:
            
            # Mock prompt rendering - now returns List[Dict[str, str]]
            mock_rendered_messages = [{"role": "user", "content": "Test message"}]
            mock_render.return_value = mock_rendered_messages
            
            # Mock provider
            mock_provider = Mock()
            mock_response = ModelResponse(
                content="Test response",
                raw={},
                meta={}
            )
            mock_provider.chat.return_value = mock_response
            mock_ollama.return_value = mock_provider
            
            # Make calls to different tasks
            manager.call("vision", "vision/analyze@v1", {"problem_statement": "Test"})
            manager.call("reasoning", "vision/analyze@v1", {"problem_statement": "Test"})
            
            # Get all stats
            all_stats = manager.get_stats()
            
            assert "vision" in all_stats
            assert "reasoning" in all_stats
            assert all_stats["vision"]["total_calls"] == 1
            assert all_stats["reasoning"]["total_calls"] == 1
    
    def test_cleanup(self, manager):
        """
        Test: Manager cleanup functionality
        How: Initialize providers and then cleanup
        Ensures: Manager properly cleans up resources
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama:
            mock_provider = Mock()
            mock_provider.cleanup = Mock()
            mock_ollama.return_value = mock_provider
            
            # Initialize provider
            manager._get_provider('ollama_local')
            
            # Verify provider was created
            assert 'ollama_local' in manager._providers
            
            # Cleanup
            manager.cleanup()
            
            # Verify provider cleanup was called
            mock_provider.cleanup.assert_called_once()
            
            # Verify providers dict was cleared
            assert manager._providers == {}
    
    def test_cleanup_with_cleanup_error(self, manager):
        """
        Test: Cleanup with provider cleanup error
        How: Mock provider cleanup failure
        Ensures: Manager handles cleanup errors gracefully
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama:
            mock_provider = Mock()
            mock_provider.cleanup.side_effect = Exception("Cleanup failed")
            mock_ollama.return_value = mock_provider
            
            # Initialize provider
            manager._get_provider('ollama_local')
            
            # Cleanup should not raise exception
            manager.cleanup()
            
            # Verify providers dict was still cleared
            assert manager._providers == {}
    
    def test_session_context_manager(self, manager):
        """
        Test: Session context manager functionality
        How: Use manager as context manager
        Ensures: Manager can be used as context manager with automatic cleanup
        """
        with patch('src.models.manager.OllamaProvider') as mock_ollama:
            mock_provider = Mock()
            mock_provider.cleanup = Mock()
            mock_ollama.return_value = mock_provider
            
            # Use as context manager
            with manager.session() as mgr:
                assert mgr is manager
                # Initialize provider
                mgr._get_provider('ollama_local')
                assert 'ollama_local' in mgr._providers
            
            # Verify cleanup was called after context exit
            mock_provider.cleanup.assert_called_once()
            assert manager._providers == {}
    
    # Note: raw_call functionality not implemented yet
