import fitz

from utils.gemini_extractor import extract_text_from_image


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from a PDF.

    Supports:
    - Normal text-based PDFs
    - Scanned/image-based PDFs using Gemini Vision OCR
    """

    if uploaded_file is None:
        raise ValueError("No PDF file provided.")

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("The PDF file is empty.")

    try:
        pdf = fitz.open(
            stream=file_bytes,
            filetype="pdf"
        )
    except Exception as exc:
        raise ValueError(
            f"Unable to read PDF: {exc}"
        ) from exc

    if pdf.page_count == 0:
        pdf.close()
        raise ValueError(
            "The PDF contains no pages."
        )

    text_parts = []
    pages_without_text = []

    try:
        # First attempt: normal PDF text extraction
        for page_number in range(pdf.page_count):

            page = pdf.load_page(page_number)

            text = page.get_text("text").strip()

            if text:
                text_parts.append(
                    f"--- PAGE {page_number + 1} ---\n{text}"
                )
            else:
                pages_without_text.append(
                    page_number
                )

        # If every page has text, return normally.
        if not pages_without_text:
            return "\n\n".join(text_parts).strip()

        # OCR only pages where no text was found.
        for page_number in pages_without_text:

            page = pdf.load_page(page_number)

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False
            )

            image_bytes = pixmap.tobytes(
                "png"
            )

            ocr_text = extract_text_from_image(
                image_bytes,
                mime_type="image/png"
            )

            if ocr_text and ocr_text.strip():

                text_parts.append(
                    f"--- PAGE {page_number + 1} "
                    f"(OCR) ---\n"
                    f"{ocr_text.strip()}"
                )

    finally:
        pdf.close()

    extracted_text = "\n\n".join(
        text_parts
    ).strip()

    if not extracted_text:
        raise ValueError(
            "No readable text could be extracted "
            "from this PDF, including OCR processing."
        )

    return extracted_text
