import io
from typing import Tuple
from pypdf import PdfReader


class DocumentValidator:
    """Pre-flight validator for incoming document uploads before calling Gemini API."""

    MAX_FILE_SIZE_MB = 10.0  # Maximum allowed upload size in MB
    MAX_PAGE_COUNT = 15      # Maximum allowed page limit per document

    @classmethod
    def validate_pdf(
        cls, file_bytes: bytes, filename: str
    ) -> Tuple[bool, str]:
        """Validates file size, PDF header magic bytes, readability, and page count.

        Returns:
            Tuple[bool, str]: (is_valid, error_message_if_invalid)
        """
        # 1. File size check
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > cls.MAX_FILE_SIZE_MB:
            return (
                False,
                f"File size ({size_mb:.1f} MB) exceeds the maximum allowed limit of {cls.MAX_FILE_SIZE_MB} MB.",
            )

        # 2. Magic bytes / MIME check (%PDF- header)
        if not file_bytes.startswith(b"%PDF"):
            return (
                False,
                "Invalid file format. The uploaded file is not a valid PDF document.",
            )

        # 3. PDF readability & page count inspection
        try:
            pdf_stream = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_stream)

            # Check if PDF is encrypted or password-protected
            if reader.is_encrypted:
                return (
                    False,
                    "The uploaded PDF is password-protected or encrypted. Please remove encryption before uploading.",
                )

            page_count = len(reader.pages)
            if page_count == 0:
                return False, "The uploaded PDF appears to be empty."

            if page_count > cls.MAX_PAGE_COUNT:
                return (
                    False,
                    f"Document has {page_count} pages, which exceeds the limit of {cls.MAX_PAGE_COUNT} pages.",
                )

        except Exception as err:
            return (
                False,
                f"Corrupted or unreadable PDF document: {str(err)}",
            )

        return True, ""
