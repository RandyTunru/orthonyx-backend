from sqlalchemy import Column, Text, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import text
from sqlalchemy.orm import declarative_base

import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    # User Data
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    email = Column(Text, nullable=False, index=True, unique=True)
    username = Column(Text, nullable=False, index=True, unique=True)
    password_hash = Column(Text, nullable=False)

    # API Key Data
    api_key_enc = Column(Text, nullable=False)  
    api_key_created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    api_key_expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    api_key_revoked = Column(Boolean, nullable=False, server_default="false")

    # Status and Metadata
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)
    meta = Column(JSONB, server_default=text("'{}'::jsonb"))
