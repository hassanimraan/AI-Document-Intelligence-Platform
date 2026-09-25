import streamlit as st

from config.schema import EXTRACTION_FIELDS
from utils.validation import normalize_record
from utils.database import DatabaseManager

from ui.common import reset_after_manual_edit


def _render_record_fields(
    data,
    key_prefix,
):
    """Render editable fields using the locked extraction schema."""

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Record data must be a dictionary."
        )

    edited_data = {}

    for field in EXTRACTION_FIELDS:

        value = data.get(
            field
        )

        if value is None:
            value = ""

        edited_data[field] = st.text_input(
            field,
            value=str(value),
            key=f"{key_prefix}_{field}",
        )

    return edited_data


def _validate_record_fields(record):
    """Normalize and validate a record before saving."""

    if not isinstance(
        record,
        dict,
    ):
        raise ValueError(
            "The record is not in a valid format."
        )

    expected_fields = set(
        EXTRACTION_FIELDS
    )

    actual_fields = set(
        record.keys()
    )

    missing_fields = (
        expected_fields - actual_fields
    )

    unexpected_fields = (
        actual_fields - expected_fields
    )

    if missing_fields:

        raise ValueError(
            "The record is missing required fields: "
            f"{sorted(missing_fields)}"
        )

    if unexpected_fields:

        raise ValueError(
            "The record contains unexpected fields: "
            f"{sorted(unexpected_fields)}"
        )

    return normalize_record(
        {
            field: record.get(field)
            for field in EXTRACTION_FIELDS
        }
    )


def _get_current_file_progress():
    """Return current PDF position and total queue size."""

    current_index = st.session_state.get(
        "selected_pdf_index",
        0,
    )

    total_files = st.session_state.get(
        "uploaded_file_count",
        1,
    )

    if not isinstance(
        current_index,
        int,
    ):
        current_index = 0

    if (
        not isinstance(
            total_files,
            int,
        )
        or total_files < 1
    ):
        total_files = 1

    current_index = max(
        0,
        min(
            current_index,
            total_files - 1,
        ),
    )

    return (
        current_index,
        total_files,
    )


def _is_current_document_workflow():
    """
    Verify that the current review state belongs to the
    currently selected uploaded PDF.

    Filename alone is intentionally not used because two
    different PDFs may have the same filename.
    """

    current_signature = (
        st.session_state.get(
            "current_file_signature"
        )
    )

    processed_signature = (
        st.session_state.get(
            "processed_file_signature"
        )
    )

    return (
        current_signature is not None
        and processed_signature is not None
        and current_signature
        == processed_signature
    )


def render_manual_review():
    """Render the human review/editing stage."""

    extracted_data = st.session_state.get(
        "extracted_data"
    )

    if not extracted_data:
        return

    if not _is_current_document_workflow():
        return

    st.divider()

    st.header(
        "✏️ Review Extracted Data"
    )

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

        try:

            normalized_data = (
                _validate_record_fields(
                    edited_data
                )
            )

            reset_after_manual_edit()

            st.session_state.edited_data = (
                normalized_data
            )

            st.success(
                "Manual edits applied successfully."
            )

            st.rerun()

        except ValueError as exc:

            st.error(
                f"Manual edits could not be applied: {exc}"
            )

        except Exception:

            st.error(
                "Manual edits could not be applied. "
                "Please review the entered values."
            )


