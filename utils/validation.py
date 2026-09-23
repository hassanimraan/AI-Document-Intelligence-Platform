from config.schema import MASTER_SCHEMA, EXTRACTION_FIELDS


def validate_schema():
    """Validate the application master schema."""

    if not MASTER_SCHEMA:
        raise ValueError("MASTER_SCHEMA is empty.")

    if len(MASTER_SCHEMA) != len(set(MASTER_SCHEMA)):
        raise ValueError("MASTER_SCHEMA contains duplicate fields.")

    if "Sr. No." not in MASTER_SCHEMA:
        raise ValueError("Sr. No. is missing from MASTER_SCHEMA.")

    expected_extraction_fields = [
        field for field in MASTER_SCHEMA
        if field != "Sr. No."
    ]

    if EXTRACTION_FIELDS != expected_extraction_fields:
        raise ValueError(
            "EXTRACTION_FIELDS does not match MASTER_SCHEMA."
        )

    return True


def validate_record(record):
    """Validate an extracted record against the schema."""

    if not isinstance(record, dict):
        raise TypeError("Record must be a dictionary.")

    unexpected_fields = set(record.keys()) - set(EXTRACTION_FIELDS)

    if unexpected_fields:
        raise ValueError(
            f"Unexpected fields: {sorted(unexpected_fields)}"
        )

    return True