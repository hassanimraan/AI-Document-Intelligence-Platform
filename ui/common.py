```python
import streamlit as st


def reset_current_document_workflow():
    """
    Clear temporary workflow data for the currently selected PDF.

    This does NOT delete anything from Supabase.
    It only clears temporary Streamlit session state.
    """

    workflow_keys = [
        "processed_pdf_name",
        "processed_file_signature",
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
        st.session_state.pop(
            key,
            None,
        )


def reset_after_new_extraction():
    """
    Clear workflow stages belonging to an older extraction
    after a new PDF has been successfully processed.
    """

    workflow_keys = [
        "corrected_data",
        "final_data",
        "verified_data",
        "final_confirmation",
        "correction_instruction",
    ]

    for key in workflow_keys:
        st.session_state.pop(
            key,
            None,
        )


def reset_after_manual_edit():
    """
    Clear downstream workflow stages after manual edits.
    """

    workflow_keys = [
        "corrected_data",
        "final_data",
        "verified_data",
        "final_confirmation",
    ]

    for key in workflow_keys:
        st.session_state.pop(
            key,
            None,
        )


def reset_after_ai_correction():
    """
    Clear final-verification state after a new AI correction.

    The corrected data itself is preserved by correction_ui.py
    after this reset.
    """

    workflow_keys = [
        "final_data",
        "verified_data",
        "final_confirmation",
    ]

    for key in workflow_keys:
        st.session_state.pop(
            key,
            None,
        )
```
