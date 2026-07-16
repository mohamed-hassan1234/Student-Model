import ipaddress
import re
from dataclasses import dataclass
from pathlib import PurePath
from urllib.parse import urlparse

from devmind_api.technology.models import ContentType


class SecurityValidationError(ValueError):
    pass


SUPPORTED_EXTENSIONS: dict[str, ContentType] = {
    ".html": ContentType.HTML,
    ".htm": ContentType.HTML,
    ".pdf": ContentType.PDF,
    ".md": ContentType.MARKDOWN,
    ".markdown": ContentType.MARKDOWN,
    ".txt": ContentType.TEXT,
}

EXECUTABLE_EXTENSIONS = {
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".ps1",
    ".sh",
    ".js",
    ".mjs",
    ".jar",
    ".msi",
    ".scr",
}


@dataclass(frozen=True)
class SafeUrl:
    url: str
    domain: str


def validate_http_url(url: str) -> SafeUrl:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise SecurityValidationError("Only HTTP and HTTPS URLs are supported")
    if parsed.username or parsed.password:
        raise SecurityValidationError("URL credentials are not allowed")
    if not parsed.hostname:
        raise SecurityValidationError("URL host is required")
    domain = parsed.hostname.lower().rstrip(".")
    if domain in {"localhost", "metadata.google.internal"} or domain.endswith(".local"):
        raise SecurityValidationError("Local or internal hostnames are not allowed")
    _validate_host_not_private(domain)
    return SafeUrl(url=url, domain=domain)


def validate_redirect_chain(urls: list[str], max_redirects: int) -> list[SafeUrl]:
    if len(urls) > max_redirects + 1:
        raise SecurityValidationError("Redirect chain is too long")
    return [validate_http_url(url) for url in urls]


def infer_content_type_from_filename(filename: str) -> ContentType:
    safe_name = sanitize_filename(filename)
    extension = PurePath(safe_name).suffix.lower()
    if extension in EXECUTABLE_EXTENSIONS:
        raise SecurityValidationError("Executable files are not supported")
    try:
        return SUPPORTED_EXTENSIONS[extension]
    except KeyError as exc:
        raise SecurityValidationError("Unsupported file extension") from exc


def sanitize_filename(filename: str) -> str:
    name = PurePath(filename).name
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._")
    if not name:
        raise SecurityValidationError("Filename is empty after sanitization")
    if name != filename and (".." in filename or "/" in filename or "\\" in filename):
        raise SecurityValidationError("Path traversal is not allowed")
    return name[:120]


def validate_upload_bytes(data: bytes, max_bytes: int) -> None:
    if not data:
        raise SecurityValidationError("Uploaded file is empty")
    if len(data) > max_bytes:
        raise SecurityValidationError("Uploaded file exceeds configured size limit")
    if data[:2] == b"MZ" or data.startswith(b"#!"):
        raise SecurityValidationError("Executable-looking files are not supported")


def _validate_host_not_private(host: str) -> None:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise SecurityValidationError("Private, loopback, link-local, or reserved IPs are blocked")
