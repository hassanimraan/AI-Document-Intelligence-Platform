from datetime import date, datetime
import math
import re

from config.schema import (
    MASTER_SCHEMA,
    EXTRACTION_FIELDS,
)


# ============================================================
# CONFIGURATION
# ============================================================

MAX_PDF_SIZE_MB = 50


# ============================================================
# SCHEMA VALIDATION
# ============================================================

def validate_schema():
    """Validate the application's master schema."""

    if not MASTER_SCHEMA:
        raise ValueError(
            "MASTER_SCHEMA is empty."
        )

    if len(MASTER_SCHEMA) != len(
        set(MASTER_SCHEMA)
    ):
        raise ValueError(
            "MASTER_SCHEMA contains duplicate fields."
        )

    if "Sr. No." not in MASTER_SCHEMA:
        raise ValueError(
            "Sr. No. is missing from MASTER_SCHEMA."
        )

    expected_extraction_fields = [
        field
        for field in MASTER_SCHEMA
        if field != "Sr. No."
    ]

    if EXTRACTION_FIELDS != expected_extraction_fields:
        raise ValueError(
            "EXTRACTION_FIELDS does not match MASTER_SCHEMA."
        )

    return True


# ============================================================
# RECORD VALIDATION
# ============================================================

def validate_record(record):
    """
    Validate an extracted or corrected credential record.

    Only fields defined in EXTRACTION_FIELDS are accepted.
    """

    if not isinstance(record, dict):
        raise TypeError(
            "Record must be a dictionary."
        )

    actual_fields = set(
        record.keys()
    )

    allowed_fields = set(
        EXTRACTION_FIELDS
    )

    unexpected_fields = (
        actual_fields - allowed_fields
    )

    if unexpected_fields:
        raise ValueError(
            "Unexpected fields found in record: "
            f"{sorted(unexpected_fields)}"
        )

    return True


# ============================================================
# AMOUNT NORMALIZATION
# ============================================================

def normalize_amount(value):
    """
    Convert an extracted amount into a database-friendly
    integer or floating-point number.

    Examples:

        '1,250,000'       -> 1250000
        'PKR 1,250,000'   -> 1250000
        'Rs. 250,500.75'  -> 250500.75
        '(125000)'        -> -125000
        ''                -> None
    """

    if value is None:
        return None

    if isinstance(value, bool):
        raise ValueError(
            "Amount cannot be a boolean value."
        )

    if isinstance(value, (int, float)):

        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError(
                    "Amount must be a finite number."
                )

        return value

    text = str(value).strip()

    if not text:
        return None

    # --------------------------------------------------------
    # Accounting-style negative values.
    #
    # Example:
    # (125000) -> -125000
    # --------------------------------------------------------

    is_parenthesized = (
        text.startswith("(")
        and text.endswith(")")
    )

    if is_parenthesized:
        text = text[1:-1].strip()

    # --------------------------------------------------------
    # Remove common currency labels/symbols.
    # --------------------------------------------------------

    text = re.sub(
        r"(?i)\b(pkr|rs|rs\.|rupees?)\b",
        "",
        text,
    )

    text = text.replace("₨", "")
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace(",", "")
    text = text.strip()

    if not text:
        return None

    # --------------------------------------------------------
    # Strict numeric validation.
    # --------------------------------------------------------

    if not re.fullmatch(
        r"-?\d+(?:\.\d+)?",
        text,
    ):
        raise ValueError(
            f"Invalid amount value: {value}"
        )

    number = float(text)

    if not math.isfinite(number):
        raise ValueError(
            f"Invalid amount value: {value}"
        )

    if is_parenthesized:
        number = -abs(number)

    # --------------------------------------------------------
    # Return integers as integers.
    # This produces cleaner PostgreSQL numeric values
    # and cleaner Excel output.
    # --------------------------------------------------------

    if number.is_integer():
        return int(number)

    return number


# ============================================================
# DATE NORMALIZATION
# ============================================================

