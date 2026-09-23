import json

import streamlit as st

from utils.validation import validate_pdf
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import (
    extract_structured_data,
    apply_natural_language_correction,
)
from config.schema import EXTRACTION_FIELDS


st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Credential Extraction Assistant")

st.info(
    "Phase 6 — Natural-Language Correction"
)


# =========================================================
# PDF UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"]
)


if uploaded_file:

    st.write(
        f"**File:** {uploaded_file.name}"
    )

    if st.button(
        "Process PDF",
        type="primary"
    ):

        try:

            # -------------------------------------------------
            # Step 1 — Validate PDF
            # -------------------------------------------------

            validate_pdf(
                uploaded_file
            )

            st.success(
                "✓ PDF validation successful."
            )


            # -------------------------------------------------
            # Step 2 — Extract PDF text
            # -------------------------------------------------

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


            # -------------------------------------------------
            # Step 3 — Gemini extraction
            # -------------------------------------------------

            with st.spinner(
                "Gemini is analyzing the document..."
            ):

                result = extract_structured_data(
                    document_text
                )


            st.success(
                "✓ Gemini extraction successful."
            )


            # -------------------------------------------------
            # Step 4 — Parse JSON
            # -------------------------------------------------

            try:

                extracted_data = json.loads(
                    result
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    "Gemini returned invalid JSON."
                ) from exc


            # -------------------------------------------------
            # Step 5 — Store temporary data
            # -------------------------------------------------

            st.session_state[
                "extracted_data"
            ] = extracted_data

            st.session_state[
                "document_text"
            ] = document_text

            st.session_state[
                "processed_filename"
            ] = uploaded_file.name

            # Clear previous correction state
            st.session_state.pop(
                "corrected_data",
                None
            )

            st.session_state.pop(
                "correction_instruction",
                None
            )


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
        "You can manually correct information "
        "or use the natural-language correction "
        "assistant below."
    )


    extracted_data = st.session_state[
        "extracted_data"
    ]


    # =====================================================
    # MANUAL EDITING
    # =====================================================

    st.subheader(
        "Extracted Information"
    )

    edited_data = {}


    for field in EXTRACTION_FIELDS:

        current_value = extracted_data.get(
            field,
            ""
        )

        edited_data[field] = st.text_input(
            field,
            value=str(current_value),
            key=f"manual_{field}"
        )


    # =====================================================
    # NATURAL-LANGUAGE CORRECTION
    # =====================================================

    st.divider()

    st.subheader(
        "💬 Natural-Language Correction"
    )

    st.write(
        "Instead of editing a field manually, "
        "you can describe the correction in normal language."
    )

    st.caption(
        'Example: "Change the amount to PKR 4,500,000."'
    )

    correction_instruction = st.text_area(
        "Describe your correction",
        placeholder=(
            "Example: Change the client name to ABC Construction "
            "and the amount to PKR 4,500,000."
        ),
        height=100,
        key="correction_instruction"
    )


    if st.button(
        "✨ Apply Correction",
        type="secondary"
    ):

        if not correction_instruction.strip():

            st.error(
                "Please enter a correction instruction."
            )

        else:

            try:

                # Build the current record from the
                # manually edited fields.
                current_record = {
                    field: edited_data.get(
                        field,
                        ""
                    )
                    for field in EXTRACTION_FIELDS
                }


                with st.spinner(
                    "Gemini is applying your correction..."
                ):

                    corrected_data = (
                        apply_natural_language_correction(
                            current_record,
                            correction_instruction
                        )
                    )


                st.session_state[
                    "corrected_data"
                ] = corrected_data

                st.success(
                    "✓ Correction applied. "
                    "Please review the updated values below."
                )


            except Exception as e:

                st.error(
                    f"Correction failed: {e}"
                )


    # =====================================================
    # CORRECTED DATA
    # =====================================================

    if "corrected_data" in st.session_state:

        st.divider()

        st.subheader(
            "🔄 Corrected Record — Review Again"
        )

        st.warning(
            "The correction has NOT been saved. "
            "Review these values carefully before confirmation."
        )

        corrected_data = st.session_state[
            "corrected_data"
        ]

        final_data = {}


        for field in EXTRACTION_FIELDS:

            final_value = corrected_data.get(
                field,
                ""
            )

            final_data[field] = st.text_input(
                field,
                value=str(final_value),
                key=f"corrected_{field}"
            )


        st.divider()

        st.subheader(
            "Confirm Record"
        )

        st.write(
            "After reviewing the final values, "
            "confirm that the record is correct."
        )

        confirmed = st.checkbox(
            "I have reviewed and verified all fields.",
            key="final_confirmation"
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

                # Database saving will be implemented
                # in the Supabase phase.

                st.session_state[
                    "verified_data"
                ] = final_data

                st.success(
                    "✓ Record verified successfully."
                )

                st.info(
                    "Database saving will be enabled "
                    "in the Supabase phase."
                )


    else:

        # =================================================
        # CONFIRMATION WITHOUT AI CORRECTION
        # =================================================

        st.divider()

        st.subheader(
            "Confirm Record"
        )

        st.write(
            "You can also manually edit the fields above "
            "and confirm the record without using "
            "natural-language correction."
        )

        confirmed_manual = st.checkbox(
            "I have reviewed and verified all fields.",
            key="manual_confirmation"
        )


        if st.button(
            "✓ Confirm & Save Record",
            type="primary",
            key="manual_save"
        ):

            if not confirmed_manual:

                st.error(
                    "Please confirm that you have reviewed "
                    "all fields before saving."
                )

            else:

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


# =========================================================
# VERIFIED DATA
# =========================================================

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
