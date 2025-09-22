"""
API models for the verification pipeline endpoints with reasoning repair capability.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from .common import APIResponse

# Request Models
class VerificationRequest(BaseModel):
    """Request for verification with potential reasoning repair."""
    problem_statement: str = Field(..., description="Original problem statement")
    worked_solution: str = Field(..., description="Step-by-step worked solution")
    final_answer: str = Field(..., description="Final answer from reasoning")
    think_reasoning: Optional[str] = Field(None, description="Internal reasoning process")
    source_metadata: Optional[Dict[str, Any]] = Field(None, description="Source metadata from previous stages")

    # Verification-specific options
    enable_reasoning_repair: bool = Field(True, description="Whether to attempt reasoning repair if verification fails")
    max_reasoning_attempts: int = Field(2, description="Maximum reasoning repair attempts")

    class Config:
        json_schema_extra = {
            "example": {
                "problem_statement": "Find the derivative of f(x) = x^2 + 3x + 1",
                "worked_solution": "To find the derivative of f(x) = x^2 + 3x + 1...",
                "final_answer": "2x + 3",
                "think_reasoning": "I need to apply the power rule for derivatives...",
                "enable_reasoning_repair": True,
                "max_reasoning_attempts": 2
            }
        }

class ReasoningRepairRequest(BaseModel):
    """Request for reasoning repair based on verification failures."""
    original_problem: str = Field(..., description="Original problem statement")
    failed_solution: str = Field(..., description="The solution that failed verification")
    failed_answer: str = Field(..., description="The answer that failed verification")
    verification_errors: List[str] = Field(..., description="List of verification error messages")
    verification_context: Dict[str, Any] = Field(..., description="Additional context from verification")

# Response Models
class VerificationResponse(APIResponse):
    """Response after verification processing with potential reasoning repair."""
    data: Optional['VerificationData'] = None

class VerificationData(BaseModel):
    """Data payload for verification response."""
    # Final verified results
    original_problem: str = Field(..., description="Original problem statement")
    final_solution: str = Field(..., description="Final verified solution")
    final_answer: str = Field(..., description="Final verified answer")
    generated_code: str = Field(..., description="Generated SymPy verification code")

    # Verification details
    status: str = Field(..., description="Final verification status")
    confidence_score: float = Field(..., description="Confidence in verification")
    verification_passed: bool = Field(..., description="Whether verification ultimately passed")

    # Processing metadata
    processing_time: float = Field(..., description="Total processing time in seconds")
    reasoning_repair_attempts: int = Field(0, description="Number of reasoning repair attempts made")
    codegen_repair_attempts: int = Field(0, description="Number of codegen repair attempts made")

    # Detailed history
    repair_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of repair attempts")
    processing_metadata: Dict[str, Any] = Field(..., description="Processing details")

    class Config:
        json_schema_extra = {
            "example": {
                "original_problem": "Find the derivative of f(x) = x^2 + 3x + 1",
                "final_solution": "To find the derivative of f(x) = x^2 + 3x + 1...",
                "final_answer": "2x + 3",
                "generated_code": "from sympy import *\nx = symbols('x')\nf = x**2 + 3*x + 1\nderivative = diff(f, x)\nprint(derivative)",
                "status": "verified",
                "confidence_score": 0.95,
                "verification_passed": True,
                "processing_time": 3.45,
                "reasoning_repair_attempts": 1,
                "codegen_repair_attempts": 0,
                "repair_history": [
                    {
                        "attempt": 1,
                        "type": "reasoning_repair",
                        "reason": "Final answer mismatch",
                        "success": True
                    }
                ]
            }
        }

# Update forward references
VerificationResponse.model_rebuild()