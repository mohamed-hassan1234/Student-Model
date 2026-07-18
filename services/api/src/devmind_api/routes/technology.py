import json
from collections.abc import AsyncIterator
from dataclasses import replace
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from starlette import status

from devmind_api.auth.dependencies import require_permission
from devmind_api.auth.models import Permission
from devmind_api.config import Settings, get_settings
from devmind_api.db import MongoDatabase, get_database
from devmind_api.exceptions import DevMindError
from devmind_api.file_storage import GridFsFileStore
from devmind_api.technology.api_schemas import (
    AskTechnologyStudentRequest,
    AskTechnologyStudentResponse,
    CapabilityStatusResponse,
    CurriculumResponse,
    CurriculumTopicStatus,
    DeactivateSourceRequest,
    IngestionReportResponse,
    IngestionStartRequest,
    RegisterFileSourceRequest,
    RegisterSourceRequest,
    SourceListResponse,
    SourceReviewRequest,
    SourceUpdateRequest,
)
from devmind_api.technology.curriculum import SUPPORTED_TOPICS
from devmind_api.technology.hashing import sha256_hex
from devmind_api.technology.models import ContentType, EvidenceStatus, IngestionStatus, SourceStatus
from devmind_api.technology.repositories import TechnologyRepository
from devmind_api.technology.security import sanitize_filename
from devmind_api.technology.services import (
    SourceRegistration,
    TechnologyServiceError,
    TechnologyStudentService,
)

router = APIRouter(prefix="/technology", tags=["technology-student"])
SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_database)]


def get_service(database: DatabaseDep, settings: SettingsDep) -> TechnologyStudentService:
    return TechnologyStudentService(TechnologyRepository(database), settings)


ServiceDep = Annotated[TechnologyStudentService, Depends(get_service)]
SourceReviewDep = Annotated[Any, Depends(require_permission(Permission.SOURCES_REVIEW))]


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def register_source(
    request: RegisterSourceRequest, service: ServiceDep, principal: SourceReviewDep
) -> Any:
    try:
        registration = replace(
            _source_registration_from_web(request), created_by=principal.user.user_id
        )
        return await service.register_source(registration)
    except TechnologyServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc
    except ValueError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/sources", response_model=SourceListResponse)
async def list_sources(
    database: DatabaseDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    topic: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> SourceListResponse:
    repository = TechnologyRepository(database)
    sources = await repository.list_sources(
        status=status_filter, topic=topic, limit=limit, offset=offset
    )
    return SourceListResponse(sources=sources, limit=limit, offset=offset)


@router.get("/sources/{source_id}")
async def read_source(source_id: str, database: DatabaseDep) -> Any:
    source = await TechnologyRepository(database).get_source(source_id)
    if source is None:
        raise DevMindError("Source not found", status.HTTP_404_NOT_FOUND)
    return source


@router.patch("/sources/{source_id}")
async def update_source(
    source_id: str, request: SourceUpdateRequest, database: DatabaseDep, _: SourceReviewDep
) -> Any:
    updates = request.model_dump(mode="python", exclude_none=True)
    if "license_url" in updates:
        updates["license_url"] = str(updates["license_url"])
    updated = await TechnologyRepository(database).update_source(source_id, updates)
    if updated is None:
        raise DevMindError("Source not found", status.HTTP_404_NOT_FOUND)
    return updated


@router.post("/sources/{source_id}/review")
async def review_source(
    source_id: str, request: SourceReviewRequest, service: ServiceDep, principal: SourceReviewDep
) -> Any:
    try:
        return await service.approve_source(
            source_id, principal.user.user_id, request.approved, request.notes
        )
    except TechnologyServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_404_NOT_FOUND) from exc


