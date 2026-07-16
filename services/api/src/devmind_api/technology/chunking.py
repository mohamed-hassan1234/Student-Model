from devmind_api.technology.hashing import sha256_hex, stable_id
from devmind_api.technology.models import (
    DocumentChunk,
    ParsedDocument,
    PermissionStatus,
    RegisteredSource,
    ReviewStatus,
)
from devmind_shared.time import utc_now


class Chunker:
    def __init__(self, chunk_size: int, overlap: int) -> None:
        if overlap >= chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size")
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(
        self,
        source: RegisteredSource,
        parsed: ParsedDocument,
        document_id: str,
        document_version_id: str,
    ) -> list[DocumentChunk]:
        text = parsed.text
        chunks: list[DocumentChunk] = []
        seen_hashes: set[str] = set()
        start = 0
        number = 1
        while start < len(text):
            end = min(len(text), start + self._chunk_size)
            if end < len(text):
                newline = text.rfind("\n\n", start, end)
                if newline > start + 200:
                    end = newline
            fragment = text[start:end].strip()
            if len(fragment) >= 40 or not chunks:
                content_hash = sha256_hex(fragment)
                if content_hash not in seen_hashes:
                    seen_hashes.add(content_hash)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=stable_id(
                                "chk", f"{document_version_id}:{number}:{content_hash}"
                            ),
                            source_id=source.source_id,
                            document_id=document_id,
                            document_version_id=document_version_id,
                            original_reference=source.original_reference,
                            document_title=parsed.title,
                            section_heading=_section_for(parsed.sections, fragment),
                            page_number=1
                            if parsed.content_type.value == "application/pdf"
                            else None,
                            chunk_number=number,
                            character_start=start,
                            character_end=end,
                            token_estimate=max(1, len(fragment.split())),
                            text=fragment,
                            content_hash=content_hash,
                            trust_level=source.trust_level,
                            license_status=source.license_review_status,
                            retrieval_use_status=source.retrieval_use_permission,
                            training_use_status=source.training_use_permission,
                            prompt_injection_flags=parsed.prompt_injection_flags,
                            ingestion_timestamp=utc_now(),
                        )
                    )
                    number += 1
            if end >= len(text):
                break
            start = max(end - self._overlap, start + 1)
        return chunks


def _section_for(sections: list[str], fragment: str) -> str | None:
    for section in sections:
        if section in fragment:
            return section
    return sections[0] if sections else None


def chunk_is_retrievable(chunk: DocumentChunk) -> bool:
    return (
        chunk.license_status is ReviewStatus.APPROVED
        and chunk.retrieval_use_status is PermissionStatus.ALLOWED
        and chunk.prompt_injection_flags.risk_score < 1.0
    )
