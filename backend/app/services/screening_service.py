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
