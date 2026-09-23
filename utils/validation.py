from datetime import date, datetime
import re

from config.schema import MASTER_SCHEMA, EXTRACTION_FIELDS


MAX_PDF_SIZE_MB = 20


def validate_schema():
    """Validate the application's master schema."""

    if not MASTER_SCHEMA:
        raise ValueError("MASTER_SCHEMA is empty.")

    if len(MASTER_SCHEMA) != len(set(MASTER_SCHEMA)):
        raise ValueError(
            "MASTER_SCHEMA contains duplicate fields."
        )

    if "Sr. No." not in MASTER_SCHEMA:
        raise ValueError(
            "Sr. No. is missing from MASTER_SCHEMA."
        )

    expected = [
        field
        for field in MASTER_SCHEMA
        if field != "Sr. No."
    ]

    if EXTRACTION_FIELDS != expected:
        raise ValueError(
            "EXTRACTION_FIELDS does not match MASTER_SCHEMA."
        )

    return True


def validate_record(record):
    """
    Validate an extracted or corrected credential record.

    Only fields defined in EXTRACTION_FIELDS are accepted.
    """

    if not isinstance(record, dict):
        raise TypeError(
            "Record must be a dictionary."
        )

    unexpected = (
        set(record.keys())
        - set(EXTRACTION_FIELDS)
    )

    if unexpected:
        raise ValueError(
            f"Unexpected fields: {sorted(unexpected)}"
        )

    return True


def normalize_amount(value):
    """
    Convert an extracted amount into a database-friendly number.

    Examples:
        '1,250,000'       -> 1250000
        'PKR 1,250,000'   -> 1250000
        'Rs. 250,500.75'  -> 250500.75
        ''                -> None
    """

    if value is None:
        return None

    if isinstance(value, bool):
        raise ValueError(
            "Amount cannot be a boolean value."
        )

    if isinstance(value, (int, float)):
        return value

    text = str(value).strip()

    if not text:
        return None

    # Handle accounting-style negative values:
    # (125000) -> -125000
    is_parenthesized = (
        text.startswith("(")
        and text.endswith(")")
    )

    if is_parenthesized:
        text = text[1:-1].strip()

    # Remove common currency labels/symbols.
    text = re.sub(
        r"(?i)\b(pkr|rs|rs\.|rupees?)\b",
        "",
        text
    )

    text = text.replace("₨", "")
    text = text.replace("₹", "")
    text = text.replace("$", "")
    text = text.replace(",", "")
    text = text.strip()

    if not text:
        return None

    # Allow only a standard numeric format.
    if not re.fullmatch(
        r"-?\d+(?:\.\d+)?",
        text
    ):
        raise ValueError(
            f"Invalid amount value: {value}"
        )

    number = float(text)

    if is_parenthesized:
        number = -abs(number)

    # Store whole numbers as integers.
    if number.is_integer():
        return int(number)

    return number


def normalize_date(value):
    """
    Convert common extracted date formats to YYYY-MM-DD.

    Supported examples:
        2026-09-23
        23/09/2026
        23-09-2026
        23.09.2026
        23 September 2026
        23 Sep 2026
        September 23, 2026
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

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(
                text,
                fmt
            )
            return parsed.date().isoformat()
        except ValueError:
            continue

    raise ValueError(
        f"Invalid date value: {value}"
    )


def normalize_text(value):
    """
    Normalize text fields.

    Empty values become None.
    Other values are converted to trimmed strings.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    return text


def normalize_record(record):
    """
    Validate and normalize a credential record.

    Returns a new dictionary containing exactly the
    extraction fields defined by the master schema.
    """

    validate_record(record)

    normalized = {}

    for field in EXTRACTION_FIELDS:
        value = record.get(field)

        if field == "Amount":
            normalized[field] = normalize_amount(value)

        elif field == "Date of Issuance":
            normalized[field] = normalize_date(value)

        else:
            normalized[field] = normalize_text(value)

    return normalized


def validate_pdf(uploaded_file):
    """
    Validate an uploaded PDF file.
    """

    if uploaded_file is None:
        raise ValueError(
            "No PDF file was uploaded."
        )

    if not uploaded_file.name.lower().endswith(".pdf"):
        raise ValueError(
            "Only PDF files are allowed."
        )

    size_mb = uploaded_file.size / (
        1024 * 1024
    )

    if size_mb > MAX_PDF_SIZE_MB:
        raise ValueError(
            f"PDF exceeds the "
            f"{MAX_PDF_SIZE_MB} MB limit."
        )

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError(
            "The uploaded PDF is empty."
        )

    if not file_bytes.startswith(b"%PDF"):
        raise ValueError(
            "The uploaded file is not a valid PDF."
        )

    return True
