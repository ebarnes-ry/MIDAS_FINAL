"""
Verification pipeline API endpoints with reasoning repair orchestration.
"""

import time
from fastapi import APIRouter, Depends, HTTPException

from ..models.verification import VerificationRequest, VerificationResponse, VerificationData
from ..dependencies.session import get_model_manager
from src.models.manager import ModelManager
from src.pipeline.verification.verification_orchestrator import VerificationOrchestrator
from src.pipeline.reasoning.types import ReasoningOutput

router = APIRouter()


@router.post("/verify", response_model=VerificationResponse)
async def verify_with_repair(
    request: VerificationRequest,
    model_manager: ModelManager = Depends(get_model_manager)
):
    """
    Complete verification pipeline with reasoning repair capability.

    This endpoint:
    1. Takes reasoning output and performs verification
    2. If verification fails due to reasoning issues, attempts reasoning repair
    3. Re-verifies the repaired reasoning
    4. Returns the final verification result with repair history

    This addresses the key missing functionality of reasoning repair orchestration.
    """
    start_time = time.time()

    try:
        # Initialize verification orchestrator
        orchestrator = VerificationOrchestrator(model_manager)

        # Convert request to ReasoningOutput
        reasoning_output = ReasoningOutput(
            original_problem=request.problem_statement,
            worked_solution=request.worked_solution,
            final_answer=request.final_answer,
            think_reasoning=request.think_reasoning or "",
            processing_metadata=request.source_metadata or {}
        )

        # Run verification with repair capability
        print(f"Starting verification with repair for problem: {request.problem_statement[:100]}...")
        max_attempts = request.max_reasoning_attempts if request.enable_reasoning_repair else 0
        verification_result, repair_history = orchestrator.verify_with_repair(
            reasoning_output=reasoning_output,
            max_reasoning_attempts=max_attempts
        )

        processing_time = time.time() - start_time
        print(f"Verification completed in {processing_time:.2f}s with {len(repair_history)} repair attempts")

        # Convert repair history to serializable format
        repair_history_data = []
        reasoning_attempts = 0
        codegen_attempts = 0

        for repair in repair_history:
            if repair.repair_type == "reasoning":
                reasoning_attempts += 1
            elif repair.repair_type == "codegen":
                codegen_attempts += 1

            repair_history_data.append({
                "attempt": repair.attempt_number,
                "type": repair.repair_type,
                "reason": repair.reason,
                "success": repair.success,
                "processing_time": repair.processing_time,
                "error_message": repair.error_message
            })

        # Determine if reasoning was repaired from metadata
        final_reasoning = verification_result.reasoning_output
        if hasattr(verification_result, 'metadata') and verification_result.metadata.get('repaired_from_codegen_fault'):
            codegen_attempts += 1

        # Create response data
        response_data = VerificationData(
            original_problem=final_reasoning.original_problem,
            final_solution=final_reasoning.worked_solution,
            final_answer=final_reasoning.final_answer,
            generated_code=verification_result.generated_code,
            status=verification_result.status,
            confidence_score=verification_result.confidence_score,
            verification_passed=(verification_result.status == "verified"),
            processing_time=processing_time,
            reasoning_repair_attempts=reasoning_attempts,
            codegen_repair_attempts=codegen_attempts,
            repair_history=repair_history_data,
            processing_metadata={
                "verification_status": verification_result.status,
                "confidence": verification_result.confidence_score,
                "errors": [e.message for e in verification_result.errors],
                "step_verifications": len(verification_result.step_verifications),
                **verification_result.metadata
            }
        )

        return VerificationResponse(
            success=True,
            message=f"Verification completed with status: {verification_result.status}",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            data=response_data
        )

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Verification with repair failed: {str(e)}"
        print(f"Error: {error_msg}")

        import traceback
        traceback.print_exc()

        return VerificationResponse(
            success=False,
            message=error_msg,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            data=None
        )