"""
API models for the code generation pipeline endpoints.

These Pydantic models define the request/response schemas for code generation,
handling the transition from reasoning to SymPy code generation.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from .common import APIResponse

# API Request Models
class CodegenRequest(BaseModel):
    """Request for generating SymPy code from reasoning output."""
    problem_statement: str = Field(..., description="Original problem statement")
    worked_solution: str = Field(..., description="Step-by-step worked solution")
    final_answer: str = Field(..., description="Final answer from reasoning")
    think_reasoning: Optional[str] = Field(None, description="Internal reasoning process")
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="Source metadata from previous stages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem_statement": "Find the derivative of f(x) = x^2 + 3x + 1",
                "worked_solution": "To find the derivative of f(x) = x^2 + 3x + 1...",
                "final_answer": "2x + 3",
                "think_reasoning": "I need to apply the power rule for derivatives...",
                "source_metadata": {
                    "reasoning_model": "phi4-mini-reasoning:latest"
                }
            }
        }

# API Response Models
class CodegenResponse(APIResponse):
    """Response after code generation processing."""
    data: Optional['CodegenData'] = None

class CodegenData(BaseModel):
    """Data payload for code generation response."""
    original_problem: str = Field(..., description="Original problem statement")
    worked_solution: str = Field(..., description="Step-by-step worked solution")
    final_answer: str = Field(..., description="Final answer from reasoning")
    generated_code: str = Field(..., description="Generated SymPy code")
    processing_time: float = Field(..., description="Processing time in seconds")
    processing_metadata: Dict[str, Any] = Field(..., description="Processing details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_problem": "Find the derivative of f(x) = x^2 + 3x + 1",
                "worked_solution": "To find the derivative of f(x) = x^2 + 3x + 1...",
                "final_answer": "2x + 3",
                "generated_code": "from sympy import *\nx = symbols('x')\nf = x**2 + 3*x + 1\nderivative = diff(f, x)\nprint(derivative)",
                "processing_time": 1.23,
                "processing_metadata": {
                    "model_used": "qwen2.5-coder:7b-instruct",
                    "prompt_version": "codegen/baseline_codegen@v1"
                }
            }
        }

# Update forward references
CodegenResponse.model_rebuild()
