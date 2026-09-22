import os
import pandas as pd
import streamlit as st
from utils.excel_manager import SchemaManager, build_default_template
from utils.gemini_extractor import GeminiExtractor
from utils.validation import DocumentValidator
from utils.correction_agent import apply_nlp_correction

st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide",
)

TEMPLATE_PATH = os.path.join("config", "master_template.xlsx")


@st.cache_resource
def load_schema():
    """Ensures master template exists, then loads and validates schema."""
    if not os.path.exists(TEMPLATE_PATH):
        build_default_template(TEMPLATE_PATH)
    return SchemaManager(TEMPLATE_PATH)


# --- UI HEADER ---
st.title("📄 Credential Extraction Assistant")
st.caption("Phase 6 — Human-in-the-Loop & Natural-Language Corrections")

st.divider()

# --- SCHEMA ENGINE INITIALIZATION ---
try:
    schema = load_schema()
except Exception as err:
    st.error(f"❌ Failed to load Excel Schema: {err}")
    st.stop()

# --- DOCUMENT EXTRACTION INTERFACE ---
st.subheader("📤 Upload Document for Extraction")
uploaded_file = st.file_uploader(
    "Choose a PDF document", type=["pdf"], help="Upload official correspondence or credential PDFs"
)

if uploaded_file:
    pdf_bytes = uploaded_file.getvalue()

    # Pre-Flight Validation
    is_valid, validation_msg = DocumentValidator.validate_pdf(
        pdf_bytes, uploaded_file.name
    )

    if not is_valid:
        st.error(f"🚫 Pre-Flight Validation Failed: {validation_msg}")
    else:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.success("✅ Pre-flight checks passed")
            st.info(f"**File Name:** {uploaded_file.name}")
            st.info(f"**File Size:** {uploaded_file.size / 1024:.1f} KB")

            extract_btn = st.button("🚀 Extract Metadata with Gemini", type="primary", use_container_width=True)

        if extract_btn:
            with st.spinner("Analyzing document with Gemini AI..."):
                try:
                    extractor = GeminiExtractor()
                    extracted_data = extractor.extract_from_pdf(
                        pdf_bytes=pdf_bytes,
                        target_fields=schema.extraction_fields,
                    )

                    st.session_state["last_extraction"] = extracted_data
                    st.success("✅ Extraction completed successfully!")

                except Exception as e:
                    st.error(f"❌ Extraction Error: {str(e)}")

# --- HUMAN-IN-THE-LOOP VERIFICATION FORM ---
if "last_extraction" in st.session_state:
    st.divider()
    st.subheader("✏️ Human-in-the-Loop Verification Workspace")
    st.caption("Review, edit, or complete extracted metadata prior to database insertion.")

    raw_extracted = st.session_state["last_extraction"]

    with st.form("verification_form"):
        updated_data = {}
        
        # Display editable fields in a clean 2-column grid
        fields = list(raw_extracted.keys())
        for i in range(0, len(fields), 2):
            c1, c2 = st.columns(2)
            
            # Column 1 Field
            f1 = fields[i]
            val1 = raw_extracted.get(f1) or ""
            updated_data[f1] = c1.text_input(label=f1, value=str(val1))
            
            # Column 2 Field (if available)
            if i + 1 < len(fields):
                f2 = fields[i + 1]
                val2 = raw_extracted.get(f2) or ""
                updated_data[f2] = c2.text_input(label=f2, value=str(val2))

        st.markdown("---")
        save_btn = st.form_submit_button("💾 Save & Confirm Record", type="primary", use_container_width=True)

        if save_btn:
            st.session_state["confirmed_record"] = updated_data
            st.success("✅ Record verified and ready for database staging!")

    # --- NATURAL-LANGUAGE CORRECTIONS SECTION ---
    st.divider()
    st.subheader("💬 Natural-Language Corrections")
    st.caption("Type an instruction to dynamically adjust extracted metadata (e.g., 'Set Approved by to Managing Director').")

    correction_input = st.text_input(
        "Enter instruction:", 
        key="nlp_input", 
        placeholder="e.g., Update Amount to 500,000"
    )

    if st.button("✨ Apply Correction", use_container_width=True):
        if correction_input.strip():
            with st.spinner("Applying AI natural-language corrections..."):
                try:
                    expected_fields = list(st.session_state["last_extraction"].keys())
                    
                    # Call Gemini correction engine
                    updated_fields = apply_nlp_correction(
                        current_data=st.session_state["last_extraction"],
                        user_instruction=correction_input,
                        expected_fields=expected_fields
                    )
                    
                    # Update session state & refresh UI
                    st.session_state["last_extraction"] = updated_fields
                    st.success("Fields updated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to apply correction: {str(e)}")
        else:
            st.warning("Please enter a valid correction instruction.")

# --- DISPLAY CONFIRMED RECORD ---
if "confirmed_record" in st.session_state:
    st.divider()
    st.subheader("📋 Verified Record Output")
    st.dataframe(
        pd.DataFrame([st.session_state["confirmed_record"]]),
        use_container_width=True,
    )

# --- SIDEBAR WORKSPACE STATUS ---
with st.sidebar:
    st.markdown("## 📊 My Database")
    st.info("Supabase authentication and persistent database will be connected in Phase 7 & 8.")
    st.metric("Confirmed Records", "1" if "confirmed_record" in st.session_state else "0")
    st.divider()
    st.write("Version: `0.6.0`")
