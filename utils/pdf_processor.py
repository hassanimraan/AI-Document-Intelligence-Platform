import fitz

from utils.gemini_extractor import extract_text_from_image


# Minimum amount of extracted text considered meaningful.
# Short text such as "CamScanner" should not prevent OCR.
MIN_MEANINGFUL_TEXT_LENGTH = 80


def _is_meaningful_page_text(text):
    """
    Determine whether PDF-native text is substantial enough
    to skip OCR.

    Scanned PDFs can contain small embedded text such as
    "CamScanner". That should not be treated as meaningful
    document content.
    """

    if not text:
        return False

    cleaned_text = " ".join(
        text.split()
    ).strip()

    if not cleaned_text:
        return False

    if len(cleaned_text) < MIN_MEANINGFUL_TEXT_LENGTH:
        return False

    return True


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from a PDF.

    Supports:
    - Normal text-based PDFs
    - Scanned/image-based PDFs
    - PDFs containing only small embedded text/watermarks
      such as "CamScanner"

    Gemini Vision OCR is used when a page does not contain
    sufficient meaningful PDF-native text.
    """

    if uploaded_file is None:
        raise ValueError(
            "No PDF file provided."
        )

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError(
            "The PDF file is empty."
        )

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

    pages_requiring_ocr = []

    try:

        # --------------------------------------------------------
        # FIRST PASS
        # Determine which pages have meaningful native text.
        # --------------------------------------------------------

        for page_number in range(
            pdf.page_count
        ):

            page = pdf.load_page(
                page_number
            )

            text = page.get_text(
                "text"
            ).strip()

            if _is_meaningful_page_text(text):

                text_parts.append(
                    f"--- PAGE {page_number + 1} ---\n"
                    f"{text}"
                )

            else:

                pages_requiring_ocr.append(
                    page_number
                )

        # --------------------------------------------------------
        # SECOND PASS
        # OCR pages that do not contain meaningful native text.
        # --------------------------------------------------------

        for page_number in pages_requiring_ocr:

            page = pdf.load_page(
                page_number
            )

            pixmap = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                alpha=False,
            )

            image_bytes = pixmap.tobytes(
                "png"
            )

            ocr_text = extract_text_from_image(
                image_bytes,
                mime_type="image/png",
            )

            if ocr_text and ocr_text.strip():

                text_parts.append(
                    f"--- PAGE {page_number + 1} (OCR) ---\n"
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
