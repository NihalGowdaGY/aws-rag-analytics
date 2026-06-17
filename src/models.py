from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from datetime import datetime, timezone
from src.database import Base

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String, nullable=False)
    generated_response = Column(String, nullable=False)
    context_found = Column(Boolean, default=True, index=True)
    latency_seconds = Column(Float, nullable=False)
    
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)