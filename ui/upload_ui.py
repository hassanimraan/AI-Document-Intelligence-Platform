import json

import streamlit as st

from utils.validation import validate_pdf
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import extract_structured_data

from ui.common import (
    reset_current_document_workflow,
    reset_after_new_extraction,
)


# ============================================================
# UPLOAD UI
# ============================================================

def render_upload_ui():
    """
    Render the PDF selection and processing workflow.

    Multiple PDFs may be selected, but only the PDF explicitly
    chosen by the user is processed.
    """

    st.header("📥 Select Credential Documents")

    st.write(
        "You may select multiple PDFs. "
        "Only the PDF you explicitly choose to process "
        "will be sent for extraction."
    )

    # --------------------------------------------------------
    # PDF UPLOADER
    # --------------------------------------------------------

    uploaded_files = st.file_uploader(
        "Select PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        key="credential_pdf_uploader",
    )

    if not uploaded_files:
        return

    # --------------------------------------------------------
    # STORE SELECTED FILE NAMES
    # --------------------------------------------------------

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

        reset_current_document_workflow()

    # --------------------------------------------------------
    # SELECT CURRENT PDF
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

    # --------------------------------------------------------
    # HANDLE PDF SWITCH
    # --------------------------------------------------------

    previous_index = st.session_state.get(
        "selected_pdf_index",
        0,
    )

    if selected_index != previous_index:

        st.session_state.selected_pdf_index = (
            selected_index
        )

        reset_current_document_workflow()

    else:

        st.session_state.selected_pdf_index = (
            selected_index
        )

    current_file = uploaded_files[selected_index]

    # --------------------------------------------------------
    # CURRENT PDF INFORMATION
    # --------------------------------------------------------

    st.info(
        f"Current PDF: **{current_file.name}**"
    )

    # --------------------------------------------------------
    # PROCESS CURRENT PDF
    # --------------------------------------------------------

    if st.button(
        "🔍 Process Current PDF",
        type="primary",
        key="process_current_pdf_button",
    ):

        try:

            # ------------------------------------------------
            # VALIDATE PDF
            # ------------------------------------------------

            validate_pdf(current_file)

            # ------------------------------------------------
            # RESET OLD EXTRACTION WORKFLOW
            # ------------------------------------------------

            reset_after_new_extraction()

            # ------------------------------------------------
            # EXTRACT TEXT / OCR
            # ------------------------------------------------

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

            # ------------------------------------------------
            # GEMINI STRUCTURED EXTRACTION
            # ------------------------------------------------

            with st.spinner(
                "Gemini is extracting credential data..."
            ):

                extracted_data = extract_structured_data(
                    extracted_text
                )

            # ------------------------------------------------
            # PARSE JSON IF NECESSARY
            # ------------------------------------------------

            if isinstance(
                extracted_data,
                str,
            ):

                extracted_data = json.loads(
                    extracted_data
                )

            if not isinstance(
                extracted_data,
                dict,
            ):

                raise ValueError(
                    "Gemini returned an invalid extraction "
                    "format."
                )

            # ------------------------------------------------
            # STORE TEMPORARY WORKFLOW DATA
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
    # SHOW EXTRACTED TEXT
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
