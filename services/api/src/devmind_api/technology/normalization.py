import re


def normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def looks_binary(data: bytes) -> bool:
    if not data:
        return False
    sample = data[:2048]
    return b"\x00" in sample
