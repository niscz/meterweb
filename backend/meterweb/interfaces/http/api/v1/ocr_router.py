from uuid import UUID
from fastapi import APIRouter, Depends, Request

from meterweb.application.dto import OCRDecisionDTO, PhotoReadingCreateDTO
from meterweb.application.use_cases.readings import AddPhotoReadingUseCase, OCRAcceptUseCase, OCRRejectUseCase, OCRRunUseCase
from meterweb.interfaces.http.common import require_auth
from meterweb.interfaces.http.dependencies import (
    get_add_photo_reading_use_case,
    get_ocr_accept_use_case,
    get_ocr_reject_use_case,
    get_ocr_run_use_case,
)
from meterweb.interfaces.http.mappers import to_reading_response
from meterweb.interfaces.http.path_validation import normalize_upload_path
from meterweb.bootstrap import get_container
from meterweb.interfaces.http.schemas import (
    OCRCandidateResponse,
    OCRRunRequest,
    OCRMetadataResponse,
    OCRRunResponse,
    PhotoReadingCreateRequest,
    PhotoReadingResponse,
)

router = APIRouter(tags=["v1-ocr"])


@router.post("/ocr/run", response_model=OCRRunResponse)
def run_ocr(request: Request, payload: OCRRunRequest, use_case: OCRRunUseCase = Depends(get_ocr_run_use_case)):
    require_auth(request)
    image_path = normalize_upload_path(payload.image_path, get_container().settings)
    result = use_case.execute(image_path)
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
    image_path = normalize_upload_path(payload.image_path, get_container().settings)
    reading, ocr_result, plausibility = use_case.execute(
        PhotoReadingCreateDTO(
            meter_register_id=payload.meter_register_id,
            measured_at=payload.measured_at,
            image_path=str(image_path),
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


@router.post("/ocr/{reading_id}/accept", response_model=OCRMetadataResponse)
def accept_ocr(
    request: Request,
    reading_id: UUID,
    use_case: OCRAcceptUseCase = Depends(get_ocr_accept_use_case),
):
    require_auth(request)
    metadata = use_case.execute(OCRDecisionDTO(reading_id=reading_id))
    return OCRMetadataResponse(
        image_path=metadata.image_path,
        ocr_confidence=metadata.ocr_confidence,
        ocr_text=metadata.ocr_text,
        candidates=[OCRCandidateResponse(value=item.value, confidence=item.confidence) for item in metadata.ocr_candidates],
        status=metadata.ocr_status,
    )


@router.post("/ocr/{reading_id}/reject", response_model=OCRMetadataResponse)
def reject_ocr(
    request: Request,
    reading_id: UUID,
    use_case: OCRRejectUseCase = Depends(get_ocr_reject_use_case),
):
    require_auth(request)
    metadata = use_case.execute(OCRDecisionDTO(reading_id=reading_id))
    return OCRMetadataResponse(
        image_path=metadata.image_path,
        ocr_confidence=metadata.ocr_confidence,
        ocr_text=metadata.ocr_text,
        candidates=[OCRCandidateResponse(value=item.value, confidence=item.confidence) for item in metadata.ocr_candidates],
        status=metadata.ocr_status,
    )
