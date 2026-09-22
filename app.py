import os
import pandas as pd
import streamlit as st
from utils.excel_manager import SchemaManager

st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)

# Set path to master template configuration
TEMPLATE_PATH = os.path.join("config", "master_template.xlsx")


@st.cache_resource
def load_schema():
    """Reads and validates the master Excel template dynamically."""
    return SchemaManager(TEMPLATE_PATH)


# --- UI HEADER ---
st.title("📄 Credential Extraction Assistant")
st.caption("Phase 2 — Dynamic Master Excel Schema Engine")

st.divider()

# --- SCHEMA ENGINE VERIFICATION ---
try:
    schema = load_schema()
    st.success("✅ Dynamic Master Excel Schema Engine Active")

    # Metrics row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Schema Headers", len(schema.master_headers))
    col2.metric("Gemini Extraction Target Fields", len(schema.extraction_fields))
    col3.metric("App-Generated Fields", len(schema.reserved_fields))

    st.subheader("📋 Detected Master Schema Overview")

    # Table breakdown of header classification
    table_data = []
    for header in schema.master_headers:
        is_reserved = header in schema.reserved_fields
        table_data.append(
            {
                "Header Name": header,
                "Target Classification": (
                    "Application Auto-Increment (Sr. No.)"
                    if is_reserved
                    else "Gemini OCR Target Field"
                ),
                "Gemini Prompt Status": (
                    "Excluded from Prompt"
                    if is_reserved
                    else "Active JSON Key"
                ),
            }
        )

    st.dataframe(pd.DataFrame(table_data), use_container_width=True)

    # Preview Gemini JSON Target Schema
    with st.expander("🔍 Expected Gemini JSON Target Structure"):
        st.json(schema.get_gemini_json_structure())

except Exception as err:
    st.error(f"❌ Failed to load Excel Schema: {err}")

# --- SIDEBAR WORKSPACE STATUS ---
with st.sidebar:
    st.markdown("## 📊 My Database")
    st.info(
        "Supabase authentication and persistent database will be connected in"
        " Phase 7 & 8."
    )
    st.metric("Confirmed Records", "0")
    st.divider()
    st.write("Version: `0.2.0`")