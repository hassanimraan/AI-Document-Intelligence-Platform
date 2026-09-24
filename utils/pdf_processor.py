import fitz

from utils.gemini_extractor import extract_text_from_image


# ============================================================
# CONFIGURATION
# ============================================================

# Short PDF-native text such as "CamScanner" is not considered
# meaningful document content and will trigger OCR.
MIN_MEANINGFUL_TEXT_LENGTH = 80

# Render scanned pages at 2x resolution before sending them
# to Gemini Vision OCR.
PDF_RENDER_SCALE = 2


# ============================================================
# TEXT VALIDATION
# ============================================================

def _is_meaningful_page_text(text):
    """
    Determine whether PDF-native text is substantial enough
    to skip OCR.

    Short embedded text, watermarks, or scanner labels such
    as "CamScanner" are not considered meaningful content.
    """

    if not text:
        return False

    cleaned_text = " ".join(
        text.split()
    ).strip()

    if not cleaned_text:
        return False

    return len(cleaned_text) >= MIN_MEANINGFUL_TEXT_LENGTH


# ============================================================
# PDF OPENING
# ============================================================

def _open_pdf(file_bytes):
    """
    Safely open a PDF from uploaded bytes.

    Returns:
        fitz.Document

    Raises:
        ValueError: if the PDF cannot be opened or is invalid.
    """

    try:
        pdf = fitz.open(
            stream=file_bytes,
            filetype="pdf",
        )

    except Exception as exc:
        raise ValueError(
            "The uploaded file could not be opened as a valid PDF. "
            "Please verify that the file is not corrupted."
        ) from exc

    if pdf.page_count <= 0:
        pdf.close()

        raise ValueError(
            "The PDF contains no readable pages."
        )

    return pdf


# ============================================================
# PAGE TEXT EXTRACTION
# ============================================================

def _extract_native_text(page):
    """
    Extract native PDF text from one page.

    Returns:
        str
    """

    try:
        text = page.get_text(
            "text"
        )

    except Exception as exc:
        raise ValueError(
            "Unable to read text from a PDF page."
        ) from exc

    return text.strip()


# ============================================================
# PAGE OCR
# ============================================================

def _ocr_page(page, page_number):
    """
    Render one PDF page as an image and send it to
    Gemini Vision OCR.

    page_number is used only for user-facing error context.
    """

    try:
        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(
                PDF_RENDER_SCALE,
                PDF_RENDER_SCALE,
            ),
            alpha=False,
        )

        image_bytes = pixmap.tobytes(
            "png"
        )

    except Exception as exc:
        raise ValueError(
            f"Unable to render PDF page {page_number} "
            "for OCR."
        ) from exc

    if not image_bytes:
        raise ValueError(
            f"PDF page {page_number} could not be converted "
            "to an image for OCR."
        )

    try:
        ocr_text = extract_text_from_image(
            image_bytes,
            mime_type="image/png",
        )

    except Exception:
        # Do not replace the Gemini exception here.
        # The Gemini extractor already provides appropriate
        # handling for quota, retry, fallback, and API errors.
        raise

    if not ocr_text or not ocr_text.strip():
        return ""

    return ocr_text.strip()


# ============================================================
# MAIN PDF PROCESSOR
# ============================================================

def extract_text_from_pdf(uploaded_file):
    """
    Extract readable text from an uploaded PDF.

    Processing strategy:

    1. Validate the uploaded file.
    2. Open the PDF safely.
    3. Inspect every page for meaningful native text.
    4. Use native text where sufficient.
    5. Render pages without meaningful text as images.
    6. Send those pages to Gemini Vision OCR.
    7. Combine native and OCR text in page order.
    8. Raise a clear error if nothing readable is obtained.

    Supports:
    - Normal text-based PDFs
    - Scanned/image-based PDFs
    - CamScanner-style PDFs
    - PDFs containing small embedded watermarks
    """

    # --------------------------------------------------------
    # FILE VALIDATION
    # --------------------------------------------------------

    if uploaded_file is None:
        raise ValueError(
            "No PDF file was provided."
        )

    try:
        file_bytes = uploaded_file.getvalue()

    except Exception as exc:
        raise ValueError(
            "The uploaded PDF could not be read."
        ) from exc

    if not file_bytes:
        raise ValueError(
            "The uploaded PDF file is empty."
        )

    # Basic PDF signature check.
    #
    # This is not a replacement for PyMuPDF validation,
    # but it allows us to reject obviously incorrect files
    # before processing them.
    if not file_bytes.startswith(b"%PDF"):
        raise ValueError(
            "The uploaded file does not appear to be a valid PDF."
        )

    # --------------------------------------------------------
    # OPEN PDF
    # --------------------------------------------------------

    pdf = _open_pdf(
        file_bytes
    )

    text_parts = []

    try:

        # ----------------------------------------------------
        # FIRST PASS
        # Extract native text where meaningful.
        # ----------------------------------------------------

        pages_requiring_ocr = []

        for page_index in range(
            pdf.page_count
        ):

            page_number = page_index + 1

            try:
                page = pdf.load_page(
                    page_index
                )

            except Exception as exc:
                raise ValueError(
                    f"Unable to read PDF page {page_number}."
                ) from exc

            native_text = _extract_native_text(
                page
            )

            if _is_meaningful_page_text(
                native_text
            ):

                text_parts.append(
                    (
                        f"--- PAGE {page_number} ---\n"
                        f"{native_text}"
                    )
                )

            else:

                pages_requiring_ocr.append(
                    page_index
                )

        # ----------------------------------------------------
        # SECOND PASS
        # OCR pages without meaningful native text.
        # ----------------------------------------------------

        for page_index in pages_requiring_ocr:

            page_number = page_index + 1

            try:
                page = pdf.load_page(
                    page_index
                )

            except Exception as exc:
                raise ValueError(
                    f"Unable to load PDF page "
                    f"{page_number} for OCR."
                ) from exc

            ocr_text = _ocr_page(
                page,
                page_number,
            )

            if ocr_text:

                text_parts.append(
                    (
                        f"--- PAGE {page_number} (OCR) ---\n"
                        f"{ocr_text}"
                    )
                )

    finally:

        # Always release the PDF resource, including when
        # Gemini raises a quota/API exception.
        pdf.close()

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    extracted_text = "\n\n".join(
        text_parts
    ).strip()

    if not extracted_text:

        raise ValueError(
            "No readable text could be extracted from this PDF. "
            "The document may contain unsupported or unreadable "
            "content."
        )

    return extracted_text
