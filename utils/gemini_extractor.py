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
    """Create and return the Gemini client."""

    api_key = (
        st.secrets.get("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(api_key=api_key)


def get_available_models(client):
    """Return supported priority Gemini models."""

    available_models = []

    try:
        models = client.models.list()

        for model in models:
            model_name = model.name.replace("models/", "")

            supported_methods = getattr(
                model,
                "supported_actions",
                []
            )

            if (
                model_name in MODEL_PRIORITY
                and (
                    not supported_methods
                    or "generateContent" in supported_methods
                )
            ):
                available_models.append(model_name)

    except Exception as exc:
        raise RuntimeError(
            f"Unable to check Gemini model availability: {exc}"
        ) from exc

    ordered_models = [
        model
        for model in MODEL_PRIORITY
        if model in available_models
    ]

    return ordered_models


def get_gemini_model():
    """Return configured Gemini model name."""

    return (
        st.secrets.get("GEMINI_MODEL")
        or os.environ.get("GEMINI_MODEL")
        or "gemini-3.8-flash"
    )


def test_gemini_connection():
    """Test Gemini connectivity with fallback and retries."""

    client = get_gemini_client()
    available_models = get_available_models(client)

    if not available_models:
        raise RuntimeError(
            "None of the configured Gemini models are currently available."
        )

    errors = []

    for model_name in available_models:

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents="Reply with exactly: Gemini connection successful.",
                )

                if response.text:
                    return response.text

            except Exception as exc:
                errors.append(
                    f"{model_name} attempt {attempt}: {exc}"
                )

                if attempt < MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        "Gemini connection failed after all model/retry attempts.\n"
        + "\n".join(errors)
    )


def extract_structured_data(document_text):
    """Extract the required fields from document text."""

    if not document_text or not document_text.strip():
        raise ValueError(
            "No document text was provided."
        )

    client = get_gemini_client()
    available_models = get_available_models(client)

    if not available_models:
        raise RuntimeError(
            "None of the configured Gemini models are currently available."
        )

    properties = {}

    for field in EXTRACTION_FIELDS:
        properties[field] = {
            "type": "string"
        }

    schema = {
        "type": "object",
        "properties": properties,
        "required": EXTRACTION_FIELDS,
    }

    prompt = f"""
You are a professional document credential extraction system.

Extract the required information from the document below.

IMPORTANT RULES:
1. Return ONLY structured JSON.
2. Use exactly the requested fields.
3. Do not create additional fields.
4. Do not extract "Sr. No.".
5. If a value is not present, return an empty string.
6. Preserve document numbers exactly.
7. Preserve dates as written in the document.
8. Preserve amounts accurately, including currency.
9. Do not guess missing information.

Required fields:
{EXTRACTION_FIELDS}

Document:
----------------
{document_text}
----------------
"""

    errors = []

    for model_name in available_models:

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )

                if response.text:
                    return response.text

                raise ValueError(
                    "Gemini returned an empty response."
                )

            except Exception as exc:
                errors.append(
                    f"{model_name} attempt {attempt}: {exc}"
                )

                if attempt < MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        "Structured Gemini extraction failed after all "
        "model/retry attempts.\n"
        + "\n".join(errors)
    )


def extract_text_from_image(image_bytes, mime_type="image/png"):
    """
    Extract readable text from a scanned document page
    using Gemini Vision.
    """

    if not image_bytes:
        raise ValueError(
            "No image data was provided for OCR."
        )

    client = get_gemini_client()
    available_models = get_available_models(client)

    if not available_models:
        raise RuntimeError(
            "None of the configured Gemini models are currently available."
        )

    prompt = """
You are an OCR system processing a scanned business document.

Read the document image carefully and transcribe all visible text.

Rules:
1. Preserve the original wording as accurately as possible.
2. Preserve names, contract numbers, document numbers,
   dates and amounts exactly.
3. Do not summarize.
4. Do not interpret or invent missing information.
5. Preserve useful headings and labels.
6. Return plain text only.
"""

    errors = []

    for model_name in available_models:

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):

            try:
                image_part = types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        image_part,
                        prompt,
                    ],
                )

                if response.text:
                    return response.text

                raise ValueError(
                    "Gemini OCR returned an empty response."
                )

            except Exception as exc:
                errors.append(
                    f"{model_name} attempt {attempt}: {exc}"
                )

                if attempt < MAX_ATTEMPTS_PER_MODEL:
                    time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(
        "Gemini OCR failed after all model/retry attempts.\n"
        + "\n".join(errors)
    )
