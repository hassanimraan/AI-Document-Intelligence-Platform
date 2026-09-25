import json

import streamlit as st

from utils.validation import (
    validate_pdf,
    normalize_record,
)
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import extract_structured_data

from ui.common import (
    reset_current_document_workflow,
    reset_after_new_extraction,
)


def _get_uploaded_file_signature(uploaded_files):
    """
    Create a lightweight identity signature for uploaded files.

    Filename + size is used to distinguish files that may share
    the same filename.
    """
    return [
        (
            file.name,
            getattr(file, "size", None),
        )
        for file in uploaded_files
    ]


def _parse_extracted_data(extracted_data):
    """
    Parse and validate Gemini's structured extraction output.
    """
    if isinstance(extracted_data, str):
        try:
            extracted_data = json.loads(extracted_data)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned data that could not "
                "be interpreted as valid JSON."
            ) from exc

    if not isinstance(extracted_data, dict):
        raise ValueError(
            "Gemini returned an invalid extraction format."
        )

    return normalize_record(extracted_data)


def _reset_for_new_file():
    """Reset temporary state when moving to another PDF."""
    reset_current_document_workflow()
    st.session_state.processing_complete = False


def render_upload_ui():
    """Render PDF selection and processing workflow."""

    st.header("📥 Select Credential Documents")

    st.write(
        "Select multiple PDFs and process them one by one. "
        "Each document must be reviewed and verified before "
        "it is permanently saved."
    )

    uploaded_files = st.file_uploader(
        "Select PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        key="credential_pdf_uploader",
    )

    # ========================================================
    # NO FILES SELECTED
    # ========================================================

    if not uploaded_files:
        stale_keys = [
            "selected_file_names",
            "selected_pdf_index",
            "uploaded_file_count",
            "uploaded_file_signature",
            "current_file_signature",
            "processed_file_signature",
            "processing_complete",
        ]

        for key in stale_keys:
            st.session_state.pop(key, None)

        return

    # ========================================================
    # UPLOAD QUEUE STATE
    # ========================================================

    st.session_state.uploaded_file_count = len(uploaded_files)

    current_file_signature = _get_uploaded_file_signature(
        uploaded_files
    )

    previous_file_signature = st.session_state.get(
        "uploaded_file_signature"
    )

    # --------------------------------------------------------
    # Detect a changed upload queue.
    # --------------------------------------------------------

    if previous_file_signature != current_file_signature:
        st.session_state.uploaded_file_signature = (
            current_file_signature
        )

        st.session_state.selected_file_names = [
            file.name for file in uploaded_files
        ]

        st.session_state.selected_pdf_index = 0
        st.session_state.processing_complete = False
        st.session_state.advance_to_next_pdf = False

        st.session_state.pop(
            "current_file_signature",
            None,
        )

        st.session_state.pop(
            "processed_file_signature",
            None,
        )

        reset_current_document_workflow()

    # ========================================================
    # PROTECT STORED INDEX
    # ========================================================

    stored_index = st.session_state.get(
        "selected_pdf_index",
        0,
    )

    if not isinstance(stored_index, int):
        stored_index = 0

    stored_index = max(
        0,
        min(
            stored_index,
            len(uploaded_files) - 1,
        ),
    )

    st.session_state.selected_pdf_index = stored_index

    # ========================================================
    # DOCUMENT SELECTOR
    # ========================================================

    file_options = [
        file.name for file in uploaded_files
    ]

    selected_index = st.selectbox(
        "Select PDF to process",
        options=range(len(uploaded_files)),
        format_func=lambda index: file_options[index],
        index=stored_index,
        key="active_pdf_selector",
    )

    if selected_index != stored_index:
        st.session_state.selected_pdf_index = selected_index
        _reset_for_new_file()
    else:
        st.session_state.selected_pdf_index = selected_index

    current_file = uploaded_files[selected_index]

    # --------------------------------------------------------
    # Identity of the currently selected file.
    # --------------------------------------------------------

    current_file_signature = (
        current_file.name,
        getattr(current_file, "size", None),
    )

    st.session_state.current_file_signature = (
        current_file_signature
    )

    # ========================================================
    # PROGRESS INFORMATION
    # ========================================================

    total_files = len(uploaded_files)
    display_number = selected_index + 1

    st.info(
        f"📄 Document {display_number} of "
        f"{total_files}: **{current_file.name}**"
    )

    if total_files > 1:
        st.progress(display_number / total_files)

        st.caption(
            f"Processing queue: {display_number} / "
            f"{total_files} documents"
        )

    # ========================================================
    # ADVANCE TO NEXT PDF
    # ========================================================

    if st.session_state.get(
        "advance_to_next_pdf",
        False,
    ):
        st.session_state.advance_to_next_pdf = False

        current_index = st.session_state.get(
            "selected_pdf_index",
            0,
        )

        next_index = current_index + 1

        if next_index < len(uploaded_files):
            st.session_state.selected_pdf_index = next_index
            _reset_for_new_file()
        else:
            st.session_state.processing_complete = True

            reset_current_document_workflow()

            st.session_state.pop(
                "processed_file_signature",
                None,
            )

    # ========================================================
    # ALL DOCUMENTS COMPLETED
    # ========================================================

    if st.session_state.get(
        "processing_complete",
        False,
    ):
    
    st.success(
        "PDF processed successfully: "
        f"{current_file.name}"
    )

    st.rerun()

    except ValueError as exc:
        st.error(
            f"PDF processing failed: {exc}"
        )

        except Exception as exc:
            st.error(
                "PDF processing could not be completed."
            )
            st.exception(exc)

    # ========================================================
    # PROCESS CURRENT PDF
    # ========================================================

    if st.button(
        "🔍 Process Current PDF",
        type="primary",
        key="process_current_pdf_button",
    ):
        try:
            # ------------------------------------------------
            # Validate before PDF processing/Gemini.
            # ------------------------------------------------

            validate_pdf(current_file)

            # ------------------------------------------------
            # Clear downstream workflow state.
            # ------------------------------------------------

            reset_after_new_extraction()

            with st.spinner(
                "Reading PDF and extracting text..."
            ):
                extracted_text = extract_text_from_pdf(
                    current_file
                )

            if not extracted_text:
                raise ValueError(
                    "No readable text was extracted from "
                    "the selected PDF."
                )

            with st.spinner(
                "Gemini is extracting credential data..."
            ):
                extracted_data = extract_structured_data(
                    extracted_text
                )

            extracted_data = _parse_extracted_data(
                extracted_data
            )

            # ------------------------------------------------
            # Store temporary workflow state.
            # ------------------------------------------------

            st.session_state.processed_pdf_name = (
                current_file.name
            )

            st.session_state.processed_file_signature = (
                current_file_signature
            )

            st.session_state.extracted_text = extracted_text

            st.session_state.extracted_data = extracted_data

            st.session_state.edited_data = (
                extracted_data.copy()
            )

            st.session_state.processing_complete = False

            st.success(
                "PDF processed successfully: "
                f"{current_file.name}"
            )

            st.rerun()

        except ValueError as exc:
            st.error(
                f"PDF processing failed: {exc}"
            )

                except Exception as exc:
            st.error(
                "PDF processing could not be completed."
            )
            st.exception(exc)

    # ========================================================
    # EXTRACTED TEXT
    # ========================================================

    extracted_text = st.session_state.get(
        "extracted_text"
    )

    processed_file_signature = st.session_state.get(
        "processed_file_signature"
    )

    # --------------------------------------------------------
    # Display extracted text only when it belongs to the
    # currently selected file.
    # --------------------------------------------------------

    if (
        extracted_text
        and processed_file_signature == current_file_signature
    ):
        st.divider()

        with st.expander(
            "📄 View Extracted Text",
            expanded=False,
        ):
            st.text(extracted_text)
