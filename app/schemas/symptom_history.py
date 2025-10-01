from app.schemas.symptom_check import SymptomCheckOut, SymptomInput
from pydantic import BaseModel 
from typing import Optional, List

class SymptomHistoryOut(BaseModel):
    user_id: str
    history: List[SymptomCheckOut]