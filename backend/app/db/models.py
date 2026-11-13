from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.session import Base
class ScreeningRecord(Base):
    __tablename__ = "screening_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
