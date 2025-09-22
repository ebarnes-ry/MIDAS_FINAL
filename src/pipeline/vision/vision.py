from src.models.manager import ModelManager
from .types import Problem, VisionInput, UserSelection, VisionFinalOutput, UIDocument, VisualContext
from .ui_transformer import UITransformer
from .vlm import VisualContextualizer
from .grouper import SemanticGrouper

from typing import Dict, Union, Optional, List, Tuple
from pathlib import Path
from PIL import Image
from difflib import SequenceMatcher
import re

class VisionPipeline:
    def __init__(self, manager: ModelManager):
        self.model_manager = manager
        self.marker_service = manager.marker #access marker service directly
        #self.visual_contextualizer = VisualContextualizer(manager)
        self.grouper = SemanticGrouper(manager)

    #def process_input(self, vision_input: VisionInput) -> UIDocument:
    def process_input(self, vision_input: VisionInput) -> UIDocument:
        """The main entry point for processing an uploaded document."""
        # Step 1: Use Marker for "dumb" OCR to get blocks and their raw text.
        marker_result = self.marker_service.convert_document(vision_input.file_path)
        if marker_result is None:
            raise ValueError("Marker processing failed")
        
        # Step 2: Transform Marker's messy output. The transformer does NOT get the image.
        ui_document = UITransformer.transform_marker_json(marker_result)

        # Step 3: Use the grouper on the full text to get semantically correct problems
        problems = self.grouper.group(ui_document.full_page_text)
        
        # Step 4: Link the found problems back to the original blocks for UI highlighting
        #ui_document.problems = self._link_problems_to_blocks(problems, ui_document)
        problems_with_blocks = self._link_problems_to_blocks(problems, ui_document)

        # Step 5: Explicitly associate figure descriptions with the problems.
        ui_document.problems = self._associate_descriptions_to_problems(problems_with_blocks, ui_document)
        
        return ui_document

    def _normalize_text(self, text: str) -> str:
        """A helper to clean text for robust comparison."""
        if not text:
            return ""
        # Lowercase, remove all non-alphanumeric characters, and collapse whitespace
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _link_problems_to_blocks(self, problems: List[Problem], document: UIDocument) -> List[Problem]:
        """
        Associate text-based problems with the UI blocks they originated from
        using a robust similarity matching algorithm.
        """
        print("\n--- Starting Block to Problem Linking Process ---")
        normalized_problems = { p.problem_id: self._normalize_text(p.problem_text) for p in problems }
        block_assignments: Dict[str, Tuple[str, float]] = {}

        for block in document.blocks:
            block_text = block.latex_content
            # print("\n\n\n\n\n\n\n\n")
            # print(block_text)
            if not block_text or not block_text.strip():
                continue

            normalized_block_text = self._normalize_text(block_text)
            if not normalized_block_text:
                continue

            # print("\n\n\n\n\n\n\n\n")
            # print(normalized_block_text)
            print(f"\n[DEBUG] Analyzing Block ID: {block.id}")
            print(f"  - Normalized Block Text: '{normalized_block_text}'")
            

            best_ratio = 0.0
            best_problem_id = None

            for problem_id, normalized_problem_text in normalized_problems.items():
                print(f"  - Normalized Problem Text: '{normalized_problem_text}'")
                if normalized_block_text in normalized_problem_text:
                    ratio = 1.0 # Perfect substring match
                else:
                    matcher = SequenceMatcher(None, normalized_block_text, normalized_problem_text)
                    match = matcher.find_longest_match(0, len(normalized_block_text), 0, len(normalized_problem_text))
                    ratio = match.size / len(normalized_block_text)

                print(f"  - Comparing with {problem_id}: Ratio = {ratio:.2f}")

                if ratio > best_ratio:
                    best_ratio = ratio
                    best_problem_id = problem_id
            
            # Use a slightly more lenient threshold and log the decision
            #threshold = 0.85
            threshold = 0.70
            if best_problem_id and best_ratio > threshold:
                block_assignments[block.id] = (best_problem_id, best_ratio)
                print(f"  ASSIGNED to {best_problem_id} (Ratio: {best_ratio:.2f} > {threshold})")
            else:
                print(f"  NOT ASSIGNED (Best Ratio: {best_ratio:.2f} <= {threshold})")

        # Second pass: Assign blocks to problems
        for problem in problems:
            problem.block_ids = [
                block_id for block_id, (p_id, ratio) in block_assignments.items()
                if p_id == problem.problem_id
            ]
        
        print("--- Block to Problem Linking Complete ---")
        return problems

    def _associate_descriptions_to_problems(self, problems: List[Problem], document: UIDocument) -> List[Problem]:
        """
        Linus's Note: I have rewritten this function to fix the silent failure.
        The old logic was too fragile. This version uses a robust heuristic.
        """
        figure_descriptions = [block.image_description for block in document.blocks if block.image_description]
        if not figure_descriptions:
            return problems # No descriptions to associate.

        for problem in problems:
            # Only associate descriptions if the LLM grouper identified a reference (e.g., "Figure 1").
            # This prevents associating a graph with a problem that doesn't mention one.
            if problem.figure_references:
                # For simplicity, we associate all available descriptions. A more advanced
                # implementation could match "Figure 1" to a specific description.
                problem.referenced_figure_descriptions = figure_descriptions
                print(f"Associated {len(problem.referenced_figure_descriptions)} descriptions with {problem.problem_id}")
        
        return problems

    def process_selection(self, user_selection: UserSelection, ui_document: UIDocument, source_image: Image.Image) -> VisionFinalOutput:
        # Find the full problem object based on the user's selection ID.
        selected_problem = next((p for p in ui_document.problems if p.problem_id == user_selection.problem_id), None)
        if not selected_problem:
            raise ValueError(f"Could not find selected problem with ID: {user_selection.problem_id}")

        # Start with the user's potentially edited problem statement.
        final_problem_statement = user_selection.edited_latex

        # If we have stored descriptions for this problem, append them.
        # if selected_problem.referenced_figure_descriptions:
        #     print(f"[DEBUG-3] HANDOFF: Found {len(selected_problem.referenced_figure_descriptions)} descriptions for {selected_problem.problem_id}.")
        #     descriptions_text = "\n\n".join(selected_problem.referenced_figure_descriptions)
        #     final_problem_statement += f"\n\n[Associated Visual Information]:\n{descriptions_text}"
        # # === END KEY LOGIC ===
        
        # The VLM call can now be a secondary, more intelligent step.
        # For now, we pass the text-based context we already have.
        # A full VLM analysis might not even be necessary if the text description is good.
        #visual_context = None 
        # visual_context = self.visual_contextualizer.analyze(...) # You can still run this if you need more than text

        if selected_problem.referenced_figure_descriptions:
            descriptions_text = "\n\n".join(selected_problem.referenced_figure_descriptions)

            # Don't embed in problem statement
            final_problem_statement = user_selection.edited_latex

            # Create proper VisualContext object
            visual_context = VisualContext(
                elements=[],
                summary=descriptions_text,
                contains_essential_info=True
            )
        else:
            final_problem_statement = user_selection.edited_latex
            visual_context = None

        return VisionFinalOutput(
            problem_statement=final_problem_statement,
            visual_context=visual_context,
            source_metadata={
                "problem_id": user_selection.problem_id,
                "processing_method": "marker_then_semantic_grouping",
                "total_available_blocks": len(ui_document.blocks),
                "total_problems_found": len(ui_document.problems),
                "vlm_analysis_performed": visual_context is not None,
                "document_dimensions": ui_document.dimensions
            }
        )


    def process_document(self, file_input: Union[str, Image.Image]):
        if isinstance(file_input, str):
            # File path provided
            return self.marker_service.convert_document(file_input)
        else:
            # PIL Image provided - need to save temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                file_input.save(tmp_file.name)
                try:
                    result = self.marker_service.convert_document(tmp_file.name)
                    return result
                finally:
                    # Clean up temporary file
                    import os
                    try:
                        os.unlink(tmp_file.name)
                    except OSError:
                        pass