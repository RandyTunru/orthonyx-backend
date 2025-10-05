from sqlalchemy import Column, Text, Boolean, TIMESTAMP, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy import text
from app.models.base import Base
import enum 

class StatusEnum(str, enum.Enum):
    not_completed = "not_completed"
    completed = "completed"


class OCRSymptom(Base):
    __tablename__ = "ocr_symptoms"

    # Identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Symptom Details
    input = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))   

    # Analysis
    analysis = Column(Text, nullable=True)

    # Timestamps and Status
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())    
    status = Column(ENUM(StatusEnum, name="status_enum", create_type=False), nullable=False, server_default=text("'not_completed'::status_enum"))
    meta = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))