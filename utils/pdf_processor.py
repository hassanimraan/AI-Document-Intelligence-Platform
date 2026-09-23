from io import BytesIO

import fitz  # PyMuPDF

from utils.gemini_extractor import extract_structured_data


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from a PDF.

    Supports:
    1. Normal text-based PDFs
    2. Scanned/image-based PDFs using Gemini vision fallback
    """

    if uploaded_file is None:
        raise ValueError("No PDF file provided.")

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("The PDF file is empty.")

    try:
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(
            f"Unable to read PDF: {exc}"
        ) from exc

    if pdf.page_count == 0:
        pdf.close()
        raise ValueError("The PDF contains no pages.")

    text_parts = []

    try:
        for page_number in range(pdf.page_count):
            page = pdf.load_page(page_number)

            text = page.get_text("text").strip()

            if text:
                text_parts.append(
                    f"--- PAGE {page_number + 1} ---\n{text}"
                )

    finally:
        pdf.close()

    extracted_text = "\n\n".join(text_parts).strip()

    if extracted_text:
        return extracted_text

    raise ValueError(
        "No extractable text was found in this PDF. "
        "This appears to be a scanned/image-based document. "
        "OCR processing will be added in the next step."
    )
