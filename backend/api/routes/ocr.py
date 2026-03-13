"""
OCR endpoint – upload an image, get back extracted text.
POST /api/ocr/
"""
import tempfile
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

router = APIRouter()


class OCRResponse(BaseModel):
    text: str
    word_count: int
    confidence: float


@router.post("/", response_model=OCRResponse)
async def extract_text(file: UploadFile = File(...)):
    allowed = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
    suffix = Path(file.filename or "image.png").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported image type: {suffix}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(tmp_path)
            text = pytesseract.image_to_string(img)
            # Try to get confidence data
            try:
                import pandas as pd
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confs = [int(c) for c in data["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0]
                confidence = sum(confs) / len(confs) / 100.0 if confs else 0.5
            except Exception:
                confidence = 0.5
        except ImportError:
            raise HTTPException(
                503,
                "OCR dependencies not installed. Run: pip install pytesseract Pillow"
            )

        text = text.strip()
        return OCRResponse(
            text=text,
            word_count=len(text.split()),
            confidence=round(confidence, 3),
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
