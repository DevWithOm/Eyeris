import os
import shutil
import time
import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.exceptions import ScreeningError
from backend.app.db.models import ScreeningRecord
from backend.app.schemas.screening import (
    ScreeningDetailResponse,
    ScreeningResponse,
    ScreeningStatus,
)
from integration.pipeline import analyse_case

def process_screening_upload(file: UploadFile, db: Session) -> ScreeningResponse:
    start_time = time.time()
    case_id = f"EYE-{uuid.uuid4().hex[:8].upper()}"

    # 1. Prepare storage directory
    case_dir = Path(settings.storage_root) / "cases" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    saved_image_path = case_dir / f"fundus_input{file_ext}"

    with open(saved_image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if saved_image_path.stat().st_size > max_bytes:
        saved_image_path.unlink(missing_ok=True)
        raise ScreeningError(f"Uploaded file exceeds maximum allowed limit of {settings.max_upload_mb} MB.")

    # 2. Run Integration Pipeline Orchestration
    try:
        pipeline_output = analyse_case(str(saved_image_path), config={"case_id": case_id})
    except Exception as e:
        raise ScreeningError(f"Pipeline orchestration error: {e}") from e

    execution_time_ms = int((time.time() - start_time) * 1000)

    # 3. Extract Fields
    status = pipeline_output.get("status", "completed")
    quality = pipeline_output.get("quality", {})
    classification = pipeline_output.get("classification") or {}
    explainability = pipeline_output.get("explainability") or {}
    decision = pipeline_output.get("clinical_decision", {})

    # 4. Persist to Database
    db_record = ScreeningRecord(
        case_id=case_id,
        image_path=str(saved_image_path),
        status=status,
        is_gradable=quality.get("is_gradable", True),
        overall_quality_score=quality.get("overall_quality_score"),
        predicted_grade=classification.get("predicted_grade"),
        grade_name=classification.get("grade_name"),
        calibrated_confidence=explainability.get("calibrated_confidence"),
        uncertainty_score=explainability.get("uncertainty_score"),
        referable=decision.get("referral_recommended"),
        urgency=decision.get("urgency"),
        rationale=decision.get("rationale"),
        action_required=decision.get("action_required"),
        model_version=classification.get("model_version"),
        execution_time_ms=execution_time_ms,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # 5. Return Validated Pydantic Schema
    return ScreeningResponse.model_validate(pipeline_output)

def get_screening_by_case_id(case_id: str, db: Session) -> ScreeningDetailResponse | None:
    record = db.query(ScreeningRecord).filter(ScreeningRecord.case_id == case_id).first()
    if not record:
        return None
    return ScreeningDetailResponse(
        case_id=record.case_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        status=record.status,
        image_url=f"/storage/cases/{record.case_id}/fundus_input.jpg",
        quality_gradable=record.is_gradable,
        overall_quality_score=record.overall_quality_score,
        predicted_grade=record.predicted_grade,
        grade_name=record.grade_name,
        calibrated_confidence=record.calibrated_confidence,
        uncertainty_score=record.uncertainty_score,
        referable=record.referable,
        urgency=record.urgency,
        rationale=record.rationale,
        action_required=record.action_required,
        model_version=record.model_version,
        execution_time_ms=record.execution_time_ms,
    )

def list_all_screenings(db: Session, limit: int = 50, offset: int = 0) -> list[ScreeningDetailResponse]:
    records = (
        db.query(ScreeningRecord)
        .order_by(ScreeningRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        ScreeningDetailResponse(
            case_id=r.case_id,
            created_at=r.created_at,
            updated_at=r.updated_at,
            status=r.status,
            image_url=f"/storage/cases/{r.case_id}/fundus_input.jpg",
            quality_gradable=r.is_gradable,
            overall_quality_score=r.overall_quality_score,
            predicted_grade=r.predicted_grade,
            grade_name=r.grade_name,
            calibrated_confidence=r.calibrated_confidence,
            uncertainty_score=r.uncertainty_score,
            referable=r.referable,
            urgency=r.urgency,
            rationale=r.rationale,
            action_required=r.action_required,
            model_version=r.model_version,
            execution_time_ms=r.execution_time_ms,
        )
        for r in records
    ]
    record = db.query(ScreeningRecord).filter(ScreeningRecord.case_id == case_id).first()
    if not record:
        return None
    return ScreeningDetailResponse(
        case_id=record.case_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        status=record.status,
        image_url=f"/storage/cases/{record.case_id}/fundus_input.jpg",
        quality_gradable=record.is_gradable,
        overall_quality_score=record.overall_quality_score,
        predicted_grade=record.predicted_grade,
        grade_name=record.grade_name,
        calibrated_confidence=record.calibrated_confidence,
        uncertainty_score=record.uncertainty_score,
        referable=record.referable,
        urgency=record.urgency,
        rationale=record.rationale,
        action_required=record.action_required,
        model_version=record.model_version,
        execution_time_ms=record.execution_time_ms,
    )
