import hashlib
from base64 import urlsafe_b64encode


def sha256_hex(data: bytes | str) -> str:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(payload).hexdigest()


def stable_id(prefix: str, data: bytes | str) -> str:
    digest = sha256_hex(data)
    token = urlsafe_b64encode(bytes.fromhex(digest[:24])).decode("ascii").rstrip("=")
    return f"{prefix}_{token}"
