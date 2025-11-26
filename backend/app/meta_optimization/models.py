# backend/app/meta_optimization/models.py
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4
from app.models.database import Base

class OptimizationActionModel(Base):
    __tablename__ = "optimization_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    campaign_id = Column(String(36), nullable=True, index=True)
    ad_id = Column(String(36), nullable=True, index=True)
    type = Column(String(50), nullable=False)
    params = Column(JSON, nullable=True)
    status = Column(String(30), nullable=False, default="suggested")
    created_by = Column(String(100), nullable=False, default="optimizer")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