@router.post("/sources/{source_id}/deactivate")
async def deactivate_source(
    source_id: str,
    request: DeactivateSourceRequest,
    database: DatabaseDep,
    _: SourceReviewDep,
) -> Any:
    updated = await TechnologyRepository(database).update_source(
        source_id,
        {"source_status": SourceStatus.INACTIVE.value, "deactivation_reason": request.reason},
    )
    if updated is None:
        raise DevMindError("Source not found", status.HTTP_404_NOT_FOUND)
    return updated


@router.get("/sources/{source_id}/history")
async def read_source_history(source_id: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "history": [],
        "limitations": ["Detailed source history UI is reserved for later Phase 1 hardening."],
    }


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_source_file(
    service: ServiceDep,
    database: DatabaseDep,
    principal: SourceReviewDep,
    metadata_json: Annotated[str, Form(alias="metadata")],
    file: Annotated[UploadFile, File()],
) -> Any:
    try:
        metadata = RegisterFileSourceRequest.model_validate(json.loads(metadata_json))
        data = await file.read()
        registration = replace(
            _source_registration_from_file(metadata, file.filename or "upload"),
            created_by=principal.user.user_id,
        )
        source = await service.upload_and_register(
            filename=file.filename or "upload", data=data, registration=registration
        )
        safe_name = sanitize_filename(file.filename or "upload")
        stored = await GridFsFileStore.from_database(database).put(
            safe_name,
            metadata.content_type.value,
            _single_chunk(data),
        )
        await TechnologyRepository(database).record_upload_metadata(
            source_id=source.source_id,
            original_filename=file.filename or "upload",
            sanitized_filename=safe_name,
            mime_type=metadata.content_type.value,
            file_size=len(data),
            checksum=sha256_hex(data),
            gridfs_file_id=stored.file_id,
            permission_metadata={
                "retrieval": metadata.retrieval_use_permission.value,
                "training": metadata.training_use_permission.value,
            },
            license_metadata={
                "license_type": metadata.license_type,
                "license_url": str(metadata.license_url) if metadata.license_url else None,
            },
        )
        return source
    except (json.JSONDecodeError, ValueError, TechnologyServiceError) as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/uploads/{source_id}/status")
async def read_upload_status(source_id: str, database: DatabaseDep) -> Any:
    source = await TechnologyRepository(database).get_source(source_id)
    if source is None:
        raise DevMindError("Source not found", status.HTTP_404_NOT_FOUND)
    return {"source_id": source_id, "parsing_status": source.ingestion_status.value}


@router.get("/uploads/{source_id}/parsing-result")
async def read_parsing_result(source_id: str, database: DatabaseDep) -> Any:
    source = await TechnologyRepository(database).get_source(source_id)
    if source is None:
        raise DevMindError("Source not found", status.HTTP_404_NOT_FOUND)
    return {"source_id": source_id, "ingestion_status": source.ingestion_status.value}


@router.delete("/uploads/{source_id}")
async def deactivate_upload(source_id: str, database: DatabaseDep, _: SourceReviewDep) -> Any:
    updated = await TechnologyRepository(database).update_source(
        source_id,
        {"source_status": SourceStatus.INACTIVE.value, "deactivation_reason": "upload deactivated"},
    )
    if updated is None:
        raise DevMindError("Source not found", status.HTTP_404_NOT_FOUND)
    return updated


@router.post("/ingestion/jobs", response_model=IngestionReportResponse)
async def start_ingestion(
    request: IngestionStartRequest, service: ServiceDep, _: SourceReviewDep
) -> Any:
    try:
        report = await service.ingest_source_url(request.source_id)
    except TechnologyServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc
    return report


@router.get("/ingestion/jobs")
async def list_ingestion_jobs(database: DatabaseDep, limit: int = 50, offset: int = 0) -> Any:
    return {
        "jobs": await TechnologyRepository(database).list_ingestion_jobs(limit=limit, offset=offset)
    }


@router.get("/ingestion/jobs/{job_id}")
async def read_ingestion_job(job_id: str, database: DatabaseDep) -> Any:
    job = await TechnologyRepository(database).get_ingestion_job(job_id)
    if job is None:
        raise DevMindError("Ingestion job not found", status.HTTP_404_NOT_FOUND)
    return job


