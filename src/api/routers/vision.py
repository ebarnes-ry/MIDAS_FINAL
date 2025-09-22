"""
Vision pipeline API endpoints.
"""
import base64
import io
import time
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Path
from PIL import Image
from bs4 import BeautifulSoup
from typing import Optional

from ..models.vision import (
    DocumentUploadResponse, DocumentUploadData,
    UserSelectionRequest, VisionAnalysisResponse, VisionAnalysisData,
    APIDocument, APIBlock, APIProblem
)
from src.pipeline.vision.types import VisionInput, UserSelection, UIBlock, UIDocument, MathValidationResult, Problem
# Make sure all necessary models and types are imported
from ..models.reasoning import ReasoningExplainRequest, ReasoningExplainResponse, ReasoningExplainData
from ..dependencies.session import get_session_manager, get_model_manager, SessionManager
from src.models.manager import ModelManager
from src.pipeline.vision.vision import VisionPipeline
from src.pipeline.reasoning.reasoning import ReasoningPipeline
from src.pipeline.reasoning.types import ReasoningInput, ReasoningOutput
from src.pipeline.verification.verification_orchestrator import VerificationOrchestrator

router = APIRouter()

# The helper functions (convert_ui_block_to_api_block, etc.) remain the same
def convert_ui_block_to_api_block(ui_block: UIBlock) -> APIBlock:
    # ... (implementation from previous step)
    polygon_flat = []
    if ui_block.polygon:
        if isinstance(ui_block.polygon[0], (list, tuple)):
            for point in ui_block.polygon:
                polygon_flat.extend([float(point[0]), float(point[1])])
        else:
            polygon_flat = [float(p) for p in ui_block.polygon]
    cropped_image = ui_block.images.get('cropped') if ui_block.images else None
    image_description = None
    if ui_block.html:
        soup = BeautifulSoup(ui_block.html, 'html.parser')
        img_desc_tag = soup.find('p', attrs={'role': 'img'})
        if img_desc_tag:
            desc_text = img_desc_tag.get_text(strip=True)
            if desc_text.lower().startswith('image description:'):
                image_description = desc_text[18:].strip()
            else:
                image_description = desc_text
    return APIBlock(id=ui_block.id, block_type=ui_block.block_type, html=ui_block.html, polygon=polygon_flat, bbox=ui_block.bbox, is_editable=ui_block.is_editable, latex_content=ui_block.latex_content, cropped_image=cropped_image, image_description=image_description)


def _extract_and_crop_image_region(block: UIBlock, original_image: Image.Image) -> Optional[str]:
    """
    Extracts the image region for a given block from the original document image.
    This logic now lives here, in the router, where it belongs.
    """
    if not original_image or not block.polygon:
        return None

    try:
        # Handle nested polygon format from Marker
        if block.polygon and isinstance(block.polygon[0], (list, tuple)):
            flat_polygon = [coord for point in block.polygon for coord in point]
        else:
            flat_polygon = block.polygon
        
        if len(flat_polygon) < 8: return None

        x_coords = flat_polygon[0::2]
        y_coords = flat_polygon[1::2]
        
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)
        
        img_width, img_height = original_image.size
        bounds = (
            max(0, int(x_min)),
            max(0, int(y_min)),
            min(img_width, int(x_max)),
            min(img_height, int(y_max))
        )
        
        if bounds[2] > bounds[0] and bounds[3] > bounds[1]:
            cropped_image = original_image.crop(bounds)
            
            buffer = io.BytesIO()
            cropped_image.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
    except Exception as e:
        print(f"Error extracting image region for block {block.id}: {e}")
    
    return None


def convert_ui_block_to_api_block(ui_block: UIBlock, original_image: Image.Image) -> APIBlock:
    """
    Converts internal UIBlock to the APIBlock model sent to the frontend.
    Now includes the logic to attach a cropped image.
    """
    cropped_b64 = None
    # print("\n\n\n\n\n\n\n\n\n\n\n\n")
    # print(ui_block.latex_content)
    # Crop the image only if it's a real figure (has a description) or is misclassified but not editable.
    if ui_block.block_type.lower() in {'figure', 'picture', 'table', 'diagram'} and not ui_block.is_editable:
        cropped_b64 = _extract_and_crop_image_region(ui_block, original_image)

    return APIBlock(
        id=ui_block.id,
        block_type=ui_block.block_type,
        html=ui_block.html,
        polygon=ui_block.polygon,
        bbox=ui_block.bbox,
        is_editable=ui_block.is_editable,
        latex_content=ui_block.latex_content,
        image_description=ui_block.image_description,
        cropped_image=cropped_b64 # <-- ATTACH THE CROPPED IMAGE HERE
    )


def convert_ui_document_to_api_document(ui_document: UIDocument, original_image: Image.Image) -> APIDocument:
    # Pass the original image to the block converter 
    api_blocks = [convert_ui_block_to_api_block(block, original_image) for block in ui_document.blocks]
    
    api_problems = [
        APIProblem(
            problem_id=p.problem_id,
            problem_text=p.problem_text,
            block_ids=p.block_ids
        ) for p in ui_document.problems
    ]

    return APIDocument(
        blocks=api_blocks,
        problems=api_problems,
        # The following fields are not on the new APIDocument, which is correct
        # total_blocks=len(ui_document.blocks),
        # editable_blocks=sum(1 for b in ui_document.blocks if b.is_editable),
        # images=ui_document.images,
        # dimensions=ui_document.dimensions,
        # metadata=ui_document.metadata
    )


