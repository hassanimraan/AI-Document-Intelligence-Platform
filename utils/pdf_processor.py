from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file):
    """Extract text from all pages of an uploaded PDF."""

    if uploaded_file is None:
        raise ValueError("No PDF file provided.")

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("The PDF file is empty.")

    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(
            f"Unable to read PDF: {exc}"
        ) from exc

    if not reader.pages:
        raise ValueError("The PDF contains no pages.")

    text_parts = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""

            if text.strip():
                text_parts.append(
                    f"--- PAGE {page_number} ---\n{text.strip()}"
                )

        except Exception as exc:
            raise ValueError(
                f"Unable to extract text from page {page_number}: {exc}"
            ) from exc

    extracted_text = "\n\n".join(text_parts).strip()

    if not extracted_text:
        raise ValueError(
            "No extractable text was found in this PDF. "
            "The document may be scanned/image-based and will "
            "require OCR processing."
        )

    return extracted_text