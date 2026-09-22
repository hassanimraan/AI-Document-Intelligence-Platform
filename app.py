import os
import pandas as pd
import streamlit as st
from utils.excel_manager import SchemaManager, build_default_template
from utils.gemini_extractor import GeminiExtractor

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
st.caption("Phase 3 — Gemini API Multi-Modal Extraction Engine")

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
    col1, col2 = st.columns([1, 2])

    with col1:
        st.info(f"**File Name:** {uploaded_file.name}")
        st.info(f"**File Size:** {uploaded_file.size / 1024:.1f} KB")

        extract_btn = st.button("🚀 Extract Metadata with Gemini", type="primary", use_container_width=True)

    if extract_btn:
        with st.spinner("Analyzing document with Gemini AI..."):
            try:
                # Read raw PDF bytes
                pdf_bytes = uploaded_file.getvalue()

                # Initialize extractor and execute extraction targeting active schema fields
                extractor = GeminiExtractor()
                extracted_data = extractor.extract_from_pdf(
                    pdf_bytes=pdf_bytes,
                    target_fields=schema.extraction_fields,
                )

                st.session_state["last_extraction"] = extracted_data
                st.success("✅ Extraction completed successfully!")

            except Exception as e:
                st.error(f"❌ Extraction Error: {str(e)}")

# --- DISPLAY EXTRACTION RESULTS ---
if "last_extraction" in st.session_state:
    st.divider()
    st.subheader("🔍 Extracted Record Preview")

    extracted_dict = st.session_state["last_extraction"]

    # Convert dictionary to formatted DataFrame for review
    preview_df = pd.DataFrame(
        [
            {
                "Target Field": k,
                "Extracted Value": v if v is not None else "— (Not Found)",
            }
            for k, v in extracted_dict.items()
        ]
    )

    st.dataframe(preview_df, use_container_width=True)

    with st.expander("📄 View Raw JSON Payload"):
        st.json(extracted_dict)

# --- SIDEBAR WORKSPACE STATUS ---
with st.sidebar:
    st.markdown("## 📊 My Database")
    st.info("Supabase authentication and persistent database will be connected in Phase 7 & 8.")
    st.metric("Confirmed Records", "0")
    st.divider()
    st.write("Version: `0.3.0`")
