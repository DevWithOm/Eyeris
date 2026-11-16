from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base

class ScreeningRecord(Base):
    __tablename__ = "screening_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    patient_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)
    
    # Image Quality Assessment
    is_gradable: Mapped[bool | None] = mapped_column(Boolean, default=True, nullable=True)
    overall_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Classification & Grading
    predicted_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    # Confidence & Uncertainty
    calibrated_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Clinical Decision & Escalation
    referable: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
