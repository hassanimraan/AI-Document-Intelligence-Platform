import os

import streamlit as st
from google import genai
from google.genai import types

from config.schema import EXTRACTION_FIELDS


def get_gemini_client():
    """Create and return the Gemini API client."""

    api_key = (
        st.secrets.get("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(api_key=api_key)


def get_gemini_model():
    """Return the configured Gemini model."""

    return (
        st.secrets.get("GEMINI_MODEL")
        or os.environ.get("GEMINI_MODEL")
        or "gemini-3.8-flash"
    )


def test_gemini_connection():
    """Test the Gemini API connection."""

    client = get_gemini_client()
    model = get_gemini_model()

    response = client.models.generate_content(
        model=model,
        contents="Reply with exactly: GEMINI CONNECTION OK",
    )

    return response.text.strip()


def extract_structured_data(document_text):
    """
    Extract structured credential data from document text.

    PDF processing/OCR will be added in a later phase.
    """

    client = get_gemini_client()
    model = get_gemini_model()

    properties = {
        field: {
            "type": "string",
            "description": (
                f"Extract the value for '{field}' "
                "only when supported by the document."
            ),
        }
        for field in EXTRACTION_FIELDS
    }

    schema = {
    "type": "object",
    "properties": properties,
    "required": EXTRACTION_FIELDS,
    }
    }

    prompt = f"""
You are a document data extraction assistant.

Analyze the supplied document text and extract information
for the following fields:

{EXTRACTION_FIELDS}

Rules:
1. Extract only information supported by the document.
2. Never invent or guess information.
3. If a field is unavailable, return an empty string.
4. Preserve names, numbers, dates and document identifiers accurately.
5. Return only the requested fields.
6. Do not create additional fields.

DOCUMENT TEXT:
{document_text}
"""

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text
