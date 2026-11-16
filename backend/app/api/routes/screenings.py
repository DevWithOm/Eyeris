from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.explanation import ExplanationDetailResponse
from backend.app.schemas.screening import (
    ScreeningDetailResponse,
    ScreeningReportResponse,
    ScreeningResponse,
)
from backend.app.services.explanation_service import get_explanation_for_case
from backend.app.services.report_service import get_report_for_case
from backend.app.services.screening_service import (
    get_screening_by_case_id,
    process_screening_upload,
)

router = APIRouter(prefix="/screenings", tags=["screenings"])

@router.post("", response_model=ScreeningResponse, status_code=status.HTTP_201_CREATED)
async def submit_screening(
    file: UploadFile = File(..., description="Retinal fundus image (JPEG or PNG)"),
    db: Session = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File provided must be an image (JPEG or PNG).",
        )

    try:
        return process_screening_upload(file=file, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening processing failed: {e}",
        )

@router.get("/{case_id}", response_model=ScreeningDetailResponse)
def get_screening(case_id: str, db: Session = Depends(get_db)):
    record = get_screening_by_case_id(case_id=case_id, db=db)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening case '{case_id}' not found.",
        )
    return record

@router.get("/{case_id}/report", response_model=ScreeningReportResponse)
def get_screening_report(case_id: str, db: Session = Depends(get_db)):
    report = get_report_for_case(case_id=case_id, db=db)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screening report for case '{case_id}' not found.",
        )
    return report

@router.get("/{case_id}/explanation", response_model=ExplanationDetailResponse)
def get_screening_explanation(case_id: str, db: Session = Depends(get_db)):
    explanation = get_explanation_for_case(case_id=case_id, db=db)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Explanation for case '{case_id}' not found.",
        )
    return explanation
