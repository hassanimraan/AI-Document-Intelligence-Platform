import streamlit as st

from config.schema import EXTRACTION_FIELDS

from utils.validation import normalize_record
from utils.database import DatabaseManager

from ui.common import (
    reset_after_manual_edit,
)


# ============================================================
# HELPER
# ============================================================

def _render_record_fields(
    data,
    key_prefix,
):
    """
    Render editable fields for one credential record.

    Returns a dictionary containing the current UI values.
    """

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


# ============================================================
# MANUAL REVIEW
# ============================================================

def render_manual_review():
    """
    Render the human review and manual editing stage.
    """

    extracted_data = st.session_state.get(
        "extracted_data"
    )

    if not extracted_data:
        return

    st.divider()

    st.header("✏️ Review Extracted Data")

    st.write(
        "Review the information extracted by Gemini. "
        "You can correct any field manually before "
        "continuing."
    )

    # --------------------------------------------------------
    # CURRENT EXTRACTED DATA
    # --------------------------------------------------------

    edited_data = _render_record_fields(
        extracted_data,
        "manual_review",
    )

    # --------------------------------------------------------
    # APPLY MANUAL EDITS
    # --------------------------------------------------------

    if st.button(
        "Apply Manual Edits",
        key="apply_manual_edits_button",
    ):

        st.session_state.edited_data = (
            edited_data
        )

        reset_after_manual_edit()

        st.success(
            "Manual edits applied successfully."
        )

        st.rerun()


# ============================================================
# FINAL VERIFICATION
# ============================================================

def render_final_verification():
    """
    Render the final verification and database save stage.
    """

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

    # --------------------------------------------------------
    # SHOW FINAL DATA
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CONFIRMATION
    # --------------------------------------------------------

    confirmation = st.checkbox(
        "I have reviewed and verified this record "
        "and confirm that it is ready to be saved.",
        key="final_confirmation_checkbox",
    )

    # --------------------------------------------------------
    # SAVE TO SUPABASE
    # --------------------------------------------------------

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

            # ------------------------------------------------
            # NORMALIZE DATA
            # ------------------------------------------------

            normalized_data = normalize_record(
                final_data
            )

            # ------------------------------------------------
            # AUTHENTICATED DATABASE SESSION
            # ------------------------------------------------

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

            # ------------------------------------------------
            # SAVE RECORD
            # ------------------------------------------------

            saved_record = (
                database.insert_credential(
                    normalized_data,
                    document_filename=(
                        st.session_state.get(
                            "processed_pdf_name"
                        )
                    ),
                )
            )

            # ------------------------------------------------
            # STORE VERIFIED DATA
            # ------------------------------------------------

            st.session_state.verified_data = (
                normalized_data
            )

            st.success(
                "✓ Record verified and saved successfully "
                "to the Supabase database."
            )

            st.info(
                "Database Record ID: "
                f"{saved_record['id']}"
            )

            st.session_state.final_confirmation = (
                True
            )

            st.write(
                "You can now select another PDF "
                "from the document list above."
            )

        except Exception as exc:

            st.error(
                f"Unable to save the record: {exc}"
            )


# ============================================================
# MAIN REVIEW UI
# ============================================================

def render_review_ui():
    """
    Render the complete human review workflow.
    """

    render_manual_review()

    render_final_verification()
