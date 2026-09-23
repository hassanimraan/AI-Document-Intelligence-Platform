import streamlit as st

from utils.gemini_extractor import test_gemini_connection


st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Credential Extraction Assistant")

st.info("Phase 3 — Gemini Integration Test")

st.write(
    "This test only verifies that the application can connect "
    "to the configured Gemini API."
)

if st.button("Test Gemini Connection", type="primary"):
    try:
        with st.spinner("Connecting to Gemini..."):
            result = test_gemini_connection()

        st.success("✓ Gemini connection successful.")
        st.code(result)

    except Exception as e:
        st.error(f"Gemini connection failed: {e}")
