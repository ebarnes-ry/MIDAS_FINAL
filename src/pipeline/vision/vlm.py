from typing import Optional
from PIL import Image
import json
from pydantic import ValidationError

from src.models.manager import ModelManager
from .types import UserSelection, UIDocument, VisualContext

class VisualContextualizer:
    def __init__(self, model_manager: ModelManager, vision_task: str = "vision"):
        self.model_manager = model_manager
        self.vision_task = vision_task

    def analyze(self, user_selection: UserSelection, ui_document: UIDocument, source_image: Image.Image) -> Optional[VisualContext]:
        if not self.should_analyze_visually(ui_document):
            return None
        return self._analyze_with_context(user_selection, ui_document, source_image)

    def should_analyze_visually(self, ui_document: UIDocument) -> bool:
        visual_block_types = {"figure", "picture", "code", "table", "figuregroup", "picturegroup", "tablegroup"}
        for block in ui_document.blocks:
            if block.block_type.lower() in visual_block_types:
                if not block._has_mathematical_content():
                    return True
        return False

    def _analyze_with_context(self, user_selection: UserSelection, ui_document: UIDocument, source_image: Image.Image) -> Optional[VisualContext]:
        print(f"--- Starting VLM analysis with task: {self.vision_task} ---")
        
        # Initial VLM call
        response = self.model_manager.call(
            task=self.vision_task,
            prompt_ref="vision/analyze@v1",
            variables={"problem_text": user_selection.edited_latex},
            schema=VisualContext,
            images=[source_image]
        )
        
        if response.parsed:
            print("✓ VLM response parsed successfully on the first attempt.")
            return response.parsed

        # If parsing failed, attempt to repair the JSON
        if "validation_error" in response.meta:
            print("VLM response failed schema validation. Attempting JSON repair...")
            
            repair_response = self.model_manager.call(
                task="json_repair",
                prompt_ref="vision/repair_json@v1",
                variables={
                    "validation_error": response.meta["validation_error"],
                    "broken_json": response.content
                }
            )
            try:
                # Attempt to parse the repaired JSON
                repaired_json = json.loads(repair_response.content)
                parsed_context = VisualContext.model_validate(repaired_json)
                print("JSON repair successful.")
                return parsed_context
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"JSON repair failed. Could not parse the repaired output: {e}")
                return None
        
        print("VLM analysis failed to produce a valid, parsable output.")
        return None