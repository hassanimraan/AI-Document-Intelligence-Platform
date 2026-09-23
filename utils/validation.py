from config.schema import MASTER_SCHEMA, EXTRACTION_FIELDS


MAX_PDF_SIZE_MB = 20


def validate_schema():
    if not MASTER_SCHEMA:
        raise ValueError("MASTER_SCHEMA is empty.")

    if len(MASTER_SCHEMA) != len(set(MASTER_SCHEMA)):
        raise ValueError("MASTER_SCHEMA contains duplicate fields.")

    if "Sr. No." not in MASTER_SCHEMA:
        raise ValueError("Sr. No. is missing from MASTER_SCHEMA.")

    expected = [
        field for field in MASTER_SCHEMA
        if field != "Sr. No."
    ]

    if EXTRACTION_FIELDS != expected:
        raise ValueError(
            "EXTRACTION_FIELDS does not match MASTER_SCHEMA."
        )

    return True


def validate_record(record):
    if not isinstance(record, dict):
        raise TypeError("Record must be a dictionary.")

    unexpected = set(record.keys()) - set(EXTRACTION_FIELDS)

    if unexpected:
        raise ValueError(
            f"Unexpected fields: {sorted(unexpected)}"
        )

    return True


def validate_pdf(uploaded_file):
    """Validate an uploaded PDF before processing."""

    if uploaded_file is None:
        raise ValueError("No PDF file was uploaded.")

    if not uploaded_file.name.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are allowed.")

    size_mb = uploaded_file.size / (1024 * 1024)

    if size_mb > MAX_PDF_SIZE_MB:
        raise ValueError(
            f"PDF exceeds the {MAX_PDF_SIZE_MB} MB limit."
        )

    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("The uploaded PDF is empty.")

    if not file_bytes.startswith(b"%PDF"):
        raise ValueError("The uploaded file is not a valid PDF.")

    return True
