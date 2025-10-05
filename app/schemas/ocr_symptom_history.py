from app.schemas.ocr_symptom_check import OCRSymptomCheckOut
from pydantic import BaseModel 
from typing import Optional, List

class OCRSymptomHistoryOut(BaseModel):
    user_id: str
    history: List[OCRSymptomCheckOut]