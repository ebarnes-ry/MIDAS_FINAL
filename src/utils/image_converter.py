from __future__ import annotations
from pathlib import Path
from typing import Union
import base64
import io
from PIL import Image


def to_base64(image_data: Union[str, Path, bytes, Image.Image]) -> str:
    if isinstance(image_data, (str, Path)):
        path = Path(image_data)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {image_data}")
        
        with Image.open(path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
    elif isinstance(image_data, bytes):
        return base64.b64encode(image_data).decode('utf-8')
        
    elif isinstance(image_data, Image.Image):
        if image_data.mode in ('RGBA', 'P'):
            image_data = image_data.convert('RGB')
        
        buffer = io.BytesIO()
        image_data.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    else:
        raise ValueError(f"Unsupported image data type: {type(image_data)}")