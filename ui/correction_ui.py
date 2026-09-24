```python
import json

import streamlit as st

from config.schema import EXTRACTION_FIELDS
from utils.gemini_extractor import apply_natural_language_correction
from utils.validation import normalize_record

from ui.common import reset_after_ai_correction


MAX_CORRECTION_INSTRUCTION_LENGTH = 2000


def _validate_correction_result(corrected_data):
    """
    Validate and normalize Gemini's corrected record.

    The correction result must:
    - be a dictionary
    - contain exactly the extraction fields
    - not contain generated fields
    - pass the application's normal record normalization
    """

    if not isinstance(corrected_data, dict):
        raise ValueError(
            "Gemini returned an invalid correction format."
        )

    expected_fields = set(EXTRACTION_FIELDS)
    actual_fields = set(corrected_data.keys())

    missing_fields = expected_fields - actual_fields
    unexpected_fields = actual_fields - expected_fields

    if missing_fields:
        raise ValueError(
            "Gemini correction is missing required fields: "
            f"{sorted(missing_fields)}"
        )

    if unexpected_fields:
        raise ValueError(
            "Gemini correction contains unexpected fields: "
            f"{sorted(unexpected_fields)}"
        )

    cleaned_data = {
        field: corrected_data.get(field)
        for field in EXTRACTION_FIELDS
    }

    return normalize_record(cleaned_data)


def _parse_correction_result(corrected_data):
    """Parse Gemini correction output when it is returned as JSON text."""

    if isinstance(corrected_data, str):

        try:
            corrected_data = json.loads(
                corrected_data
            )

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Gemini returned correction data that "
                "could not be interpreted as valid JSON."
            ) from exc

    return _validate_correction_result(
        corrected_data
    )


def render_correction_ui():
    """
    Render the natural-language AI correction workflow.
    """

    edited_data = st.session_state.get(
        "edited_data"
    )

    if not edited_data:
        return

    st.divider()

    st.header(
        "🤖 Natural-Language Correction"
    )

    st.write(
        "Describe the required correction in plain language. "
        "Gemini will apply the requested change to the "
        "currently reviewed record."
    )

    # --------------------------------------------------------
    # CORRECTION INSTRUCTION
    # --------------------------------------------------------

    correction_instruction = st.text_area(
        "Correction instruction",
        value=st.session_state.get(
            "correction_instruction",
            "",
        ),
        placeholder=(
            "Example: Change the amount to 1,250,000 "
            "and change the document type to Payment Certificate."
        ),
        key="correction_instruction_input",
        height=100,
        max_chars=MAX_CORRECTION_INSTRUCTION_LENGTH,
    )

    st.caption(
        f"Maximum instruction length: "
        f"{MAX_CORRECTION_INSTRUCTION_LENGTH} characters."
    )

    # --------------------------------------------------------
    # APPLY AI CORRECTION
    # --------------------------------------------------------

    if st.button(
        "🤖 Apply AI Correction",
        key="apply_ai_correction_button",
    ):

        instruction = correction_instruction.strip()

        if not instruction:
            st.warning(
                "Please enter a correction instruction."
            )
            return

        if len(instruction) > MAX_CORRECTION_INSTRUCTION_LENGTH:
            st.error(
                "The correction instruction is too long."
            )
            return

        try:
            st.session_state.correction_instruction = (
                instruction
            )

            with st.spinner(
                "Gemini is applying the requested correction..."
            ):
                corrected_data = (
                    apply_natural_language_correction(
                        edited_data,
                        instruction,
                    )
                )

            cleaned_data = _parse_correction_result(
                corrected_data
            )

            # Clear downstream state before storing the
            # newly corrected record.
            reset_after_ai_correction()

            st.session_state.corrected_data = (
                cleaned_data
            )

            st.success(
                "AI correction applied successfully."
            )

            st.rerun()

        except ValueError as exc:

            st.error(
                f"AI correction failed: {exc}"
            )

        except Exception:

            st.error(
                "AI correction could not be completed. "
                "Please try again or make the correction manually."
            )

    # --------------------------------------------------------
    # SHOW CORRECTED DATA
    # --------------------------------------------------------

    corrected_data = st.session_state.get(
        "corrected_data"
    )

    if not corrected_data:
        return

    st.subheader(
        "🔎 Corrected Data"
    )

    for field in EXTRACTION_FIELDS:

        value = corrected_data.get(field)

        if value is None:
            value = ""

        st.text_input(
            field,
            value=str(value),
            disabled=True,
            key=f"corrected_display_{field}",
        )

    # --------------------------------------------------------
    # USE CORRECTED DATA
    # --------------------------------------------------------

    if st.button(
        "Use Corrected Data",
        type="primary",
        key="use_corrected_data_button",
    ):

        final_corrected_data = corrected_data.copy()

        # Clear correction-specific state.
        reset_after_ai_correction()

        # Promote the corrected record to the normal
        # manual-review workflow.
        st.session_state.edited_data = (
            final_corrected_data
        )

        st.session_state.correction_instruction = (
            correction_instruction.strip()
        )

        st.success(
            "Corrected data has been applied. "
            "Please review it in the final verification section."
        )

        st.rerun()
```
