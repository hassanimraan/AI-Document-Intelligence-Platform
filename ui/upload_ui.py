import json

import streamlit as st

from utils.validation import validate_pdf, normalize_record
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import extract_structured_data

from ui.common import (
    reset_current_document_workflow,
    reset_after_new_extraction,
)


def _get_uploaded_file_signature(uploaded_files):
    """
    Create a lightweight signature for the currently selected files.

    File name alone is not sufficient because a user could replace
    a PDF while keeping the same filename.
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
    Parse and validate structured extraction output.

    Gemini's extractor normally returns validated structured data,
    but this function provides a second defensive validation layer
    before data enters the UI workflow.
    """

    if isinstance(extracted_data, str):
        try:
            extracted_data = json.loads(
                extracted_data
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned data that could not "
                "be interpreted as valid JSON."
            ) from exc

    if not isinstance(extracted_data, dict):
        raise ValueError(
            "Gemini returned an invalid extraction format."
        )

    return normalize_record(
        extracted_data
    )


def _reset_for_new_file():
    """Reset temporary state when moving to a different PDF."""

    reset_current_document_workflow()

    st.session_state.processing_complete = False


def render_upload_ui():
    st.header(
        "📥 Select Credential Documents"
    )

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

    if not uploaded_files:
        # Remove stale queue state when the uploader is cleared.
        st.session_state.pop(
            "selected_file_names",
            None,
        )
        st.session_state.pop(
            "selected_pdf_index",
            None,
        )
        st.session_state.pop(
            "uploaded_file_count",
            None,
        )
        st.session_state.pop(
            "processing_complete",
            None,
        )

        return

    # --------------------------------------------------------
    # Upload queue state
    # --------------------------------------------------------

    st.session_state.uploaded_file_count = (
        len(uploaded_files)
    )

    current_file_signature = (
        _get_uploaded_file_signature(
            uploaded_files
        )
    )

    previous_file_signature = (
        st.session_state.get(
            "uploaded_file_signature"
        )
    )

    if (
        previous_file_signature
        != current_file_signature
    ):
        st.session_state.uploaded_file_signature = (
            current_file_signature
        )

        st.session_state.selected_file_names = [
            file.name
            for file in uploaded_files
        ]

        st.session_state.selected_pdf_index = 0

        st.session_state.processing_complete = False

        st.session_state.advance_to_next_pdf = False

        reset_current_document_workflow()

    # --------------------------------------------------------
    # Advance to next PDF after successful save
    # --------------------------------------------------------

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
            st.session_state.selected_pdf_index = (
                next_index
            )

            _reset_for_new_file()

        else:
            st.session_state.processing_complete = True

            reset_current_document_workflow()

    # --------------------------------------------------------
    # Protect against an invalid stored index
    # --------------------------------------------------------

    stored_index = st.session_state.get(
        "selected_pdf_index",
        0,
    )

    if not isinstance(
        stored_index,
        int,
    ):
        stored_index = 0

    stored_index = max(
        0,
        min(
            stored_index,
            len(uploaded_files) - 1,
        ),
    )

    st.session_state.selected_pdf_index = (
        stored_index
    )

    # --------------------------------------------------------
    # Document selector
    # --------------------------------------------------------

    file_options = [
        file.name
        for file in uploaded_files
    ]

    selected_index = st.selectbox(
        "Select PDF to process",
        options=range(
            len(uploaded_files)
        ),
        format_func=lambda index: (
            file_options[index]
        ),
        index=stored_index,
        key="active_pdf_selector",
    )

    if selected_index != stored_index:
        st.session_state.selected_pdf_index = (
            selected_index
        )

        _reset_for_new_file()

    else:
        st.session_state.selected_pdf_index = (
            selected_index
        )

    current_file = uploaded_files[
        selected_index
    ]

    # --------------------------------------------------------
    # Progress information
    # --------------------------------------------------------

    total_files = len(
        uploaded_files
    )

    display_number = (
        selected_index + 1
    )

    st.info(
        f"📄 Document {display_number} of "
        f"{total_files}: **{current_file.name}**"
    )

    if total_files > 1:
        st.progress(
            display_number / total_files
        )

        st.caption(
            f"Processing queue: {display_number} / "
            f"{total_files} documents"
        )

    # --------------------------------------------------------
    # All documents completed
    # --------------------------------------------------------

    if st.session_state.get(
        "processing_complete",
        False,
    ):
        st.success(
            f"All {total_files} selected PDF documents "
            "have been processed and reviewed."
        )

    # --------------------------------------------------------
    # Process current PDF
    # --------------------------------------------------------

    if st.button(
        "🔍 Process Current PDF",
        type="primary",
        key="process_current_pdf_button",
    ):

        try:
            # Validate the uploaded file before any
            # PDF processing or Gemini request.
            validate_pdf(
                current_file
            )

            # Remove downstream state from any previous
            # extraction for this document.
            reset_after_new_extraction()

            with st.spinner(
                "Reading PDF and extracting text..."
            ):
                extracted_text = (
                    extract_text_from_pdf(
                        current_file
                    )
                )

            if not extracted_text:
                raise ValueError(
                    "No readable text was extracted from "
                    "the selected PDF."
                )

            with st.spinner(
                "Gemini is extracting credential data..."
            ):
                extracted_data = (
                    extract_structured_data(
                        extracted_text
                    )
                )

            extracted_data = (
                _parse_extracted_data(
                    extracted_data
                )
            )

            # ------------------------------------------------
            # Store temporary workflow state
            # ------------------------------------------------

            st.session_state.processed_pdf_name = (
                current_file.name
            )

            st.session_state.extracted_text = (
                extracted_text
            )

            st.session_state.extracted_data = (
                extracted_data
            )

            st.session_state.edited_data = (
                extracted_data.copy()
            )

            st.session_state.processing_complete = (
                False
            )

            st.success(
                "PDF processed successfully: "
                f"{current_file.name}"
            )

            st.rerun()

        except ValueError as exc:

            st.error(
                f"PDF processing failed: {exc}"
            )

        except Exception:

            st.error(
                "PDF processing could not be completed. "
                "Please verify the document and try again."
            )

    # --------------------------------------------------------
    # Extracted text
    # --------------------------------------------------------

    extracted_text = st.session_state.get(
        "extracted_text"
    )

    processed_pdf_name = st.session_state.get(
        "processed_pdf_name"
    )

    # Only display extracted text when it belongs to
    # the currently selected document.
    if (
        extracted_text
        and processed_pdf_name == current_file.name
    ):
        st.divider()

        with st.expander(
            "📄 View Extracted Text",
            expanded=False,
        ):
            st.text(
                extracted_text
            )
