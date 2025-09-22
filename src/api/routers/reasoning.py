"""
Reasoning pipeline API endpoints.

These endpoints provide HTTP access to the reasoning processing pipeline,
handling the transition from vision analysis to mathematical reasoning.
"""

import time
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ..models.reasoning import ReasoningRequest, ReasoningResponse, ReasoningData
from ..dependencies.session import get_model_manager
from src.models.manager import ModelManager
from src.pipeline.reasoning.reasoning import ReasoningPipeline
from src.pipeline.reasoning.types import ReasoningInput

router = APIRouter()

@router.post("/reason", response_model=ReasoningResponse)
async def process_reasoning(
    request: ReasoningRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Process reasoning on a problem statement.
    
    This endpoint:
    1. Takes a problem statement and optional visual context
    2. Processes it through the reasoning pipeline
    3. Returns the worked solution, final answer, and internal reasoning
    """
    
    start_time = time.time()
    print(f"Starting reasoning processing for problem: {request.problem_statement[:100]}...")
    
    try:
        # Initialize reasoning pipeline
        reasoning_pipeline = ReasoningPipeline(model_manager)
        
        # Create ReasoningInput from request
        reasoning_input = ReasoningInput(
            problem_statement=request.problem_statement,
            visual_context=request.visual_context,
            source_metadata=request.source_metadata
        )
        
        print(f"Processing reasoning with model...")
        # Process through reasoning pipeline
        reasoning_output = reasoning_pipeline.process(reasoning_input)
        
        processing_time = time.time() - start_time
        print(f"Reasoning processing completed in {processing_time:.2f}s")
        
        # Create response data
        response_data = ReasoningData(
            original_problem=reasoning_output.original_problem,
            worked_solution=reasoning_output.worked_solution,
            final_answer=reasoning_output.final_answer,
            think_reasoning=reasoning_output.think_reasoning,
            processing_time=processing_time,
            processing_metadata=reasoning_output.processing_metadata
        )
        
        return ReasoningResponse(
            success=True,
            message="Reasoning processing completed successfully",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            data=response_data
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Reasoning processing failed: {str(e)}"
        print(f"Error: {error_msg}")
        
        return ReasoningResponse(
            success=False,
            message=error_msg,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            data=None
        )
# At the end of src/api/routers/reasoning.py

from ..models.reasoning import ReasoningExplainRequest, ReasoningExplainResponse, ReasoningExplainData

@router.post("/explain", response_model=ReasoningExplainResponse)
async def explain_step(
    request: ReasoningExplainRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Provide a detailed explanation for a single step in a worked solution.
    """
    start_time = time.time()
    try:
        response = model_manager.call(
            task="explain_step",
            prompt_ref="reasoning/explain_step@v1",
            variables={
                "problem_statement": request.problem_statement,
                "worked_solution": request.worked_solution,
                "step_text": request.step_text,
            }
        )
        
        processing_time = time.time() - start_time
        
        return ReasoningExplainResponse(
            success=True,
            message="Explanation generated successfully.",
            data=ReasoningExplainData(
                explanation=response.content,
                processing_time=processing_time
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {e}")