def image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), session_manager: SessionManager = Depends(get_session_manager), model_manager: ModelManager = Depends(get_model_manager)):
    start_time = time.time()
    if not file.content_type or not any(file.content_type.startswith(p) for p in ["application/pdf", "image/"]):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}.")
    try:
        file_content = await file.read()
        original_image = Image.open(io.BytesIO(file_content)).convert("RGB")
        print("--- Validating image content ---")
        validation_response = model_manager.call(task="validation", prompt_ref="vision/validate@v1", variables={}, schema=MathValidationResult, images=[original_image])
        if not validation_response.parsed or not validation_response.parsed.contains_math:
            reason = validation_response.parsed.reason if validation_response.parsed else "Could not determine content."
            raise HTTPException(status_code=400, detail=f"Validation Failed: {reason}")
        print(f"Content validated: {validation_response.parsed.reason}")
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_filepath = tmp_file.name
        try:
            vision_pipeline = VisionPipeline(model_manager)
            vision_input = VisionInput(file_path=tmp_filepath, file_type=file.content_type)
            ui_document = vision_pipeline.process_input(vision_input)
            
            original_image_base64 = image_to_base64(original_image)
            processing_time = time.time() - start_time
            
            # === MODIFIED LOGIC: PASS ORIGINAL IMAGE TO CONVERTER ===
            api_document = convert_ui_document_to_api_document(ui_document, original_image)
            
            processing_metadata = { "filename": file.filename, "processing_time": processing_time }
            document_id = session_manager.create_session(
                ui_document=ui_document, 
                original_image_base64=original_image_base64, 
                processing_metadata=processing_metadata
            )
            
            return DocumentUploadResponse(
                success=True, message="Document processed successfully",
                data=DocumentUploadData(
                    document_id=document_id, 
                    document=api_document, 
                    original_image_base64=original_image_base64, 
                    processing_time=processing_time, 
                    processing_metadata=processing_metadata
                )
            )
        finally:
            os.unlink(tmp_filepath)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete")
async def complete_pipeline(request: UserSelectionRequest, session_manager: SessionManager = Depends(get_session_manager), model_manager: ModelManager = Depends(get_model_manager)):
    full_start_time = time.time()
    session = session_manager.get_session(request.document_id)
    if not session:
        raise HTTPException(status_code=404, detail="Document not found or session expired")

    try:
        vision_start_time = time.time()
        user_selection = UserSelection(
            problem_id=request.problem_id,
            edited_latex=request.edited_latex,
            original_image_path=""
        )
        image_data = base64.b64decode(session.original_image_base64)
        source_image = Image.open(io.BytesIO(image_data))
        vision_pipeline = VisionPipeline(model_manager)
        vision_output = vision_pipeline.process_selection(user_selection, session.ui_document, source_image)
        vision_time = time.time() - vision_start_time
        reasoning_start_time = time.time()
        reasoning_pipeline = ReasoningPipeline(model_manager)
        reasoning_input = ReasoningInput(problem_statement=vision_output.problem_statement, visual_context=vision_output.visual_context.summary if vision_output.visual_context else None, source_metadata=vision_output.source_metadata)
        reasoning_output = reasoning_pipeline.process(reasoning_input)
        reasoning_time = time.time() - reasoning_start_time
        verification_start_time = time.time()
        verification_orchestrator = VerificationOrchestrator(model_manager)
        verification_result, repair_history = verification_orchestrator.verify_with_repair(
            reasoning_output=reasoning_output,
            max_reasoning_attempts=2
        )
        verification_time = time.time() - verification_start_time
        total_processing_time = time.time() - full_start_time
        response_data = {
            "vision": {"problem_statement": vision_output.problem_statement, "visual_context": vision_output.visual_context, "processing_time": vision_time, "metadata": vision_output.source_metadata},
            "reasoning": {"original_problem": reasoning_output.original_problem, "worked_solution": reasoning_output.worked_solution, "final_answer": reasoning_output.final_answer, "think_reasoning": reasoning_output.think_reasoning, "processing_time": reasoning_time, "metadata": reasoning_output.processing_metadata},
            "verification": {
                "original_problem": verification_result.reasoning_output.original_problem,
                "worked_solution": verification_result.reasoning_output.worked_solution,
                "final_answer": verification_result.reasoning_output.final_answer,
                "generated_code": verification_result.generated_code,
                "processing_time": verification_time,
                "status": verification_result.status,
                "confidence_score": verification_result.confidence_score,
                "answer_match": verification_result.answer_match,
                "errors": [err.model_dump() for err in verification_result.errors],
                "repair_history": [
                    {
                        "attempt": repair.attempt_number,
                        "type": repair.repair_type,
                        "reason": repair.reason,
                        "success": repair.success,
                        "processing_time": repair.processing_time,
                        "error_message": repair.error_message
                    }
                    for repair in repair_history
                ],
                "metadata": {
                    "reasoning_repair_attempts": len([r for r in repair_history if r.repair_type == "reasoning"]),
                    "codegen_repair_attempts": len([r for r in repair_history if r.repair_type == "codegen"])
                }
            },
            "total_processing_time": total_processing_time
        }
        return {"success": True, "message": "Complete pipeline processing successful", "data": response_data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Complete pipeline failed: {str(e)}")

# The /explain endpoint remains the same
@router.post("/explain", response_model=ReasoningExplainResponse)
async def explain_step(request: ReasoningExplainRequest, model_manager: ModelManager = Depends(get_model_manager)):
    start_time = time.time()
    try:
        response = model_manager.call(
            task="explain_step",
            prompt_ref="reasoning/explain_step@v1",
            variables={"problem_statement": request.problem_statement, "worked_solution": request.worked_solution, "step_text": request.step_text}
        )
        processing_time = time.time() - start_time
        return ReasoningExplainResponse(
            success=True,
            message="Explanation generated successfully.",
            data=ReasoningExplainData(explanation=response.content, processing_time=processing_time)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {e}")