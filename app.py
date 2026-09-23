import json

import streamlit as st

from utils.validation import validate_pdf
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import extract_structured_data
from config.schema import EXTRACTION_FIELDS


st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Credential Extraction Assistant")

st.info(
    "Phase 5 — Human Verification & Editing"
)


uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"]
)


if uploaded_file:

    st.write(f"**File:** {uploaded_file.name}")

    if st.button(
        "Process PDF",
        type="primary"
    ):

        try:

            # -----------------------------
            # Step 1 — Validate PDF
            # -----------------------------

            validate_pdf(uploaded_file)

            st.success(
                "✓ PDF validation successful."
            )


            # -----------------------------
            # Step 2 — Extract PDF text
            # -----------------------------

            with st.spinner(
                "Reading PDF..."
            ):

                document_text = (
                    extract_text_from_pdf(
                        uploaded_file
                    )
                )

            st.success(
                "✓ PDF text/OCR extraction successful."
            )


            # -----------------------------
            # Step 3 — Gemini extraction
            # -----------------------------

            with st.spinner(
                "Gemini is analyzing the document..."
            ):

                result = extract_structured_data(
                    document_text
                )


            st.success(
                "✓ Gemini extraction successful."
            )


            # -----------------------------
            # Step 4 — Parse JSON
            # -----------------------------

            try:

                extracted_data = json.loads(
                    result
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    "Gemini returned invalid JSON."
                ) from exc


            # -----------------------------
            # Store temporarily
            # -----------------------------

            st.session_state[
                "extracted_data"
            ] = extracted_data

            st.session_state[
                "document_text"
            ] = document_text

            st.session_state[
                "processed_filename"
            ] = uploaded_file.name


        except Exception as e:

            st.error(
                f"Processing failed: {e}"
            )


# =========================================================
# HUMAN VERIFICATION
# =========================================================

if "extracted_data" in st.session_state:

    st.divider()

    st.header(
        "🔎 Review & Verify Extracted Data"
    )

    st.warning(
        "Please carefully review every field. "
        "You can correct or complete the information "
        "before confirming the record."
    )


    extracted_data = st.session_state[
        "extracted_data"
    ]


    edited_data = {}


    # -----------------------------------------------------
    # Editable fields
    # -----------------------------------------------------

    for field in EXTRACTION_FIELDS:

        current_value = extracted_data.get(
            field,
            ""
        )

        edited_data[field] = st.text_input(
            field,
            value=str(current_value)
        )


    st.divider()


    # -----------------------------------------------------
    # Confirmation
    # -----------------------------------------------------

    st.subheader(
        "Confirm Record"
    )

    st.write(
        "Review the information above before saving."
    )


    confirmed = st.checkbox(
        "I have reviewed and verified all fields."
    )


    if st.button(
        "✓ Confirm & Save Record",
        type="primary"
    ):

        if not confirmed:

            st.error(
                "Please confirm that you have reviewed "
                "all fields before saving."
            )

        else:

            # IMPORTANT:
            # Database saving will be added later.
            # For now we only store the verified
            # record temporarily in session state.

            st.session_state[
                "verified_data"
            ] = edited_data

            st.success(
                "✓ Record verified successfully."
            )

            st.info(
                "Database saving will be enabled "
                "in the Supabase phase."
            )


    # -----------------------------------------------------
    # Show verified data
    # -----------------------------------------------------

    if "verified_data" in st.session_state:

        st.divider()

        st.subheader(
            "Verified Record"
        )

        st.json(
            st.session_state[
                "verified_data"
            ]
        )
