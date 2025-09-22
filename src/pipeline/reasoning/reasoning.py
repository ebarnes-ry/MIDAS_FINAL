import re
from typing import Dict, Any
from src.models.manager import ModelManager
from .types import ReasoningInput, ReasoningOutput

class ReasoningPipeline:
    def __init__(self, manager: ModelManager):
        self.model_manager = manager
    
    def process(self, reasoning_input: ReasoningInput) -> ReasoningOutput:
        """
        Process reasoning input using phi4-mini-reasoning model
        """
        print(f"Starting reasoning process...")
        print(f"Problem statement: {reasoning_input.problem_statement}...")
        
        # Prepare variables for the prompt
        variables = {
            "problem_text": reasoning_input.problem_statement
        }
        
        # Add visual context if available (only if not None/empty)
        if reasoning_input.visual_context and reasoning_input.visual_context.strip():
            variables["visual_context"] = reasoning_input.visual_context
            print(f"Visual context provided: {reasoning_input.visual_context}...")
        else:
            print(f"")
        
        print(f"Variables being sent to model: {list(variables.keys())}")
        print(f"Variable values: {[(k, len(str(v)) if isinstance(v, str) else type(v).__name__) for k, v in variables.items()]}")
        
        # Call the reasoning model
        print(f"Calling model_manager.call with task='reasoning', prompt_ref='reasoning/solve@v1'")
        try:
            response = self.model_manager.call(
                task="reasoning",
                prompt_ref="reasoning/solve@v1",
                variables=variables
            )
            print(f"Model response received, content length: {len(response.content)}")
        except Exception as e:
            print(f"Model call failed: {e}")
            print(f"Error type: {type(e).__name__}")
            raise
        
        # Parse the response to extract components
        parsed_output = self._parse_reasoning_response(response.content)
        
        return ReasoningOutput(
            original_problem=reasoning_input.problem_statement,
            worked_solution=parsed_output["worked_solution"],
            final_answer=parsed_output["final_answer"],
            think_reasoning=parsed_output["think_reasoning"],
            processing_metadata={
                "model_used": "phi4-mini-reasoning:latest",
                "prompt_version": "reasoning/solve@v1",
                "source_metadata": reasoning_input.source_metadata or {},
                "raw_response_length": len(response.content)
            }
        )
    
    def _parse_reasoning_response(self, response_content: str) -> Dict[str, str]:
        """
        Parse the reasoning response to extract think tags, worked solution, and final answer
        """
        # Extract content within <think> tags
        think_match = re.search(r'<think>(.*?)</think>', response_content, re.DOTALL)
        think_reasoning = think_match.group(1).strip() if think_match else ""
        
        # Remove think tags from the response to get the worked solution
        worked_solution = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
        
        # Try to extract final answer (look for boxed answer patterns)
        final_answer = self._extract_final_answer(worked_solution)
        
        return {
            "think_reasoning": think_reasoning,
            "worked_solution": worked_solution,
            "final_answer": final_answer
        }
    
    def _extract_final_answer(self, worked_solution: str) -> str:
        # Look for boxed pattern with balanced braces
        import re
        pattern = r'\\boxed\{'
        match = re.search(pattern, worked_solution)
        if match:
            start = match.end() - 1  # Position of opening brace
            brace_count = 0
            for i, char in enumerate(worked_solution[start:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return worked_solution[start+1:start+i].strip()
        # Look for common boxed answer patterns
        patterns = [
            r'\\boxed\{([^}]+)\}',  # LaTeX boxed
            r'\\box\{([^}]+)\}',    # Alternative LaTeX box
            r'Answer:\s*([^\n]+)',  # Plain text answer
            r'Final answer:\s*([^\n]+)',  # Alternative plain text
            r'Therefore,\s*([^\n]+)',  # Therefore pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, worked_solution, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no specific pattern found, try to get the last line or last sentence
        lines = [line.strip() for line in worked_solution.split('\n') if line.strip()]
        if lines:
            return lines[-1]
        
        return "No clear final answer found"