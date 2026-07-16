import pytest

from devmind_api.technology.models import PermissionStatus
from devmind_api.technology.policy import SourcePolicyError, validate_source_registration
from devmind_api.technology.security import (
    SecurityValidationError,
    infer_content_type_from_filename,
    validate_http_url,
)


def test_source_policy_allows_approved_curriculum_topic() -> None:
    domain = validate_source_registration(
        original_reference="https://developer.mozilla.org/en-US/docs/Web/HTML",
        technology_topic="html",
        license_type="cc-by-sa",
        retrieval_use_permission=PermissionStatus.ALLOWED,
        training_use_permission=PermissionStatus.DISALLOWED,
    )

    assert domain == "developer.mozilla.org"


def test_source_policy_rejects_unknown_topic() -> None:
    with pytest.raises(SourcePolicyError):
        validate_source_registration(
            original_reference="https://example.com/ml",
            technology_topic="machine_learning",
            license_type="mit",
            retrieval_use_permission=PermissionStatus.ALLOWED,
            training_use_permission=PermissionStatus.DISALLOWED,
        )


def test_url_validation_blocks_ssrf_targets() -> None:
    for url in ("http://127.0.0.1/page", "http://169.254.169.254/latest", "file:///tmp/a"):
        with pytest.raises(SecurityValidationError):
            validate_http_url(url)


def test_file_validation_rejects_executable_extension() -> None:
    with pytest.raises(SecurityValidationError):
        infer_content_type_from_filename("lesson.exe")
