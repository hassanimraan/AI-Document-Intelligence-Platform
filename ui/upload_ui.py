import json

import streamlit as st

from utils.validation import validate_pdf
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import extract_structured_data

from ui.common import (
    reset_current_document_workflow,
    reset_after_new_extraction,
)


def render_upload_ui():
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

    if not uploaded_files:
        return

    # Store the number of uploaded documents so that
    # the review module can determine whether another
    # document is available.
    st.session_state.uploaded_file_count = len(
        uploaded_files
    )

    current_file_names = [
        file.name
        for file in uploaded_files
    ]

    previous_file_names = st.session_state.get(
        "selected_file_names"
    )

    if previous_file_names != current_file_names:
        st.session_state.selected_file_names = (
            current_file_names
        )

        st.session_state.selected_pdf_index = 0

        st.session_state.processing_complete = False

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

            st.session_state.processing_complete = False

            reset_current_document_workflow()

        else:
            st.session_state.processing_complete = True

            reset_current_document_workflow()

    # --------------------------------------------------------
    # Document selector
    # --------------------------------------------------------

    file_options = [
        file.name
        for file in uploaded_files
    ]

    selected_index = st.selectbox(
        "Select PDF to process",
        options=range(len(uploaded_files)),
        format_func=lambda index: file_options[index],
        index=st.session_state.get(
            "selected_pdf_index",
            0,
        ),
        key="active_pdf_selector",
    )

    previous_index = st.session_state.get(
        "selected_pdf_index",
        0,
    )

    if selected_index != previous_index:
        st.session_state.selected_pdf_index = (
            selected_index
        )

        st.session_state.processing_complete = False

        reset_current_document_workflow()

    else:
        st.session_state.selected_pdf_index = (
            selected_index
        )

    current_file = uploaded_files[selected_index]

    # --------------------------------------------------------
    # Progress information
    # --------------------------------------------------------

    total_files = len(uploaded_files)

    display_number = selected_index + 1

    st.info(
        f"📄 Document {display_number} of {total_files}: "
        f"**{current_file.name}**"
    )

    # --------------------------------------------------------
    # Processing progress
    # --------------------------------------------------------

    if total_files > 1:
        st.progress(
            display_number / total_files
        )

        st.caption(
            f"Processing queue: {display_number} / "
            f"{total_files} documents"
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
            validate_pdf(current_file)

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

            if isinstance(extracted_data, str):
                extracted_data = json.loads(
                    extracted_data
                )

            if not isinstance(
                extracted_data,
                dict,
            ):
                raise ValueError(
                    "Gemini returned an invalid extraction format."
                )

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
                f"PDF processed successfully: "
                f"{current_file.name}"
            )

            st.rerun()

        except json.JSONDecodeError:
            st.error(
                "Gemini returned data that could not "
                "be interpreted as valid JSON."
            )

        except Exception as exc:
            st.error(
                f"PDF processing failed: {exc}"
            )

    # --------------------------------------------------------
    # Extracted text
    # --------------------------------------------------------

    if st.session_state.get(
        "extracted_text"
    ):
        st.divider()

        with st.expander(
            "📄 View Extracted Text",
            expanded=False,
        ):
            st.text(
                st.session_state.extracted_text
            )
