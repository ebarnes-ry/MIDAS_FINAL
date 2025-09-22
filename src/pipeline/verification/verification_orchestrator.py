"""
Verification orchestrator that handles the complete verification pipeline
including reasoning repair when verification fails due to reasoning issues.
"""

import time
from typing import Tuple, Optional, List
from dataclasses import dataclass, field

from .verification import VerificationPipeline
from .verification_types import VerificationResult
from ..reasoning.reasoning import ReasoningPipeline
from ..reasoning.types import ReasoningOutput
from src.models.manager import ModelManager

@dataclass
class RepairAttempt:
    """Record of a repair attempt"""
    attempt_number: int
    repair_type: str
    reason: str
    success: bool
    processing_time: float
    error_message: Optional[str] = None
    repaired_reasoning: Optional[ReasoningOutput] = field(default=None, repr=False)

class VerificationOrchestrator:
    """
    Orchestrates the full verification pipeline with reasoning repair capability.
    """

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.verification_pipeline = VerificationPipeline(model_manager)
        self.reasoning_pipeline = ReasoningPipeline(model_manager)

    def verify_with_repair(self, reasoning_output: ReasoningOutput, max_reasoning_attempts: int = 2) -> Tuple[VerificationResult, List[RepairAttempt]]:
        """
        Main method that performs verification with automatic repair capabilities.
        """
        repair_history = []
        current_reasoning = reasoning_output

        for attempt in range(max_reasoning_attempts + 1):
            # The first loop (attempt 0) is the initial verification.
            # Subsequent loops are for repair attempts.
            if attempt > 0:
                print(f"--- Reasoning Repair Attempt {attempt}/{max_reasoning_attempts} ---")
                start_time = time.time()
                
                # Attempt to get a repaired reasoning
                repaired_reasoning = self._attempt_reasoning_repair(current_reasoning, verification_result)
                
                # Log the repair attempt
                processing_time = time.time() - start_time
                repair_attempt = RepairAttempt(
                    attempt_number=attempt,
                    repair_type="reasoning",
                    reason=f"Reasoning verification failed with status: {verification_result.status}",
                    success=repaired_reasoning is not None,
                    processing_time=processing_time,
                    repaired_reasoning=repaired_reasoning
                )
                repair_history.append(repair_attempt)

                if not repaired_reasoning:
                    print("Reasoning repair failed to produce a new solution. Halting.")
                    break # Exit the loop if repair fails
                
                current_reasoning = repaired_reasoning

            # Run verification on the current version of the reasoning
            verification_result = self.verification_pipeline.verify(current_reasoning)

            # Check for an exit condition
            if verification_result.status == "verified":
                print("Verification successful.")
                return verification_result, repair_history
            
            if verification_result.status != "failed_reasoning":
                print(f"Halting repair loop due to non-reasoning error: {verification_result.status}")
                return verification_result, repair_history # Exit loop on codegen/pipeline errors
        
        print("Max reasoning repair attempts reached.")
        return verification_result, repair_history # Return the last failed result

    def _attempt_reasoning_repair(self, failed_reasoning: ReasoningOutput, verification_result: VerificationResult) -> Optional[ReasoningOutput]:
        """
        Attempts to repair reasoning by calling a dedicated repair prompt.
        Returns the new ReasoningOutput on success, or None on failure.
        """
        try:
            # Create the specific feedback for the repair prompt
            feedback = self._create_reasoning_repair_context(verification_result)

            # Call the dedicated 'reasoning_repair' task
            response = self.model_manager.call(
                task="reasoning_repair",
                prompt_ref="reasoning/repair@v1",
                variables={
                    "original_problem": failed_reasoning.original_problem,
                    "failed_solution": failed_reasoning.worked_solution,
                    "verification_feedback": feedback
                }
            )

            # The reasoning pipeline's parser can be reused to parse the output
            # of the repair prompt, as it follows the same <think>/solution format.
            parsed_output = self.reasoning_pipeline._parse_reasoning_response(response.content)

            return ReasoningOutput(
                original_problem=failed_reasoning.original_problem,
                worked_solution=parsed_output["worked_solution"],
                final_answer=parsed_output["final_answer"],
                think_reasoning=parsed_output["think_reasoning"],
                processing_metadata={
                    "source": "reasoning_repair",
                    "original_failure": verification_result.status
                }
            )
        except Exception as e:
            print(f"Error during reasoning repair call: {e}")
            return None

    def _create_reasoning_repair_context(
        self,
        verification_result: VerificationResult
    ) -> str:
        """
        Creates a concise feedback string for the reasoning repair prompt.
        """
        context_parts = []
        for error in verification_result.errors:
            context_parts.append(f"- {error.message}")

        # Add step-specific feedback if available
        failed_steps = [s for s in verification_result.step_verifications if not s.verified]
        if failed_steps:
            context_parts.append("\nThe following steps were proven incorrect:")
            for step in failed_steps:
                context_parts.append(f"  - Step {step.step_number}: {step.description}")
        
        return "\n".join(context_parts)