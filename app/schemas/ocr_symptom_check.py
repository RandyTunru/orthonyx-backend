from pydantic import BaseModel
from typing import Dict, Union
from datetime import datetime

class OCRSymptomCheckIn(BaseModel):
    age: int # Standard User Information
    sex: str 
    identified_data: Dict[str, Union[int, float, str]]  # generic dictionary for flexibility

    model_config = {
        "json_schema_extra": {
            "example":{
                "age": 34,
                "sex": "female",
                "identified_data": {
                    "chief_complaint": "Persistent cough and fatigue",
                    "onset_duration": "Approximately 5 days",
                    "blood_pressure": "118/76 mmHg",
                    "heart_rate_bpm": 82,
                    "temperature_f": "99.1",
                    "physician_notes": "Lungs clear on auscultation. Mild pharyngeal erythema. Patient reports no difficulty breathing.",
                    "wbc_count": 11500
                    # Additional key-value pairs can be added here
                }
            }
        }
    }

class OCRSymptomCheckOut(BaseModel):
    id: str
    user_id: str
    timestamp: datetime
    input: Dict[str, Union[int, float, str]]  
    analysis: str
    status: str