def normalize_date(value):
    """
    Convert common extracted date formats to YYYY-MM-DD.

    Supported examples include:

        2026-09-23
        23/09/2026
        23-09-2026
        23.09.2026
        23 September 2026
        23 Sep 2026
        September 23, 2026
        Tue 7/28/2026 12:55 PM
        Tuesday 7/28/2026 12:55 PM
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()

    if not text:
        return None

    # --------------------------------------------------------
    # Remove leading weekday names.
    # --------------------------------------------------------

    text_without_weekday = re.sub(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|"
        r"Sunday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    # --------------------------------------------------------
    # Supported date formats.
    # --------------------------------------------------------

    formats = [

        # Date + time
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y %H:%M",
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %H:%M",

        # ISO
        "%Y-%m-%d",

        # Numeric date formats
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d.%m.%Y",

        # Text dates
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:

        try:

            parsed = datetime.strptime(
                text_without_weekday,
                fmt,
            )

            return parsed.date().isoformat()

        except ValueError:
            continue

    raise ValueError(
        f"Invalid date value: {value}"
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize a credential text field.

    Empty values become None.
    Other values are converted to trimmed strings.
    Repeated whitespace is collapsed.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    # Collapse repeated spaces/newlines/tabs.
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    if not text:
        return None

    return text


# ============================================================
# COMPLETE RECORD NORMALIZATION
# ============================================================

def normalize_record(record):
    """
    Validate and normalize a credential record.

    Returns a new dictionary containing exactly the
    extraction fields defined by the master schema.

    Sr. No. is deliberately excluded because it is generated
    by the application/database export layer.
    """

    validate_record(
        record
    )

    normalized = {}

    for field in EXTRACTION_FIELDS:

        value = record.get(
            field
        )

        if field == "Amount":

            normalized[field] = (
                normalize_amount(value)
            )

        elif field == "Date of Issuance":

            normalized[field] = (
                normalize_date(value)
            )

        else:

            normalized[field] = (
                normalize_text(value)
            )

    return normalized


# ============================================================
# PDF VALIDATION
# ============================================================

def validate_pdf(uploaded_file):
    """
    Validate an uploaded PDF before processing.

    Checks:

    1. File exists.
    2. Filename has .pdf extension.
    3. File does not exceed MAX_PDF_SIZE_MB.
    4. File contains data.
    5. File begins with the PDF file signature.
    """

    if uploaded_file is None:
        raise ValueError(
            "No PDF file was uploaded."
        )

    filename = getattr(
        uploaded_file,
        "name",
        "",
    )

    if not filename:
        raise ValueError(
            "The uploaded file has no filename."
        )

    if not filename.lower().endswith(
        ".pdf"
    ):
        raise ValueError(
            "Only PDF files are allowed."
        )

    # --------------------------------------------------------
    # File size
    # --------------------------------------------------------

    file_size = getattr(
        uploaded_file,
        "size",
        None,
    )

    if file_size is not None:

        if file_size < 0:
            raise ValueError(
                "The uploaded PDF has an invalid file size."
            )

        size_mb = (
            file_size
            / (1024 * 1024)
        )

        if size_mb > MAX_PDF_SIZE_MB:
            raise ValueError(
                f"PDF exceeds the "
                f"{MAX_PDF_SIZE_MB} MB limit."
            )

    # --------------------------------------------------------
    # File contents
    # --------------------------------------------------------

    try:
        file_bytes = uploaded_file.getvalue()

    except Exception as exc:
        raise ValueError(
            "The uploaded PDF could not be read."
        ) from exc

    if not file_bytes:
        raise ValueError(
            "The uploaded PDF is empty."
        )

    # --------------------------------------------------------
    # PDF signature
    # --------------------------------------------------------

    if not file_bytes.startswith(
        b"%PDF"
    ):
        raise ValueError(
            "The uploaded file is not a valid PDF."
        )

    return True


# ============================================================
# MODULE VALIDATION
# ============================================================

validate_schema()
