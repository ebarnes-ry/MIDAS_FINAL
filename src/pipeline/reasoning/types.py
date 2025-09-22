from dataclasses import dataclass
from typing import Optional, Dict, Any
from pydantic import BaseModel

# Input types
@dataclass
class ReasoningInput:
    problem_statement: str
    visual_context: Optional[str] = None  # Optional visual context from vision pipeline
    source_metadata: Optional[Dict[str, Any]] = None

# Output types
@dataclass
class ReasoningOutput:
    original_problem: str
    worked_solution: str
    final_answer: str
    think_reasoning: str  # Content within <think> tags
    processing_metadata: Dict[str, Any]
