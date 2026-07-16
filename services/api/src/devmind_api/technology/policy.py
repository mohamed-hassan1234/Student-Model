from urllib.parse import urlparse

from devmind_api.technology.curriculum import TechnologyTopic
from devmind_api.technology.models import (
    PermissionStatus,
    RegisteredSource,
    ReviewStatus,
    SourceStatus,
)
from devmind_api.technology.security import SecurityValidationError, validate_http_url


class SourcePolicyError(ValueError):
    pass


ALLOWED_LICENSE_TYPES = {
    "official-docs",
    "mit",
    "apache-2.0",
    "bsd",
    "cc-by",
    "cc-by-sa",
    "public-domain",
    "user-owned",
}


def validate_source_registration(
    *,
    original_reference: str,
    technology_topic: str,
    license_type: str,
    retrieval_use_permission: PermissionStatus,
    training_use_permission: PermissionStatus,
) -> str:
    if technology_topic not in {topic.value for topic in TechnologyTopic}:
        raise SourcePolicyError("Technology topic is outside the Phase 1 curriculum")
    if license_type.lower() not in ALLOWED_LICENSE_TYPES:
        raise SourcePolicyError("License type is not in the Phase 1 allowlist")
    if retrieval_use_permission is not PermissionStatus.ALLOWED:
        raise SourcePolicyError("Retrieval permission must be allowed before ingestion")
    if training_use_permission is PermissionStatus.UNKNOWN:
        raise SourcePolicyError("Training permission must be explicitly allowed or disallowed")
    if original_reference.startswith(("http://", "https://")):
        return validate_http_url(original_reference).domain
    parsed = urlparse(original_reference)
    if parsed.scheme and parsed.scheme not in {"file-id"}:
        raise SourcePolicyError("Unsupported source reference scheme")
    return "uploaded-file"


def can_ingest_source(source: RegisteredSource) -> bool:
    return (
        source.source_status in {SourceStatus.APPROVED, SourceStatus.ACTIVE}
        and source.license_review_status is ReviewStatus.APPROVED
        and source.human_approval_status is ReviewStatus.APPROVED
        and source.retrieval_use_permission is PermissionStatus.ALLOWED
    )


def assert_can_ingest_source(source: RegisteredSource) -> None:
    if not can_ingest_source(source):
        raise SourcePolicyError("Source policy state does not permit ingestion")


def assert_domain_allowed(source: RegisteredSource) -> None:
    if source.original_reference.startswith(("http://", "https://")):
        try:
            safe_url = validate_http_url(source.original_reference)
        except SecurityValidationError as exc:
            raise SourcePolicyError(str(exc)) from exc
        if safe_url.domain != source.source_domain:
            raise SourcePolicyError("Registered source domain does not match URL")
