# tests/test_prompts.py

import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Optional

from src.models.prompts import PromptManager, PromptConfig


@pytest.fixture
def temp_prompts_dir():
    """Create a temporary prompts directory with test data"""
    temp_dir = tempfile.mkdtemp()
    prompts_path = Path(temp_dir)
    
    # Create test prompt structure
    vision_v1 = prompts_path / "vision" / "analyze" / "v1"
    vision_v1.mkdir(parents=True)
    
    # Basic prompt with stop sequences
    (vision_v1 / "config.yaml").write_text("""
stop_sequences:
  - "END"
  - "STOP"
""")
    
    (vision_v1 / "system.j2").write_text("""You are analyzing images for mathematical problems.

Your task:
1. Identify visual elements in the image
2. Describe how each element relates to the problem
3. Extract structured data if present""")
    
    (vision_v1 / "user.j2").write_text("""Problem: {{ problem_statement }}
{% if context is defined %}
Context: {{ context }}
{% endif %}
{% if additional_info is defined %}
Additional information: {{ additional_info }}
{% endif %}""")
    
    # Create a reasoning prompt without config file
    reasoning_v1 = prompts_path / "reasoning" / "solve" / "v1"
    reasoning_v1.mkdir(parents=True)
    
    (reasoning_v1 / "system.j2").write_text("You solve mathematical problems step by step.")
    (reasoning_v1 / "user.j2").write_text("Solve: {{ problem }}")
    
    # Create a prompt with minimal config (empty)
    minimal_v1 = prompts_path / "minimal" / "test" / "v1" 
    minimal_v1.mkdir(parents=True)
    
    (minimal_v1 / "config.yaml").write_text("")  # Empty config
    (minimal_v1 / "system.j2").write_text("Simple system prompt.")
    (minimal_v1 / "user.j2").write_text("User: {{ input }}")
    
    yield prompts_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_prompts_dir):
    """Create a PromptManager with test data"""
    return PromptManager(temp_prompts_dir)


# ============ Prompt Loading Tests ============

class TestPromptLoading:    
    def test_load_valid_prompt_with_config(self, manager):
        """Load a prompt that exists with config file"""
        config = manager.load_prompt("vision/analyze@v1")
        
        assert config.name == "vision/analyze"
        assert config.version == "v1"
        assert config.stop_sequences == ["END", "STOP"]
        assert "analyzing images" in config.system_template.lower()
        assert "{{ problem_statement }}" in config.user_template
    
    def test_load_prompt_without_config(self, manager):
        """Load a prompt without config file"""
        config = manager.load_prompt("reasoning/solve@v1")
        
        assert config.name == "reasoning/solve"
        assert config.version == "v1"
        assert config.stop_sequences is None
        assert "solve mathematical problems" in config.system_template.lower()
    
    def test_load_prompt_with_empty_config(self, manager):
        """Load a prompt with empty config file"""
        config = manager.load_prompt("minimal/test@v1")
        
        assert config.name == "minimal/test"
        assert config.version == "v1"
        assert config.stop_sequences is None
    
    def test_load_missing_prompt(self, manager):
        """Fail clearly when prompt doesn't exist"""
        with pytest.raises(FileNotFoundError, match="Prompt not found"):
            manager.load_prompt("vision/analyze@v99")
    
    def test_load_missing_system_template(self, temp_prompts_dir, manager):
        """Fail clearly when system.j2 is missing"""
        broken_prompt = temp_prompts_dir / "broken" / "test" / "v1"
        broken_prompt.mkdir(parents=True)
        (broken_prompt / "user.j2").write_text("User prompt")
        # Missing system.j2
        
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            manager.load_prompt("broken/test@v1")
    
    def test_load_missing_user_template(self, temp_prompts_dir, manager):
        """Fail clearly when user.j2 is missing"""
        broken_prompt = temp_prompts_dir / "broken2" / "test" / "v1"
        broken_prompt.mkdir(parents=True)
        (broken_prompt / "system.j2").write_text("System prompt")
        # Missing user.j2
        
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            manager.load_prompt("broken2/test@v1")
    
    def test_invalid_reference_format(self, manager):
        """Fail clearly on bad reference format"""
        with pytest.raises(ValueError, match="Invalid prompt reference"):
            manager.load_prompt("vision/analyze")  # Missing version
    
    def test_caching(self, manager):
        """Verify prompts are cached after first load"""
        # First load
        config1 = manager.load_prompt("vision/analyze@v1")
        
        # Second load should return same object
        config2 = manager.load_prompt("vision/analyze@v1")
        
        assert config1 is config2  # Same object, not just equal

    def test_prompt_config_ref_property(self, manager):
        """Test PromptConfig.ref property works correctly"""
        config = manager.load_prompt("vision/analyze@v1")
        assert config.ref == "vision/analyze@v1"


