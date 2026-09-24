```python
import streamlit as st

from config.schema import EXTRACTION_FIELDS
from utils.validation import normalize_record
from utils.database import DatabaseManager
from ui.common import reset_after_manual_edit


def _render_record_fields(data, key_prefix):
    edited_data = {}

    for field in EXTRACTION_FIELDS:
        value = data.get(field)

        if value is None:
            value = ""

        edited_data[field] = st.text_input(
            field,
            value=str(value),
            key=f"{key_prefix}_{field}",
        )

    return edited_data


def render_manual_review():
    extracted_data = st.session_state.get(
        "extracted_data"
    )

    if not extracted_data:
        return

    st.divider()

    st.header("✏️ Review Extracted Data")

    st.write(
        "Review the information extracted by Gemini. "
        "You can correct any field manually before continuing."
    )

    edited_data = _render_record_fields(
        extracted_data,
        "manual_review",
    )

    if st.button(
        "Apply Manual Edits",
        key="apply_manual_edits_button",
    ):
        st.session_state.edited_data = edited_data

        reset_after_manual_edit()

        st.success(
            "Manual edits applied successfully."
        )

        st.rerun()


def render_final_verification():
    edited_data = st.session_state.get(
        "edited_data"
    )

    if not edited_data:
        return

    st.divider()

    st.header("✅ Final Verification")

    st.write(
        "Confirm that the information below is correct "
        "before saving it permanently to the database."
    )

    final_data = {}

    for field in EXTRACTION_FIELDS:
        value = edited_data.get(field)

        if value is None:
            value = ""

        final_data[field] = st.text_input(
            field,
            value=str(value),
            key=f"final_verification_{field}",
        )

    st.session_state.final_data = final_data

    confirmation = st.checkbox(
        "I have reviewed and verified this record "
        "and confirm that it is ready to be saved.",
        key="final_confirmation_checkbox",
    )

    if st.button(
        "💾 Confirm & Save Record",
        type="primary",
        key="confirm_save_record_button",
    ):
        if not confirmation:
            st.warning(
                "Please confirm that you have reviewed "
                "and verified the record before saving."
            )

            return

        try:
            normalized_data = normalize_record(
                final_data
            )

            database = DatabaseManager()

            access_token = st.session_state.get(
                "access_token"
            )

            refresh_token = st.session_state.get(
                "refresh_token"
            )

            database.set_user_session(
                access_token,
                refresh_token,
            )

            saved_record = database.insert_credential(
                normalized_data,
                document_filename=(
                    st.session_state.get(
                        "processed_pdf_name"
                    )
                ),
            )

            st.session_state.verified_data = (
                normalized_data
            )

            st.session_state.final_confirmation = True

            st.success(
                "✓ Record verified and saved successfully "
                "to the Supabase database."
            )

            st.info(
                "Database Record ID: "
                f"{saved_record['id']}"
            )

            # ------------------------------------------------
            # Determine whether another PDF is available.
            # ------------------------------------------------

            current_index = st.session_state.get(
                "selected_pdf_index",
                0,
            )

            total_files = st.session_state.get(
                "uploaded_file_count",
                1,
            )

            if current_index + 1 < total_files:

                st.success(
                    "This document is complete. "
                    "You can continue with the next PDF."
                )

                if st.button(
                    "➡️ Process Next PDF",
                    type="primary",
                    key="process_next_pdf_button",
                ):
                    st.session_state.advance_to_next_pdf = (
                        True
                    )

                    st.rerun()

            else:

                st.success(
                    "🎉 All selected PDFs have been "
                    "processed and verified."
                )

                st.info(
                    "You can now load your records and "
                    "download the Excel export."
                )

        except Exception as exc:
            st.error(
                f"Unable to save the record: {exc}"
            )


def render_review_ui():
    render_manual_review()
    render_final_verification()
```
