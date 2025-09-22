import json
from typing import List, Optional, Tuple, Dict, Any

from .verification_types import CodeExecutionResult, StepVerification

class VerificationOutputParser:
    """
    Parses the stdout of a verification script that adheres to the strict JSON contract.
    """
    def parse(self, execution_result: CodeExecutionResult) -> Tuple[List[StepVerification], Optional[Dict[str, Any]], Optional[Exception]]:
        """
        Parses the stdout for JSON objects.

        Returns:
            - A list of StepVerification objects.
            - A dictionary containing the final verdict.
            - An exception if parsing fails (indicating a contract violation).
        """
        if not execution_result.success:
            return [], None, None

        stdout = execution_result.stdout.strip()
        step_verifications = []
        final_verdict = None
        
        lines = stdout.splitlines()
        
        try:
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                data = json.loads(line)
                
                if "step" in data and "verified" in data:
                    # Validate required fields before creating StepVerification
                    if not isinstance(data["step"], int) or not isinstance(data["verified"], bool):
                        continue  # Skip malformed step verification
                    step_verifications.append(StepVerification(
                        step_number=data["step"],
                        description=data.get("description", ""),
                        verified=data["verified"]
                    ))
                elif "final_answer_verified" in data:
                    # Validate final verdict structure
                    if isinstance(data.get("final_answer_verified"), bool):
                        final_verdict = data
            
            return step_verifications, final_verdict, None
        except json.JSONDecodeError as e:
            # This indicates the codegen model violated the contract.
            return step_verifications, final_verdict, e
        except Exception as e:
            return step_verifications, final_verdict, e