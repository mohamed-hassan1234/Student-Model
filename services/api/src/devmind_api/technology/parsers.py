import re
from html.parser import HTMLParser

from devmind_api.technology.models import ContentType, ParsedDocument
from devmind_api.technology.normalization import looks_binary, normalize_text
from devmind_api.technology.prompt_injection import mark_prompt_injection


class DocumentParserError(ValueError):
    pass


class SafeHtmlExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []
        self._title_parts: list[str] = []
        self._in_title = False
        self._canonical_url: str | None = None
        self._current_heading: str | None = None
        self.headings: list[str] = []

    @property
    def canonical_url(self) -> str | None:
        return self._canonical_url

    @property
    def title(self) -> str:
        return normalize_text(" ".join(self._title_parts)) or "Untitled HTML document"

    @property
    def text(self) -> str:
        return normalize_text("\n".join(self._parts))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag == "link":
            attr_map = dict(attrs)
            if attr_map.get("rel") == "canonical" and attr_map.get("href"):
                self._canonical_url = attr_map["href"]
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "code"}:
            self._parts.append("\n")
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._current_heading = ""

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._current_heading:
            heading = normalize_text(self._current_heading)
            if heading:
                self.headings.append(heading)
            self._current_heading = None
        if tag in {"p", "li", "pre", "code"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
        if self._current_heading is not None:
            self._current_heading += data
        self._parts.append(data)


def parse_html(data: bytes, source_url: str | None = None) -> ParsedDocument:
    text = data.decode("utf-8", errors="replace")
    extractor = SafeHtmlExtractor()
    extractor.feed(text)
    parsed_text = extractor.text
    if not parsed_text:
        raise DocumentParserError("HTML document did not contain extractable text")
    return ParsedDocument(
        title=extractor.title,
        content_type=ContentType.HTML,
        text=parsed_text,
        sections=extractor.headings,
        canonical_url=extractor.canonical_url or source_url,
        prompt_injection_flags=mark_prompt_injection(parsed_text),
    )


def parse_markdown(data: bytes) -> ParsedDocument:
    text = _decode_text(data)
    text = re.sub(r"<script\b.*?</script>", "", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", "", text, flags=re.I | re.S)
    title = _first_heading(text) or "Untitled Markdown document"
    normalized = normalize_text(text)
    return ParsedDocument(
        title=title,
        content_type=ContentType.MARKDOWN,
        text=normalized,
        sections=re.findall(r"^#{1,6}\s+(.+)$", normalized, flags=re.M),
        prompt_injection_flags=mark_prompt_injection(normalized),
    )


def parse_text(data: bytes) -> ParsedDocument:
    text = _decode_text(data)
    normalized = normalize_text(text)
    if not normalized:
        raise DocumentParserError("Text document is empty")
    return ParsedDocument(
        title="Plain text document",
        content_type=ContentType.TEXT,
        text=normalized,
        prompt_injection_flags=mark_prompt_injection(normalized),
    )


def parse_pdf(data: bytes) -> ParsedDocument:
    if not data.startswith(b"%PDF"):
        raise DocumentParserError("PDF header is missing")
    raw = data.decode("latin-1", errors="ignore")
    pages = max(1, raw.count("/Type /Page"))
    literal_strings = re.findall(r"\(([^()] {0,2000}|[^()]{1,2000})\)\s*Tj", raw)
    if not literal_strings:
        literal_strings = re.findall(r"\(([^()]{1,2000})\)", raw)
    text = normalize_text("\n".join(_unescape_pdf_string(item) for item in literal_strings))
    warnings: list[str] = []
    empty_pages: list[int] = []
    if not text:
        warnings.append("No extractable PDF text found; OCR was not performed")
        empty_pages = list(range(1, pages + 1))
        text = "PDF contained no extractable text."
    return ParsedDocument(
        title="PDF document",
        content_type=ContentType.PDF,
        text=text,
        page_count=pages,
        empty_pages=empty_pages,
        extraction_warnings=warnings,
        prompt_injection_flags=mark_prompt_injection(text),
    )


def parse_document(
    content_type: ContentType, data: bytes, source_url: str | None = None
) -> ParsedDocument:
    if content_type is not ContentType.PDF and looks_binary(data):
        raise DocumentParserError("Unsupported binary content")
    if content_type is ContentType.HTML:
        return parse_html(data, source_url)
    if content_type is ContentType.MARKDOWN:
        return parse_markdown(data)
    if content_type is ContentType.TEXT:
        return parse_text(data)
    if content_type is ContentType.PDF:
        return parse_pdf(data)
    raise DocumentParserError(f"Unsupported content type: {content_type}")


def _decode_text(data: bytes) -> str:
    if looks_binary(data):
        raise DocumentParserError("Binary content is not supported")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentParserError("Text content must be UTF-8 encoded") from exc


def _first_heading(text: str) -> str | None:
    match = re.search(r"^#{1,6}\s+(.+)$", text, flags=re.M)
    return normalize_text(match.group(1)) if match else None


def _unescape_pdf_string(value: str) -> str:
    return (
        value.replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\n", "\n")
        .replace(r"\r", "\n")
        .replace(r"\t", "\t")
    )
