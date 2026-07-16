# Parser Architecture

- HTML: strips scripts/styles, preserves headings and text, records canonical URL when present, and treats content as untrusted.
- PDF: extracts simple text where available, records page-count hints and empty-page limitations, and does not perform OCR.
- Markdown: preserves headings, code blocks, and list structure while removing unsafe embedded scripts/styles.
- Plain text: requires UTF-8 and rejects binary content.

Parser output is normalized before chunking.
