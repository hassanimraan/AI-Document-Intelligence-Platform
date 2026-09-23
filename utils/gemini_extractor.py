import os
import time

import streamlit as st
from google import genai
from google.genai import types

from config.schema import EXTRACTION_FIELDS


MODEL_PRIORITY = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

MAX_ATTEMPTS_PER_MODEL = 3
RETRY_DELAY_SECONDS = 2


def get_gemini_client():
    """Create Gemini API client."""

    api_key = (
        st.secrets.get("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    return genai.Client(api_key=api_key)


def get_available_models(client):
    """Return configured models that support generateContent."""

    available = set()

    for model in client.models.list():
        model_name = model.name.replace("models/", "")

        if (
            model_name in MODEL_PRIORITY
            and "generateContent" in (model.supported_actions or [])
        ):
            available.add(model_name)

    return [
        model
        for model in MODEL_PRIORITY
        if model in available
    ]


def get_gemini_model():
    """Return configured/default model."""

    return (
        st.secrets.get("GEMINI_MODEL")
        or os.environ.get("GEMINI_MODEL")
        or "gemini-3.8-flash"
    )


def test_gemini_connection():
    """Test Gemini using available models with fallback."""

    client = get_gemini_client()

    available_models = get_available_models(client)

    if not available_models:
        raise RuntimeError(
            "None of the configured Gemini Flash models are available."
        )

    errors = []

    for model in available_models:

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents="Reply with exactly: GEMINI CONNECTION OK",
                )

                return response.text.strip()

            except Exception as error:
                errors.append(
                    f"{model} attempt {attempt}: {error}"
                )

                if attempt < MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        "All available Gemini models failed.\n\n"
        + "\n".join(errors)
    )


def extract_structured_data(document_text):
    """Extract structured credential data using model fallback."""

    client = get_gemini_client()

    available_models = get_available_models(client)

    if not available_models:
        raise RuntimeError(
            "None of the configured Gemini Flash models are available."
        )

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

    prompt = f"""
You are a document data extraction assistant.

Extract information for these fields:

{EXTRACTION_FIELDS}

Rules:
1. Extract only information supported by the document.
2. Never invent or guess information.
3. If unavailable, return an empty string.
4. Preserve names, numbers, dates and document identifiers accurately.
5. Return only the requested fields.
6. Do not create additional fields.

DOCUMENT TEXT:
{document_text}
"""

    errors = []

    for model in available_models:

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )

                if not response.text:
                    raise ValueError(
                        "Gemini returned an empty response."
                    )

                return response.text

            except Exception as error:
                errors.append(
                    f"{model} attempt {attempt}: {error}"
                )

                if attempt < MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        "All available Gemini models failed.\n\n"
        + "\n".join(errors)
    )
