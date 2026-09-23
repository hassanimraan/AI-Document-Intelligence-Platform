import streamlit as st

from utils.validation import validate_pdf
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import extract_structured_data


st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Credential Extraction Assistant")

st.info("Phase 4 — PDF Extraction Test")

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"]
)

if uploaded_file:

    st.write(f"**File:** {uploaded_file.name}")

    if st.button("Process PDF", type="primary"):

        try:
            # Step 1 — Validate
            validate_pdf(uploaded_file)
            st.success("✓ PDF validation successful.")

            # Step 2 — Extract text
            with st.spinner("Extracting PDF text..."):
                document_text = extract_text_from_pdf(
                    uploaded_file
                )

            st.success("✓ PDF text extraction successful.")

            with st.expander("View extracted text"):
                st.text(document_text)

            # Step 3 — Gemini extraction
            with st.spinner("Gemini is analyzing the document..."):
                result = extract_structured_data(
                    document_text
                )

            st.success("✓ Gemini extraction successful.")

            st.markdown("### Extracted Data")
            st.json(result)

        except Exception as e:
            st.error(f"Processing failed: {e}")
