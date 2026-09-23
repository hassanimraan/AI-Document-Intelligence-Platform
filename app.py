import streamlit as st

from utils.excel_manager import ExcelManager
from utils.validation import validate_schema


st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)


st.markdown("## 📄 Credential Extraction Assistant")
st.write("Production-grade document extraction and persistent personal database.")

st.info("Phase 2 — Master Excel Schema + Dynamic Column Engine")


# ---------------------------------------------------------
# PHASE 2 SCHEMA TEST
# ---------------------------------------------------------

try:
    validate_schema()

    excel_manager = ExcelManager()

    master_headers = excel_manager.get_headers()
    extraction_headers = excel_manager.get_extraction_headers()

    st.success("✓ Schema loaded and validated successfully.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Master Excel Schema")
        for number, field in enumerate(master_headers, start=1):
            st.write(f"{number}. `{field}`")

    with col2:
        st.markdown("### Gemini Extraction Fields")
        for number, field in enumerate(extraction_headers, start=1):
            st.write(f"{number}. `{field}`")

    st.info(
        f"Master fields: {len(master_headers)}  |  "
        f"Extraction fields: {len(extraction_headers)}"
    )

    # Test record
    test_record = {
        "Client (PMA)": "Test Client",
        "System (LMBS, PMBS, MMBS, OLMRTS)": "OLMRTS",
        "Contract": "TEST-001",
        "Document Type": "Payment Certificate",
        "Document Number": "PC-001",
        "Date of Issuance": "23 September 2026",
        "Amount": 1000000,
        "Initiated By": "Test Initiator",
        "Reviewed By": "Test Reviewer",
        "Approved by": "Test Approver",
    }

    excel_manager.validate_record(test_record)

    st.success("✓ Test record passed validation.")

    test_df = excel_manager.create_dataframe([test_record])

    st.markdown("### Generated DataFrame")
    st.dataframe(test_df, use_container_width=True)

except Exception as e:
    st.error(f"Schema test failed: {e}")


st.divider()

st.markdown("### Current Project Status")
st.write("Phase 2 testing — Gemini and Supabase are not connected yet.")
