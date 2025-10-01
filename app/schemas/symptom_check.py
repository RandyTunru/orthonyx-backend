from pydantic import BaseModel
from typing import Optional, Dict, Union
from datetime import datetime

# Symptom check endpoint input schema
class SymptomCheckIn(BaseModel):
    age: int 
    sex: str
    symptoms: str
    duration: str
    severity: int
    additional_notes: Optional[str] = None


# Symptom check endpoint output schemas
class SymptomInput(BaseModel): # Input details nested within the output schema
    age: int
    sex: str
    symptoms: str
    duration: str
    severity: int
    additional_notes: Optional[str] = None

class SymptomCheckOut(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    input: SymptomInput 
    analysis: str
    status: str