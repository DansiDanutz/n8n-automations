"""Database models."""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .db import Base


class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
