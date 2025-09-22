from PIL import Image
from typing import List, Any

from .types import OCRResult, OCRTextLine, OCRChar
from src.models.manager import ModelManager

class ocr:
    def __init__(self, manager: ModelManager):
        self.manager = manager
        self.model = manager.get_provider_for_task("ocr")

    async def ocr_image_content(self, image: Image.Image) -> OCRResult:
        raw_result = await self.model.generate_raw_ocr(image)
        
        #convert to result text lines
        lines = self.convert_to_lines(raw_result)

        #format full latex text from the lines
        latex_text = self.format_latex(lines)

        #extract and structure the math content (i.e. equations/expressions/symbols) from the latex text
        math_content = self.extract_math_content(latex_text)

        return OCRResult(
            latex=latex_text, 
            lines=lines, 
            equations=math_content, 
            model_info={"model": self.model.model_name, "provider": self.model.provider_name})

    def convert_to_lines(self, raw_result: Any) -> List[OCRTextLine]:
        lines: List[OCRTextLine] = []
        for tl in raw_result.text_lines:
            chars = [
                OCRChar(
                    text=char.text, 
                    confidence=char.confidence, 
                    bbox=char.bbox, 
                    bbox_valid=char.bbox_valid
                    ) for char in tl.chars
                ]
            lines.append(
                OCRTextLine(
                    text=tl.text, 
                    polygon=tl.polygon, 
                    confidence=tl.confidence, 
                    chars=chars
                ))
        return lines

    def format_latex(self, lines: List[OCRTextLine]) -> str:
        #TODO: make this better if needed
        return "\n".join(line.text for line in lines)

    def extract_math_content(self, text: str) -> List[str]:
        pass


