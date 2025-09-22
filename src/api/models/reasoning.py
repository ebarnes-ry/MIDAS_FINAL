"""
API models for the reasoning pipeline endpoints.

These Pydantic models define the request/response schemas for reasoning processing,
handling the transition from vision analysis to mathematical reasoning.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

from .common import APIResponse

# API Request Models
class ReasoningRequest(BaseModel):
    """Request for processing reasoning on a problem statement."""
    problem_statement: str = Field(..., description="The problem statement to reason about")
    visual_context: Optional[str] = Field(None, description="Visual context from vision analysis")
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="Source metadata from vision pipeline")
    
    class Config:
        json_schema_extra = {
            "example": {
                "problem_statement": "Find the derivative of f(x) = x^2 + 3x + 1",
                "visual_context": "The function is a quadratic polynomial",
                "source_metadata": {
                    "selected_blocks": ["block_1", "block_2"],
                    "processing_method": "marker_json_optimized"
                }
            }
        }

# API Response Models
class ReasoningResponse(APIResponse):
    """Response after reasoning processing."""
    data: Optional['ReasoningData'] = None

class ReasoningData(BaseModel):
    """Data payload for reasoning response."""
    original_problem: str = Field(..., description="Original problem statement")
    worked_solution: str = Field(..., description="Step-by-step worked solution")
    final_answer: str = Field(..., description="Final answer extracted from solution")
    think_reasoning: str = Field(..., description="Internal reasoning process")
    processing_time: float = Field(..., description="Processing time in seconds")
    processing_metadata: Dict[str, Any] = Field(..., description="Processing details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_problem": "Find the derivative of f(x) = x^2 + 3x + 1",
                "worked_solution": "To find the derivative of f(x) = x^2 + 3x + 1...",
                "final_answer": "2x + 3",
                "think_reasoning": "I need to apply the power rule for derivatives...",
                "processing_time": 2.45,
                "processing_metadata": {
                    "model_used": "phi4-mini-reasoning:latest",
                    "prompt_version": "reasoning/solve@v1"
                }
            }
        }

class ReasoningExplainRequest(BaseModel):
    problem_statement: str
    worked_solution: str
    step_text: str

class ReasoningExplainData(BaseModel):
    explanation: str
    processing_time: float

class ReasoningExplainResponse(APIResponse):
    data: Optional[ReasoningExplainData] = None

# Update the forward reference at the end of the file
ReasoningResponse.model_rebuild()
ReasoningExplainResponse.model_rebuild() # Add this line