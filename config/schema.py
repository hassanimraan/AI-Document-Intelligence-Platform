MASTER_SCHEMA = [
    "Sr. No.",
    "Client (PMA)",
    "System (LMBS, PMBS, MMBS, OLMRTS)",
    "Contract",
    "Document Type",
    "Document Number",
    "Date of Issuance",
    "Amount",
    "Initiated By",
    "Reviewed By",
    "Approved by",
]

GENERATED_FIELDS = [
    "Sr. No.",
]

EXTRACTION_FIELDS = [
    field for field in MASTER_SCHEMA
    if field not in GENERATED_FIELDS
]