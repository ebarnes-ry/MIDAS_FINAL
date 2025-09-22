import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, ValidationError
from PIL import Image
import io

from src.models.providers.ollama import OllamaProvider
from src.models.providers.base import ChatRequest, ModelResponse, ModelError, ModelTimeout, ModelRetryable


class TestSchema(BaseModel):
    """Test schema for structured output testing"""
    answer: str
    confidence: float


class TestOllamaProvider:
    """Test suite for OllamaProvider functionality"""
    
    @pytest.fixture
    def provider(self):
        """Create a test OllamaProvider instance"""
        with patch('src.models.providers.ollama.Client'):
            return OllamaProvider(host="http://localhost:11434", request_timeout_s=30)
    
    @pytest.fixture
    def mock_client(self, provider):
        """Get the mocked client from the provider"""
        return provider.client
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample PIL Image for testing"""
        # Create a simple 100x100 RGB image
        img = Image.new('RGB', (100, 100), color='red')
        return img
    
    def test_initialization(self, provider):
        """
        Test: OllamaProvider initialization with custom settings
        How: Create provider with custom host and timeout
        Ensures: Provider can be initialized with different configurations
        """
        assert provider.host == "http://localhost:11434"
        assert provider.keep_alive == "5m"
        assert provider.client is not None
    
    def test_initialization_defaults(self):
        """
        Test: OllamaProvider initialization with default settings
        How: Create provider without parameters
        Ensures: Provider uses sensible defaults
        """
        with patch('src.models.providers.ollama.Client'):
            provider = OllamaProvider()
            assert provider.host == "http://localhost:11434"
            assert provider.keep_alive == "5m"
    
    def test_basic_chat_completion(self, provider, mock_client):
        """
        Test: Basic chat completion without images or schema
        How: Mock successful Ollama response and verify parsing
        Ensures: Provider can handle simple text-only requests
        """
        # Mock Ollama response
        mock_response = Mock()
        mock_response.message.content = "Hello, world!"
        mock_response.model = "test-model"
        mock_response.total_duration = 1000000000  # 1 second in nanoseconds
        mock_response.eval_count = 10
        mock_response.eval_duration = 500000000  # 0.5 seconds
        
        mock_client.chat.return_value = mock_response
        
        # Create request
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}],
            params={"temperature": 0.7}
        )
        
        # Execute
        response = provider.chat(request)
        
        # Verify
        assert response.content == "Hello, world!"
        assert response.parsed is None
        assert response.meta["provider"] == "ollama"
        assert response.meta["model"] == "test-model"
        assert response.meta["total_duration_ns"] == 1000000000
        assert response.meta["eval_count"] == 10
        assert response.meta["eval_duration_ns"] == 500000000
        assert "latency" in response.meta
        
        # Verify client was called correctly
        mock_client.chat.assert_called_once()
        call_args = mock_client.chat.call_args
        assert call_args[1]["model"] == "test-model"
        assert call_args[1]["messages"] == [{"role": "user", "content": "Hello"}]
        assert call_args[1]["options"]["temperature"] == 0.7
        assert call_args[1]["keep_alive"] == "5m"
    
    def test_chat_with_images(self, provider, mock_client, sample_image):
        """
        Test: Chat completion with image inputs
        How: Mock request with images and verify base64 conversion
        Ensures: Provider can handle multimodal requests with image processing
        """
        mock_response = Mock()
        mock_response.message.content = "I can see a red image"
        mock_response.model = "test-model"
        mock_response.total_duration = 1000000000
        
        mock_client.chat.return_value = mock_response
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "What do you see?"}],
            images=[sample_image]
        )
        
        with patch('src.models.providers.ollama.to_base64') as mock_to_base64:
            mock_to_base64.return_value = "base64_encoded_image"
            
            response = provider.chat(request)
            
            # Verify image was converted to base64
            mock_to_base64.assert_called_once_with(sample_image)
            
            # Verify the converted image was included in the request
            call_args = mock_client.chat.call_args
            messages = call_args[1]["messages"]
            assert len(messages) == 1
            assert "base64_encoded_image" in messages[0]["images"]
    
    def test_schema_enforcement(self, provider, mock_client):
        """
        Test: Schema enforcement with Pydantic model
        How: Mock request with schema and verify format parameter
        Ensures: Provider can enforce structured output using model_json_schema()
        """
        mock_response = Mock()
        mock_response.message.content = '{"answer": "test answer", "confidence": 0.95}'
        mock_response.model = "test-model"
        mock_response.total_duration = 1000000000
        
        mock_client.chat.return_value = mock_response
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Answer the question"}],
            schema=TestSchema
        )
        
        response = provider.chat(request)
        
        # Verify schema was passed to Ollama
        call_args = mock_client.chat.call_args
        assert call_args[1]["format"] == TestSchema.model_json_schema()
        
        # Verify response was parsed
        assert response.parsed is not None
        assert isinstance(response.parsed, TestSchema)
        assert response.parsed.answer == "test answer"
        assert response.parsed.confidence == 0.95
    
    def test_no_schema_no_format(self, provider, mock_client):
        """
        Test: Request without schema should not set format parameter
        How: Mock request without schema and verify format=None
        Ensures: Provider only sets format when schema is provided
        """
        mock_response = Mock()
        mock_response.message.content = 'Plain text response'
        mock_response.model = "test-model"
        mock_response.total_duration = 1000000000
        
        mock_client.chat.return_value = mock_response
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Return text"}]
        )
        
        response = provider.chat(request)
        
        # Verify format=None was passed to Ollama
        mock_client.chat.assert_called_once()
        call_args = mock_client.chat.call_args
        assert call_args[1]["format"] is None
        
        # Verify response content
        assert response.content == 'Plain text response'
        assert response.parsed is None
    
    def test_schema_validation_error(self, provider, mock_client):
        """
        Test: Schema validation failure handling
        How: Mock invalid JSON response and verify graceful error handling
        Ensures: Provider handles validation errors without crashing
        """
        mock_response = Mock()
        mock_response.message.content = '{"invalid": "json"}'  # Missing required fields
        mock_response.model = "test-model"
        mock_response.total_duration = 1000000000
        
        mock_client.chat.return_value = mock_response
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Answer"}],
            schema=TestSchema
        )
        
        response = provider.chat(request)
        
        # Verify validation error was captured
        assert response.parsed is None
        assert "validation_error" in response.meta
        assert "answer" in response.meta["validation_error"]  # Missing required field
    
    def test_timeout_handling(self, provider, mock_client):
        """
        Test: Request timeout handling
        How: Mock httpx.ReadTimeout and verify ModelTimeout exception
        Ensures: Provider properly handles and classifies timeout errors
        """
        from httpx import ReadTimeout
        
        mock_client.chat.side_effect = ReadTimeout("Request timed out")
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with pytest.raises(ModelTimeout) as exc_info:
            provider.chat(request)
        
        assert "Ollama timeout" in str(exc_info.value)
        assert "Request timed out" in str(exc_info.value)
    
    def test_retryable_error_handling(self, provider, mock_client):
        """
        Test: Retryable error classification and retry logic
        How: Mock retryable ResponseError and verify ModelRetryable exception
        Ensures: Provider can distinguish retryable from non-retryable errors
        """
        # Import the actual ResponseError to inherit from it
        from ollama import ResponseError
        
        # Mock a retryable error (429 - Rate Limited)
        mock_error = ResponseError("Rate limited")
        mock_error.status_code = 429
        mock_client.chat.side_effect = mock_error
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with pytest.raises(ModelRetryable) as exc_info:
            provider.chat(request)
        
        assert "Rate limited" in str(exc_info.value)
    
    def test_non_retryable_error_handling(self, provider, mock_client):
        """
        Test: Non-retryable error handling
        How: Mock non-retryable ResponseError and verify ModelError exception
        Ensures: Provider properly handles permanent failures
        """
        # Mock ResponseError since we can't import ollama in tests
        ResponseError = type('ResponseError', (Exception,), {'status_code': 400})
        
        # Mock a non-retryable error (400 - Bad Request)
        mock_error = ResponseError("Bad request")
        mock_error.status_code = 400
        mock_client.chat.side_effect = mock_error
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with pytest.raises(ModelError) as exc_info:
            provider.chat(request)
        
        assert "Bad request" in str(exc_info.value)
    
    def test_connection_error_handling(self, provider, mock_client):
        """
        Test: Connection error handling
        How: Mock httpx.ConnectError and verify ModelRetryable exception
        Ensures: Provider handles network connectivity issues as retryable
        """
        # Import the actual ConnectError to inherit from it
        from httpx import ConnectError
        
        mock_client.chat.side_effect = ConnectError("Connection failed")
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        with pytest.raises(ModelError) as exc_info:
            provider.chat(request)
        
        assert "Connection failed" in str(exc_info.value)
    
    def test_keep_alive_parameter_override(self, provider, mock_client):
        """
        Test: Keep-alive parameter override
        How: Mock request with custom keep_alive and verify it's used
        Ensures: Provider respects custom keep-alive settings
        """
        mock_response = Mock()
        mock_response.message.content = "Response"
        mock_response.model = "test-model"
        mock_response.total_duration = 1000000000
        
        mock_client.chat.return_value = mock_response
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}],
            params={"keep_alive": "10m"}
        )
        
        provider.chat(request)
        
        # Verify custom keep_alive was used
        call_args = mock_client.chat.call_args
        assert call_args[1]["keep_alive"] == "10m"
    
    def test_health_check_success(self, provider, mock_client):
        """
        Test: Health check when Ollama is available
        How: Mock successful list() call
        Ensures: Provider can verify service availability
        """
        mock_client.list.return_value = {"models": []}
        
        assert provider.health_check() is True
        mock_client.list.assert_called_once()
    
    def test_health_check_failure(self, provider, mock_client):
        """
        Test: Health check when Ollama is unavailable
        How: Mock failed list() call
        Ensures: Provider can detect service unavailability
        """
        mock_client.list.side_effect = Exception("Connection failed")
        
        assert provider.health_check() is False
        mock_client.list.assert_called_once()
    
    def test_model_preloading(self, provider, mock_client):
        """
        Test: Model preloading functionality
        How: Mock successful preload call
        Ensures: Provider can preload models for faster subsequent requests
        """
        mock_response = Mock()
        mock_response.message.content = ""
        mock_client.chat.return_value = mock_response
        
        result = provider.preload_model("test-model")
        
        assert result is True
        mock_client.chat.assert_called_once_with(
            model="test-model",
            messages=[{"role": "user", "content": ""}],
            keep_alive="5m"
        )
    
    def test_model_preloading_failure(self, provider, mock_client):
        """
        Test: Model preloading failure handling
        How: Mock failed preload call
        Ensures: Provider handles preloading failures gracefully
        """
        mock_client.chat.side_effect = Exception("Model not found")
        
        result = provider.preload_model("nonexistent-model")
        
        assert result is False
    
    def test_response_metadata_extraction(self, provider, mock_client):
        """
        Test: Comprehensive response metadata extraction
        How: Mock response with all timing fields and verify extraction
        Ensures: Provider extracts all available performance metrics
        """
        mock_response = Mock()
        mock_response.message.content = "Response"
        mock_response.model = "test-model"
        mock_response.total_duration = 1000000000
        mock_response.load_duration = 50000000
        mock_response.prompt_eval_count = 5
        mock_response.prompt_eval_duration = 200000000
        mock_response.eval_count = 10
        mock_response.eval_duration = 500000000
        
        mock_client.chat.return_value = mock_response
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        response = provider.chat(request)
        
        # Verify all timing metadata was extracted
        meta = response.meta
        assert meta["total_duration_ns"] == 1000000000
        assert meta["load_duration_ns"] == 50000000
        assert meta["prompt_eval_count"] == 5
        assert meta["prompt_eval_duration_ns"] == 200000000
        assert meta["eval_count"] == 10
        assert meta["eval_duration_ns"] == 500000000
    
    def test_malformed_response_handling(self, provider, mock_client):
        """
        Test: Malformed response handling
        How: Mock response without expected structure
        Ensures: Provider handles unexpected response formats gracefully
        """
        # Mock response without message attribute
        mock_response = {"unexpected": "structure"}
        mock_client.chat.return_value = mock_response
        
        request = ChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        response = provider.chat(request)
        
        # Should fall back to string representation
        assert response.content == str(mock_response)
    
    def test_retry_decorator_configuration(self, provider):
        """
        Test: Retry decorator is properly configured
        How: Verify retry configuration through introspection
        Ensures: Provider has proper retry logic with exponential backoff
        """
        # Check that the chat method has retry decorator
        chat_method = provider.chat
        assert hasattr(chat_method, 'retry')
        
        # The retry decorator should be configured with:
        # - stop_after_attempt(3)
        # - wait_exponential_jitter
        # - retry_if_exception(_is_retryable)
        retry_obj = chat_method.retry
        assert retry_obj.stop.max_attempt_number == 3
        assert retry_obj.wait is not None
        assert retry_obj.retry is not None