# ============ Prompt Rendering Tests ============

class TestPromptRendering:    
    def test_render_with_all_variables(self, manager):
        """Render with all required and optional variables"""
        messages = manager.render(
            "vision/analyze@v1",
            {
                "problem_statement": "Find the area under the curve",
                "context": "Grade 10 calculus",
                "additional_info": "Use integration"
            }
        )
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "analyzing images" in messages[0]["content"].lower()
        assert "Find the area under the curve" in messages[1]["content"]
        assert "Grade 10 calculus" in messages[1]["content"]
        assert "Use integration" in messages[1]["content"]
    
    def test_render_with_only_required_variables(self, manager):
        """Render with only required variables"""
        messages = manager.render(
            "vision/analyze@v1",
            {"problem_statement": "Find the area"}
        )
        
        assert len(messages) == 2
        assert "Find the area" in messages[1]["content"]
        # Optional variables should not appear
        assert "Context:" not in messages[1]["content"]
        assert "Additional information:" not in messages[1]["content"]
    
    def test_render_missing_required_variable(self, manager):
        """Fail clearly when required variable is missing"""
        with pytest.raises(ValueError, match="Missing required variable"):
            manager.render(
                "vision/analyze@v1",
                {"context": "Grade 10"}  # Missing problem_statement
            )
    
    def test_render_simple_prompt(self, manager):
        """Render a simple prompt without conditionals"""
        messages = manager.render(
            "reasoning/solve@v1",
            {"problem": "What is 2 + 2?"}
        )
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "solve mathematical problems" in messages[0]["content"].lower()
        assert "Solve: What is 2 + 2?" in messages[1]["content"]
    
    def test_render_returns_correct_format(self, manager):
        """Verify render returns correct message format"""
        messages = manager.render(
            "minimal/test@v1",
            {"input": "test input"}
        )
        
        # Should be a list of dicts with role and content
        assert isinstance(messages, list)
        assert len(messages) == 2
        
        for message in messages:
            assert isinstance(message, dict)
            assert "role" in message
            assert "content" in message
            assert isinstance(message["role"], str)
            assert isinstance(message["content"], str)
        
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_render_with_jinja_features(self, temp_prompts_dir, manager):
        """Test that Jinja2 features work correctly"""
        # Create a prompt that uses loops and filters
        complex_prompt = temp_prompts_dir / "complex" / "test" / "v1"
        complex_prompt.mkdir(parents=True)
        
        (complex_prompt / "system.j2").write_text("System with {{ items|length }} items.")
        (complex_prompt / "user.j2").write_text("""Items:
{% for item in items %}
- {{ item|upper }}
{% endfor %}""")
        
        messages = manager.render(
            "complex/test@v1",
            {"items": ["apple", "banana", "cherry"]}
        )
        
        assert "System with 3 items" in messages[0]["content"]
        assert "- APPLE" in messages[1]["content"]
        assert "- BANANA" in messages[1]["content"]
        assert "- CHERRY" in messages[1]["content"]


# ============ Configuration Tests ============

class TestConfiguration:
    def test_load_config_with_stop_sequences(self, manager):
        """Test loading config with stop sequences"""
        config = manager.load_prompt("vision/analyze@v1")
        assert config.stop_sequences == ["END", "STOP"]
    
    def test_load_config_without_file(self, manager):
        """Test loading when no config file exists"""
        config = manager.load_prompt("reasoning/solve@v1")
        assert config.stop_sequences is None
    
    def test_load_config_empty_file(self, manager):
        """Test loading with empty config file"""
        config = manager.load_prompt("minimal/test@v1")
        assert config.stop_sequences is None

    def test_config_with_invalid_yaml(self, temp_prompts_dir, manager):
        """Test handling of invalid YAML in config"""
        bad_config = temp_prompts_dir / "bad" / "yaml" / "v1"
        bad_config.mkdir(parents=True)
        
        (bad_config / "config.yaml").write_text("invalid: yaml: [unclosed")
        (bad_config / "system.j2").write_text("System")
        (bad_config / "user.j2").write_text("User")
        
        # Should raise an exception when trying to load
        with pytest.raises(Exception):  # YAML parsing error
            manager.load_prompt("bad/yaml@v1")