def render_final_verification():
    """Render final verification and permanent database save."""

    edited_data = st.session_state.get(
        "edited_data"
    )

    if not edited_data:
        return

    if not _is_current_document_workflow():
        return

    st.divider()

    st.header(
        "✅ Final Verification"
    )

    st.write(
        "Confirm that the information below is correct "
        "before saving it permanently to the database."
    )

    # ========================================================
    # ALREADY SAVED
    # ========================================================

    if st.session_state.get(
        "final_confirmation",
        False,
    ):

        st.success(
            "This record has already been verified and saved "
            "to the database."
        )

        verified_data = st.session_state.get(
            "verified_data"
        )

        if verified_data:

            for field in EXTRACTION_FIELDS:

                value = verified_data.get(
                    field
                )

                if value is None:
                    value = ""

                st.text_input(
                    field,
                    value=str(value),
                    disabled=True,
                    key=f"verified_display_{field}",
                )

        current_index, total_files = (
            _get_current_file_progress()
        )

        if (
            current_index + 1
            < total_files
        ):

            st.info(
                "This document is complete. "
                "Continue with the next PDF."
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

        return

    # ========================================================
    # FINAL VERIFICATION FIELDS
    # ========================================================

    final_data = {}

    for field in EXTRACTION_FIELDS:

        value = edited_data.get(
            field
        )

        if value is None:
            value = ""

        final_data[field] = st.text_input(
            field,
            value=str(value),
            key=f"final_verification_{field}",
        )

    st.session_state.final_data = (
        final_data
    )

    # ========================================================
    # HUMAN CONFIRMATION
    # ========================================================

    confirmation = st.checkbox(
        "I have reviewed and verified this record "
        "and confirm that it is ready to be saved.",
        key="final_confirmation_checkbox",
    )

    # ========================================================
    # SAVE
    # ========================================================

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

            normalized_data = (
                _validate_record_fields(
                    final_data
                )
            )

            access_token = (
                st.session_state.get(
                    "access_token"
                )
            )

            refresh_token = (
                st.session_state.get(
                    "refresh_token"
                )
            )

            if not access_token:

                raise ValueError(
                    "Your authentication session has expired. "
                    "Please log in again."
                )

            if not refresh_token:

                raise ValueError(
                    "Your authentication session is incomplete. "
                    "Please log in again."
                )

            # ------------------------------------------------
            # Verify that the document being saved is still
            # the document that was actually processed.
            # ------------------------------------------------

            if not _is_current_document_workflow():

                raise ValueError(
                    "The selected PDF no longer matches "
                    "the processed document. Please process "
                    "the selected PDF again before saving."
                )

            database = DatabaseManager()

            database.set_user_session(
                access_token,
                refresh_token,
            )

            processed_pdf_name = (
                st.session_state.get(
                    "processed_pdf_name"
                )
            )

            if not processed_pdf_name:

                raise ValueError(
                    "The processed PDF filename is unavailable."
                )

            saved_record = (
                database.insert_credential(
                    normalized_data,
                    document_filename=(
                        processed_pdf_name
                    ),
                )
            )

            saved_record_id = (
                saved_record.get("id")
                if isinstance(
                    saved_record,
                    dict,
                )
                else None
            )

            if not saved_record_id:

                raise ValueError(
                    "The database did not return "
                    "a valid record ID."
                )

            # ------------------------------------------------
            # Mark the workflow as permanently saved.
            # ------------------------------------------------

            st.session_state.verified_data = (
                normalized_data
            )

            st.session_state.final_confirmation = (
                True
            )

            st.session_state.final_data = (
                normalized_data
            )

            st.success(
                "✓ Record verified and saved successfully "
                "to the Supabase database."
            )

            st.info(
                "Database Record ID: "
                f"{saved_record_id}"
            )

            # ------------------------------------------------
            # Determine whether another PDF exists.
            # ------------------------------------------------

            current_index, total_files = (
                _get_current_file_progress()
            )

            if (
                current_index + 1
                < total_files
            ):

                st.info(
                    "This document is complete. "
                    "Continue with the next PDF."
                )

                if st.button(
                    "➡️ Process Next PDF",
                    type="primary",
                    key="process_next_pdf_after_save_button",
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

        except ValueError as exc:

            st.error(
                f"Unable to save the record: {exc}"
            )

        except Exception:

            st.error(
                "The record could not be saved to the "
                "database. Please try again."
            )


def render_review_ui():
    """Render the complete review and verification workflow."""

    render_manual_review()
    render_final_verification()
