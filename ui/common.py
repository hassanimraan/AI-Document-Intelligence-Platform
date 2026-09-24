import streamlit as st


def reset_current_document_workflow():
    """
    Clear temporary workflow data for the currently
    selected PDF.

    This does NOT delete anything from Supabase.
    It only clears temporary Streamlit session state.
    """

    workflow_keys = [
        "processed_pdf_name",
        "extracted_text",
        "extracted_data",
        "edited_data",
        "corrected_data",
        "final_data",
        "verified_data",
        "final_confirmation",
        "correction_instruction",
    ]

    for key in workflow_keys:
        st.session_state.pop(key, None)


def reset_after_new_extraction():
    """
    Clear workflow stages that belong to an older
    extraction after a new PDF has been processed.
    """

    workflow_keys = [
        "corrected_data",
        "final_data",
        "verified_data",
        "final_confirmation",
        "correction_instruction",
    ]

    for key in workflow_keys:
        st.session_state.pop(key, None)


def reset_after_manual_edit():
    """
    Clear downstream workflow stages after manual
    edits are applied.
    """

    workflow_keys = [
        "corrected_data",
        "final_data",
        "final_confirmation",
    ]

    for key in workflow_keys:
        st.session_state.pop(key, None)


def reset_after_ai_correction():
    """
    Clear final confirmation after an AI correction.
    """

    workflow_keys = [
        "final_data",
        "final_confirmation",
    ]

    for key in workflow_keys:
        st.session_state.pop(key, None)