@router.post("/ingestion/jobs/{job_id}/retry")
async def retry_ingestion_job(job_id: str, database: DatabaseDep, _: SourceReviewDep) -> Any:
    await TechnologyRepository(database).update_ingestion_job(job_id, {"state": "queued"})
    return {"job_id": job_id, "state": "queued"}


@router.post("/ingestion/jobs/{job_id}/cancel")
async def cancel_ingestion_job(job_id: str, database: DatabaseDep, _: SourceReviewDep) -> Any:
    await TechnologyRepository(database).update_ingestion_job(job_id, {"state": "cancelled"})
    return {"job_id": job_id, "state": "cancelled"}


@router.get("/ingestion/events")
async def read_ingestion_events() -> dict[str, list[Any]]:
    return {"events": []}


@router.post("/student/ask", response_model=AskTechnologyStudentResponse)
async def ask_technology_student(request: AskTechnologyStudentRequest, service: ServiceDep) -> Any:
    try:
        return await service.answer_question(request.question, request.limit)
    except TechnologyServiceError as exc:
        raise DevMindError(str(exc), status.HTTP_400_BAD_REQUEST) from exc


@router.get("/student/evidence/{retrieval_event_id}")
async def read_answer_evidence(retrieval_event_id: str) -> dict[str, Any]:
    return {"retrieval_event_id": retrieval_event_id, "evidence": []}


@router.get("/student/retrieval-events/{retrieval_event_id}")
async def read_retrieval_event(retrieval_event_id: str) -> dict[str, Any]:
    return {"retrieval_event_id": retrieval_event_id}


@router.get("/student/curriculum", response_model=CurriculumResponse)
async def read_supported_curriculum() -> CurriculumResponse:
    return CurriculumResponse(
        topics=[CurriculumTopicStatus(topic=topic) for topic in SUPPORTED_TOPICS]
    )


@router.get("/student/capabilities", response_model=CapabilityStatusResponse)
async def read_capability_status() -> CapabilityStatusResponse:
    return CapabilityStatusResponse(
        supported_content_types=list(ContentType),
        evidence_statuses=list(EvidenceStatus),
        source_statuses=list(SourceStatus),
        ingestion_statuses=list(IngestionStatus),
    )


def _source_registration_from_web(request: RegisterSourceRequest) -> SourceRegistration:
    return SourceRegistration(
        name=request.name,
        description=request.description,
        original_reference=str(request.original_url),
        content_type=request.content_type,
        technology_topic=request.technology_topic.value,
        subtopic=request.subtopic,
        trust_level=request.trust_level,
        author_or_organization=request.author_or_organization,
        license_type=request.license_type,
        license_url=str(request.license_url) if request.license_url else None,
        license_review_status=request.license_review_status,
        retrieval_use_permission=request.retrieval_use_permission,
        training_use_permission=request.training_use_permission,
        human_approval_status=request.human_approval_status,
        created_by=request.created_by,
    )


def _source_registration_from_file(
    request: RegisterFileSourceRequest, filename: str
) -> SourceRegistration:
    return SourceRegistration(
        name=request.name,
        description=request.description,
        original_reference=f"file-id://pending/{filename}",
        content_type=request.content_type,
        technology_topic=request.technology_topic.value,
        subtopic=request.subtopic,
        trust_level=request.trust_level,
        author_or_organization=request.author_or_organization,
        license_type=request.license_type,
        license_url=str(request.license_url) if request.license_url else None,
        license_review_status=request.license_review_status,
        retrieval_use_permission=request.retrieval_use_permission,
        training_use_permission=request.training_use_permission,
        human_approval_status=request.human_approval_status,
        created_by=request.created_by,
    )


async def _single_chunk(data: bytes) -> AsyncIterator[bytes]:
    yield data
