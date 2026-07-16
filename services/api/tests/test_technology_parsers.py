import pytest

from devmind_api.technology.models import ContentType
from devmind_api.technology.parsers import (
    DocumentParserError,
    parse_document,
    parse_html,
    parse_markdown,
    parse_pdf,
    parse_text,
)


def test_html_extraction_removes_scripts_and_preserves_heading() -> None:
    parsed = parse_html(
        b"<html><head><title>HTML</title><script>bad()</script></head>"
        b"<body><h1>Intro</h1><p>Use semantic tags.</p></body></html>",
        "https://example.com/html",
    )

    assert parsed.title == "HTML"
    assert "bad()" not in parsed.text
    assert "Intro" in parsed.sections


def test_markdown_extraction_preserves_heading_and_code() -> None:
    parsed = parse_markdown(b"# React\n\n```tsx\nconst App = () => null\n```")

    assert parsed.title == "React"
    assert "const App" in parsed.text


def test_text_parser_rejects_binary_content() -> None:
    with pytest.raises(DocumentParserError):
        parse_text(b"hello\x00world")


def test_pdf_parser_reports_image_only_limitations() -> None:
    parsed = parse_pdf(b"%PDF-1.4\n/Type /Page\n%%EOF")

    assert parsed.page_count == 1
    assert parsed.empty_pages == [1]
    assert "OCR was not performed" in parsed.extraction_warnings[0]


def test_parse_document_dispatches_plain_text() -> None:
    parsed = parse_document(ContentType.TEXT, b"Git tracks changes.")

    assert parsed.text == "Git tracks changes."
