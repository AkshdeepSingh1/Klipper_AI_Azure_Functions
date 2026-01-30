from sqlalchemy import Column, BigInteger, TIMESTAMP, func
from shared.core.database import Base


class ProcessingJob(Base):
    """Processing Job model"""
    __tablename__ = "processing_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<ProcessingJob(id={self.id})>"
