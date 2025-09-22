"""
Debug test to understand why verification is failing
"""

import pytest
from unittest.mock import Mock
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from src.models.manager import ModelManager
from src.pipeline.reasoning.types import ReasoningOutput
from src.pipeline.verification.verification import VerificationPipeline


def test_debug_code_generation():
    """Debug the code generation step"""

    # Create mock model manager
    mock_manager = Mock(spec=ModelManager)
    mock_manager.config = {
        "tasks": {
            "verification": {
                "model": "qwen2.5-coder:7b-instruct",
                "params": {"temperature": 0.1, "max_tokens": 2000},
                "prompt_ref": "codegen/baseline_codegen@v2",
                "provider": "ollama_local",
                "max_repair_attempts": 3,
                "confidence_threshold": 0.95,
                "min_acceptable_confidence": 0.7,
                "repair_temperature": 0.2,
                "execution_timeout": 10,
                "memory_limit_mb": 512
            }
        }
    }

    # Mock a simple successful response
    mock_response = Mock()
    mock_response.content = """```python
from sympy import *

# Calculate 15 × 24
result = 15 * 24
print(f"Result: {result}")
print(f"Final answer matches: {result == 360}")
print(f"Computed: {result}, Claimed: 360")
```"""

    mock_manager.call.return_value = mock_response

    # Create reasoning input
    reasoning = ReasoningOutput(
        original_problem="Calculate: 15 × 24",
        worked_solution="15 × 24 = 360",
        final_answer="360",
        think_reasoning="<think>Simple multiplication</think>",
        processing_metadata={"test": True}
    )

    # Test code generation directly
    pipeline = VerificationPipeline(mock_manager)

    try:
        code, metadata = pipeline.code_generator.generate(reasoning)
        print(f"Generated code: {code}")
        print(f"Metadata: {metadata}")

        # Test execution
        execution_result = pipeline.executor.execute(code)
        print(f"Execution success: {execution_result.success}")
        print(f"Stdout: {execution_result.stdout}")
        print(f"Stderr: {execution_result.stderr}")

        # Test full verification
        result = pipeline.verify(reasoning)
        print(f"Verification status: {result.status}")
        print(f"Confidence: {result.confidence_score}")
        print(f"Errors: {result.errors}")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_debug_code_generation()