import json

import streamlit as st

from config.schema import EXTRACTION_FIELDS
from utils.gemini_extractor import apply_natural_language_correction

from ui.common import reset_after_ai_correction


# ============================================================
# NATURAL-LANGUAGE CORRECTION
# ============================================================

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

    st.header("🤖 Natural-Language Correction")

    st.write(
        "You can describe a correction in plain language. "
        "Gemini will apply the requested change to the "
        "extracted record."
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

            # ------------------------------------------------
            # PARSE JSON IF NECESSARY
            # ------------------------------------------------

            if isinstance(
                corrected_data,
                str,
            ):

                corrected_data = json.loads(
                    corrected_data
                )

            if not isinstance(
                corrected_data,
                dict,
            ):

                raise ValueError(
                    "Gemini returned an invalid correction format."
                )

            # ------------------------------------------------
            # KEEP ONLY EXPECTED FIELDS
            # ------------------------------------------------

            cleaned_data = {
                field: corrected_data.get(field)
                for field in EXTRACTION_FIELDS
            }

            st.session_state.corrected_data = (
                cleaned_data
            )

            reset_after_ai_correction()

            # Restore corrected data after downstream reset.
            st.session_state.corrected_data = (
                cleaned_data
            )

            st.success(
                "AI correction applied successfully."
            )

            st.rerun()

        except json.JSONDecodeError:

            st.error(
                "Gemini returned correction data that "
                "could not be interpreted as valid JSON."
            )

        except Exception as exc:

            st.error(
                f"AI correction failed: {exc}"
            )

    # --------------------------------------------------------
    # SHOW CORRECTED DATA
    # --------------------------------------------------------

    corrected_data = st.session_state.get(
        "corrected_data"
    )

    if not corrected_data:
        return

    st.subheader("🔎 Corrected Data")

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

        st.session_state.edited_data = (
            corrected_data.copy()
        )

        st.session_state.corrected_data = None

        reset_after_ai_correction()

        st.session_state.edited_data = (
            corrected_data.copy()
        )

        st.success(
            "Corrected data has been applied. "
            "Please review it in the final verification section."
        )

        st.rerun()
