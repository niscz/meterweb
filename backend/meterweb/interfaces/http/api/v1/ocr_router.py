from pathlib import Path

from fastapi import APIRouter, Depends, Request

from meterweb.application.dto import PhotoReadingCreateDTO
from meterweb.application.use_cases.readings import AddPhotoReadingUseCase, OCRRunUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import get_add_photo_reading_use_case, get_ocr_run_use_case
from meterweb.interfaces.http.mappers import to_reading_response
from meterweb.interfaces.http.schemas import (
    OCRCandidateResponse,
    OCRRunRequest,
    OCRRunResponse,
    PhotoReadingCreateRequest,
    PhotoReadingResponse,
)

router = APIRouter(tags=["v1-ocr"])


@router.post("/ocr/run", response_model=OCRRunResponse)
def run_ocr(request: Request, payload: OCRRunRequest, use_case: OCRRunUseCase = Depends(get_ocr_run_use_case)):
    require_auth(request)
    result = use_case.execute(Path(payload.image_path))
    return OCRRunResponse(
        text=result.text,
        candidates=[OCRCandidateResponse(value=item.value, confidence=item.confidence) for item in result.candidates],
        best_candidate=(
            OCRCandidateResponse(value=result.best_candidate.value, confidence=result.best_candidate.confidence)
            if result.best_candidate
            else None
        ),
    )


@router.post("/ocr/readings", response_model=PhotoReadingResponse)
def create_photo_reading(
    request: Request,
    payload: PhotoReadingCreateRequest,
    use_case: AddPhotoReadingUseCase = Depends(get_add_photo_reading_use_case),
):
    require_auth(request)
    reading, ocr_result, plausibility = use_case.execute(
        PhotoReadingCreateDTO(
            meter_register_id=payload.meter_register_id,
            measured_at=payload.measured_at,
            image_path=payload.image_path,
        ),
        confirmed_value=payload.confirmed_value,
    )
    return PhotoReadingResponse(
        reading=to_reading_response(reading),
        ocr_result=OCRRunResponse(
            text=ocr_result.text,
            candidates=[OCRCandidateResponse(value=item.value, confidence=item.confidence) for item in ocr_result.candidates],
            best_candidate=(
                OCRCandidateResponse(value=ocr_result.best_candidate.value, confidence=ocr_result.best_candidate.confidence)
                if ocr_result.best_candidate
                else None
            ),
        ),
        plausibility_warning=plausibility.warning,
    )
