"""
Code generation pipeline API endpoints.
"""

import time
from fastapi import APIRouter, Depends, HTTPException

from ..models.codegen import CodegenRequest, CodegenResponse, CodegenData
from ..dependencies.session import get_model_manager
from src.models.manager import ModelManager
from src.pipeline.verification.verification import VerificationPipeline
from src.pipeline.reasoning.types import ReasoningOutput

router = APIRouter()

@router.post("/generate", response_model=CodegenResponse)
async def generate_code(
    request: CodegenRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Generate SymPy code from reasoning output. This is a standalone endpoint for the verification stage.
    """
    start_time = time.time()
    
    try:
        verification_pipeline = VerificationPipeline(model_manager)
        
        # Adapt the request to the ReasoningOutput type that the pipeline expects
        reasoning_input = ReasoningOutput(
            original_problem=request.problem_statement,
            worked_solution=request.worked_solution,
            final_answer=request.final_answer,
            think_reasoning=request.think_reasoning or "",
            processing_metadata=request.source_metadata or {}
        )
        
        verification_result = verification_pipeline.verify(reasoning_input)
        
        processing_time = time.time() - start_time
        
        response_data = CodegenData(
            original_problem=verification_result.reasoning_output.original_problem,
            worked_solution=verification_result.reasoning_output.worked_solution,
            final_answer=verification_result.reasoning_output.final_answer,
            generated_code=verification_result.generated_code,
            processing_time=processing_time,
            processing_metadata={
                "status": verification_result.status,
                "confidence": verification_result.confidence_score,
                **verification_result.metadata
            }
        )
        
        return CodegenResponse(
            success=True,
            message="Code generation and verification completed.",
            data=response_data
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")