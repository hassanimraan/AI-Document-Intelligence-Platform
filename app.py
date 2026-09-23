import streamlit as st

from utils.gemini_extractor import extract_structured_data


st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Credential Extraction Assistant")

st.info("Phase 3 — Structured Gemini Extraction Test")

sample_text = """
PAYMENT CERTIFICATE

Client (PMA): Punjab Mass Transit Authority
System: OLMRTS
Contract: OLMRTS-2024-017

Document Type: Payment Certificate
Document Number: PC-045
Date of Issuance: 15 August 2026
Amount: PKR 4,250,000

Initiated By: Hafiz Adeel
Reviewed By: Muhammad Usman
Approved by: Ahmed Raza
"""

st.markdown("### Sample Document Text")
st.text_area(
    "Document content",
    sample_text,
    height=300
)

if st.button("Extract Structured Data", type="primary"):
    try:
        with st.spinner("Gemini is extracting data..."):
            result = extract_structured_data(sample_text)

        st.success("✓ Structured extraction successful.")

        st.markdown("### Gemini JSON Output")
        st.json(result)

    except Exception as e:
        st.error(f"Extraction failed: {e}")
