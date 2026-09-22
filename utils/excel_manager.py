import os
from typing import Any, Dict, List, Tuple
import pandas as pd

DEFAULT_TEMPLATE_PATH = os.path.join("config", "master_template.xlsx")

# Set of header variations that should be handled by the app rather than Gemini OCR
APP_GENERATED_FIELDS = {"sr. no.", "sr no", "sr_no", "sr.no.", "s.no."}


class SchemaManager:
    """Dynamic Excel Schema Engine to read, validate, and separate extraction

    targets from application-generated fields.
    """

    def __init__(self, template_path: str = DEFAULT_TEMPLATE_PATH):
        self.template_path = template_path
        self.master_headers: List[str] = []
        self.extraction_fields: List[str] = []
        self.reserved_fields: List[str] = []
        self.load_and_validate_schema()

    def load_and_validate_schema(self) -> Tuple[List[str], List[str]]:
        """Reads row 1 of master_template.xlsx, validates structure, and separates

        app-generated fields (Sr. No.) from Gemini extraction targets.
        """
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(
                f"Master template missing at '{self.template_path}'."
            )

        try:
            df = pd.read_excel(self.template_path, nrows=0)
        except Exception as e:
            raise ValueError(f"Error reading Excel sheet: {str(e)}")

        headers = [str(col).strip() for col in df.columns]

        if not headers:
            raise ValueError("The master template header row is empty.")

        # Header Validation (check for duplicates or blanks)
        seen = set()
        for idx, h in enumerate(headers):
            if not h or h.startswith("Unnamed:"):
                raise ValueError(
                    f"Column index {idx + 1} has a blank/invalid header name."
                )
            if h.lower() in seen:
                raise ValueError(
                    f"Duplicate header detected: '{h}'. Column names must be"
                    " unique."
                )
            seen.add(h.lower())

        self.master_headers = headers
        self.reserved_fields = [
            h for h in headers if h.lower().strip() in APP_GENERATED_FIELDS
        ]
        self.extraction_fields = [
            h for h in headers if h.lower().strip() not in APP_GENERATED_FIELDS
        ]

        return self.master_headers, self.extraction_fields

    def get_gemini_json_structure(self) -> Dict[str, Any]:
        """Generates sample JSON structure required by Gemini system prompt."""
        return {field: None for field in self.extraction_fields}


def build_default_template(filepath: str = DEFAULT_TEMPLATE_PATH) -> None:
    """Creates default template matching the locked 11-column master schema if missing."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    headers = [
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

    df = pd.DataFrame(columns=headers)
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Master Schema")