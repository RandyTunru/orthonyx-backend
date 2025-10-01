from sqlalchemy import Column, Text, Boolean, TIMESTAMP, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy import text
from app.models.base import Base
import enum 

class SexEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class StatusEnum(str, enum.Enum):
    in_review = "in_review"
    completed = "completed"


class Symptom(Base):
    __tablename__ = "symptoms"

    # Identifiers
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Symptom Details
    age = Column(Integer, nullable=False)
    sex = Column(ENUM(SexEnum, name="sex_enum", create_type=False), nullable=False)
    symptoms = Column(Text, nullable=False)
    duration = Column(Text, nullable=False)
    severity = Column(Integer, nullable=False)
    additional_notes = Column(Text, nullable=True)     

    # Analysis
    analysis = Column(Text, nullable=True)

    # Timestamps and Status
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())    
    status = Column(ENUM(StatusEnum, name="status_enum", create_type=False), nullable=False, server_default=text("'in_review'::status_enum"))
    meta = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))