# ============ Error Handling Tests ============

class TestErrorHandling:
    def test_prompt_manager_invalid_directory(self):
        """Test PromptManager with non-existent directory"""
        with pytest.raises(FileNotFoundError, match="Prompts dir not found"):
            PromptManager(Path("/nonexistent/directory"))
    
    def test_render_with_undefined_variable_strict(self, manager):
        """Test that undefined variables cause strict failures"""
        with pytest.raises(ValueError, match="Missing required variable"):
            manager.render(
                "vision/analyze@v1", 
                {}  # No variables provided
            )


# ============ Cache Management Tests ============

class TestCacheManagement:
    def test_cache_performance(self, manager):
        """Test that caching improves performance"""
        import time
        
        # First load (should be slower - loading from disk)
        start = time.perf_counter()
        config1 = manager.load_prompt("vision/analyze@v1")
        first_load_time = time.perf_counter() - start
        
        # Second load (should be faster - from cache)
        start = time.perf_counter()
        config2 = manager.load_prompt("vision/analyze@v1")
        cached_load_time = time.perf_counter() - start
        
        # Cached load should be significantly faster
        assert cached_load_time < first_load_time
        assert config1 is config2
    
    def test_clear_cache(self, manager):
        """Test cache clearing functionality"""
        # Load a prompt to populate cache
        config1 = manager.load_prompt("vision/analyze@v1")
        assert "vision/analyze@v1" in manager._cache
        
        # Clear cache
        manager.clear_cache()
        assert manager._cache == {}
        
        # Load again should create new object
        config2 = manager.load_prompt("vision/analyze@v1")
        assert config1 is not config2  # Different objects
        assert config1.name == config2.name  # But same content


# ============ Integration Tests ============

class TestIntegration:
    """Test complete workflows as they'll be used by the model manager"""
    
    def test_vision_workflow(self, manager):
        """Test typical vision pipeline usage"""
        # Load and render a vision prompt
        messages = manager.render(
            "vision/analyze@v1",
            {
                "problem_statement": "Calculate the area of the triangle shown",
                "context": "High school geometry"
            }
        )
        
        # Should get properly formatted messages for model call
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "triangle" in messages[1]["content"]
        assert "geometry" in messages[1]["content"]
    
    def test_reasoning_workflow(self, manager):
        """Test typical reasoning pipeline usage"""
        messages = manager.render(
            "reasoning/solve@v1",
            {"problem": "If x + 5 = 12, what is x?"}
        )
        
        # Should get clean messages without any schema references
        system_content = messages[0]["content"]
        user_content = messages[1]["content"]
        
        assert "schema" not in system_content.lower()
        assert "json" not in system_content.lower()
        assert "If x + 5 = 12" in user_content
    
    def test_multiple_prompt_versions(self, temp_prompts_dir, manager):
        """Test handling multiple versions of same prompt"""
        # Create v2 of vision prompt
        vision_v2 = temp_prompts_dir / "vision" / "analyze" / "v2"
        vision_v2.mkdir(parents=True)
        
        (vision_v2 / "system.j2").write_text("You are an advanced image analyzer.")
        (vision_v2 / "user.j2").write_text("Advanced analysis: {{ problem_statement }}")
        
        # Load both versions
        v1_messages = manager.render("vision/analyze@v1", {"problem_statement": "test"})
        v2_messages = manager.render("vision/analyze@v2", {"problem_statement": "test"})
        
        # Should be different content
        assert v1_messages[0]["content"] != v2_messages[0]["content"]
        assert "advanced" in v2_messages[0]["content"].lower()
        assert "Advanced analysis:" in v2_messages[1]["content"]