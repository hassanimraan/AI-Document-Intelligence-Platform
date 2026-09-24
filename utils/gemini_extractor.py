import os
import time
import json

import streamlit as st
from google import genai
from google.genai import types

from config.schema import EXTRACTION_FIELDS


# -------------------------------------------------------------------
# Gemini model configuration
# -------------------------------------------------------------------

MODEL_PRIORITY = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

# Maximum number of retries for temporary errors.
# This is deliberately low to prevent unnecessary API usage.
MAX_TRANSIENT_RETRIES = 1

# Initial delay before a controlled retry.
RETRY_DELAY_SECONDS = 2


# -------------------------------------------------------------------
# Gemini client
# -------------------------------------------------------------------

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


# -------------------------------------------------------------------
# Model discovery
# -------------------------------------------------------------------

def get_available_models(client):
    """Return supported priority Gemini models."""

    available_models = []

    try:
        models = client.models.list()

        for model in models:
            model_name = model.name.replace(
                "models/",
                ""
            )

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

    return [
        model
        for model in MODEL_PRIORITY
        if model in available_models
    ]


def get_gemini_model():
    """Return configured Gemini model name."""

    return (
        st.secrets.get("GEMINI_MODEL")
        or os.environ.get("GEMINI_MODEL")
        or "gemini-3.8-flash"
    )


def _get_model_sequence(available_models):
    """
    Build a controlled model sequence.

    The configured model is attempted first, followed by the
    remaining priority models.

    Model fallback is only used when the current model is
    unavailable or temporarily unavailable. It is NOT used
    after a daily quota exhaustion.
    """

    configured_model = get_gemini_model()

    ordered_models = []

    if configured_model in available_models:
        ordered_models.append(configured_model)

    for model_name in available_models:
        if model_name not in ordered_models:
            ordered_models.append(model_name)

    return ordered_models


# -------------------------------------------------------------------
# Error classification
# -------------------------------------------------------------------

def _get_exception_status_code(exc):
    """
    Attempt to retrieve an HTTP/status code from a Gemini exception.
    """

    for attribute in (
        "status_code",
        "code",
        "http_status",
    ):
        value = getattr(exc, attribute, None)

        if isinstance(value, int):
            return value

    return None


def _classify_gemini_error(exc):
    """
    Classify a Gemini exception into a controlled application
    action.

    Possible actions:

    - quota_exhausted
    - rate_limit
    - service_unavailable
    - not_found
    - bad_request
    - authentication
    - permission
    - server_error
    - other
    """

    message = str(exc).lower()

    status_code = _get_exception_status_code(exc)

    # ---------------------------------------------------------------
    # Daily quota exhaustion
    # ---------------------------------------------------------------

    if (
        "quota exceeded" in message
        or "quota_exceeded" in message
        or "generate_content_free_tier_requests" in message
        or "daily quota" in message
        or "daily limit" in message
    ):
        return "quota_exhausted"

    # ---------------------------------------------------------------
    # HTTP 429
    # ---------------------------------------------------------------

    if status_code == 429:
        if (
            "quota" in message
            or "daily" in message
            or "resource_exhausted" in message
        ):
            return "quota_exhausted"

        return "rate_limit"

    # Some SDK versions may not expose status_code directly.
    if (
        "429" in message
        and (
            "rate limit" in message
            or "too many requests" in message
        )
    ):
        return "rate_limit"

    # ---------------------------------------------------------------
    # HTTP 503
    # ---------------------------------------------------------------

    if status_code == 503:
        return "service_unavailable"

    if (
        "503" in message
        or "service unavailable" in message
        or "temporarily unavailable" in message
        or "high demand" in message
    ):
        return "service_unavailable"

    # ---------------------------------------------------------------
    # HTTP 404 / model unavailable
    # ---------------------------------------------------------------

    if status_code == 404:
        return "not_found"

    if (
        "404" in message
        or "not found" in message
        or "model not found" in message
    ):
        return "not_found"

    # ---------------------------------------------------------------
    # HTTP 400
    # ---------------------------------------------------------------

    if status_code == 400:
        return "bad_request"

    if (
        "400" in message
        or "invalid argument" in message
        or "invalid request" in message
        or "bad request" in message
        or "schema" in message
    ):
        return "bad_request"

    # ---------------------------------------------------------------
    # HTTP 401
    # ---------------------------------------------------------------

    if status_code == 401:
        return "authentication"

    if (
        "401" in message
        or "unauthorized" in message
        or "api key" in message
    ):
        return "authentication"

    # ---------------------------------------------------------------
    # HTTP 403
    # ---------------------------------------------------------------

    if status_code == 403:
        return "permission"

    if (
        "403" in message
        or "permission denied" in message
        or "forbidden" in message
    ):
        return "permission"

    # ---------------------------------------------------------------
    # HTTP 500 / 504
    # ---------------------------------------------------------------

    if status_code in (500, 504):
        return "server_error"

    if (
        "500" in message
        or "internal server error" in message
        or "504" in message
        or "deadline exceeded" in message
        or "timeout" in message
    ):
        return "server_error"

    return "other"


# -------------------------------------------------------------------
# Error messages
# -------------------------------------------------------------------

def _build_quota_error_message():
    """Return a user-friendly daily quota message."""

    return (
        "Gemini daily quota has been reached. "
        "No additional Gemini requests will be attempted. "
        "Please try again after the quota resets or "
        "update the Gemini API usage/billing tier."
    )


def _build_failure_message(operation, errors):
    """Build a concise technical failure message."""

    details = "\n".join(errors)

    return (
        f"{operation} failed.\n\n"
        f"Gemini request details:\n"
        f"{details}"
    )


# -------------------------------------------------------------------
# Generic controlled Gemini request runner
# -------------------------------------------------------------------

def _generate_content_with_policy(
    client,
    model_sequence,
    contents,
    config=None,
    operation="Gemini request",
):
    """
    Execute a Gemini generation request using a controlled
    API usage policy.

    IMPORTANT:

    This function intentionally does NOT perform the old
    model × retry multiplication.

    Daily quota exhaustion stops immediately.

    Temporary rate limits get one retry.

    Temporary service errors get one retry before moving
    to the next available model.

    Model-not-found errors move directly to the next model.
    """

    if not model_sequence:
        raise RuntimeError(
            "No Gemini models are available."
        )

    errors = []

    for model_name in model_sequence:

        transient_retry_count = 0

        while True:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )

                if not getattr(response, "text", None):
                    raise ValueError(
                        "Gemini returned an empty response."
                    )

                return response

            except Exception as exc:

                error_type = _classify_gemini_error(exc)

                errors.append(
                    f"{model_name}: {error_type}: {exc}"
                )

                # ---------------------------------------------------
                # DAILY QUOTA
                # ---------------------------------------------------

                if error_type == "quota_exhausted":
                    raise RuntimeError(
                        _build_quota_error_message()
                    ) from exc

                # ---------------------------------------------------
                # AUTHENTICATION
                # ---------------------------------------------------

                if error_type == "authentication":
                    raise RuntimeError(
                        "Gemini authentication failed. "
                        "Please verify the GEMINI_API_KEY."
                    ) from exc

                # ---------------------------------------------------
                # PERMISSION
                # ---------------------------------------------------

                if error_type == "permission":
                    raise RuntimeError(
                        "Gemini API permission was denied. "
                        "Please check the API key and project permissions."
                    ) from exc

                # ---------------------------------------------------
                # INVALID REQUEST
                # ---------------------------------------------------

                if error_type == "bad_request":
                    raise RuntimeError(
                        f"{operation} was rejected as an invalid request. "
                        "The application will not retry this request.\n\n"
                        f"Details: {exc}"
                    ) from exc

                # ---------------------------------------------------
                # RATE LIMIT
                # ---------------------------------------------------

                if error_type == "rate_limit":

                    if transient_retry_count < MAX_TRANSIENT_RETRIES:

                        transient_retry_count += 1

                        time.sleep(
                            RETRY_DELAY_SECONDS
                        )

                        continue

                    raise RuntimeError(
                        f"{operation} was temporarily rate-limited. "
                        "The application made one controlled retry "
                        "and stopped to avoid unnecessary API usage.\n\n"
                        f"Details: {exc}"
                    ) from exc

                # ---------------------------------------------------
                # TEMPORARY SERVICE UNAVAILABLE
                # ---------------------------------------------------

                if error_type == "service_unavailable":

                    if transient_retry_count < MAX_TRANSIENT_RETRIES:

                        transient_retry_count += 1

                        time.sleep(
                            RETRY_DELAY_SECONDS
                        )

                        continue

                    # One controlled retry failed.
                    # Move to the next available model.
                    break

                # ---------------------------------------------------
                # MODEL NOT FOUND
                # ---------------------------------------------------

                if error_type == "not_found":
                    break

                # ---------------------------------------------------
                # SERVER ERROR
                # ---------------------------------------------------

                if error_type == "server_error":

                    if transient_retry_count < MAX_TRANSIENT_RETRIES:

                        transient_retry_count += 1

                        time.sleep(
                            RETRY_DELAY_SECONDS
                        )

                        continue

                    break

                # ---------------------------------------------------
                # UNKNOWN ERROR
                # ---------------------------------------------------

                raise RuntimeError(
                    _build_failure_message(
                        operation,
                        errors,
                    )
                ) from exc

    raise RuntimeError(
        _build_failure_message(
            operation,
            errors,
        )
    )


# -------------------------------------------------------------------
# Gemini connection test
# -------------------------------------------------------------------

def test_gemini_connection():
    """
    Test Gemini connectivity with minimal API usage.

    Only the configured model is tested.

    This function intentionally does not cycle through every
    model because a connection test should not consume quota
    unnecessarily.
    """

    client = get_gemini_client()

    configured_model = get_gemini_model()

    response = _generate_content_with_policy(
        client=client,
        model_sequence=[configured_model],
        contents=(
            "Reply with exactly: "
            "Gemini connection successful."
        ),
        operation="Gemini connection test",
    )

    return response.text


# -------------------------------------------------------------------
# Structured extraction schema
# -------------------------------------------------------------------

def _build_extraction_schema():
    """Build the Gemini JSON schema."""

    properties = {}

    for field in EXTRACTION_FIELDS:
        properties[field] = {
            "type": "string"
        }

    return {
        "type": "object",
        "properties": properties,
        "required": EXTRACTION_FIELDS,
    }


# -------------------------------------------------------------------
# Structured document extraction
# -------------------------------------------------------------------

def extract_structured_data(document_text):
    """
    Extract the required fields from document text.

    Normal operation uses one Gemini generation request.

    Additional requests occur only when a temporary service
    problem requires controlled retry/fallback.
    """

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

    model_sequence = _get_model_sequence(
        available_models
    )

    schema = _build_extraction_schema()

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

    response = _generate_content_with_policy(
        client=client,
        model_sequence=model_sequence,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
        operation="Structured Gemini extraction",
    )

    return response.text


# -------------------------------------------------------------------
# OCR
# -------------------------------------------------------------------

def extract_text_from_image(
    image_bytes,
    mime_type="image/png",
):
    """
    Extract text from a scanned document page using Gemini Vision.

    Each scanned page requires a Gemini request.

    The same intelligent retry/quota policy is applied.
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

    model_sequence = _get_model_sequence(
        available_models
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

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type,
    )

    response = _generate_content_with_policy(
        client=client,
        model_sequence=model_sequence,
        contents=[
            image_part,
            prompt,
        ],
        operation="Gemini OCR",
    )

    return response.text


# -------------------------------------------------------------------
# Natural-language correction
# -------------------------------------------------------------------

def apply_natural_language_correction(
    current_record,
    correction_instruction,
):
    """
    Apply a user's natural-language correction
    to the current extracted record.

    The corrected record is returned for human review.

    Nothing is saved to the database here.

    This function is called ONLY when the user explicitly
    requests AI correction.
    """

    if not isinstance(current_record, dict):
        raise TypeError(
            "Current record must be a dictionary."
        )

    if (
        not correction_instruction
        or not correction_instruction.strip()
    ):
        raise ValueError(
            "Correction instruction cannot be empty."
        )

    current_data = {
        field: str(
            current_record.get(field, "")
        )
        for field in EXTRACTION_FIELDS
    }

    schema = _build_extraction_schema()

    prompt = f"""
You are a professional document-record correction assistant.

The user has already reviewed a document extraction
and wants to make a correction using natural language.

CURRENT RECORD:
----------------
{json.dumps(current_data, ensure_ascii=False, indent=2)}
----------------

USER CORRECTION:
----------------
{correction_instruction}
----------------

IMPORTANT RULES:

1. Return ONLY structured JSON.
2. Return every field in the record.
3. Use exactly these fields:
   {EXTRACTION_FIELDS}
4. Do not create additional fields.
5. Do not modify fields that the user's instruction
   does not ask you to change.
6. Apply only corrections that are clearly stated.
7. Do not guess or invent information.
8. Do not change "Sr. No.".
9. If the user asks to clear a field, return
   an empty string for that field.
10. Preserve dates, document numbers and amounts
    exactly as instructed.

Return the corrected record only.
"""

    client = get_gemini_client()

    available_models = get_available_models(client)

    if not available_models:
        raise RuntimeError(
            "None of the configured Gemini models are currently available."
        )

    model_sequence = _get_model_sequence(
        available_models
    )

    response = _generate_content_with_policy(
        client=client,
        model_sequence=model_sequence,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        ),
        operation="Natural-language Gemini correction",
    )

    try:
        corrected_record = json.loads(
            response.text
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Gemini returned correction data "
            "that could not be interpreted as valid JSON."
        ) from exc

    unexpected_fields = (
        set(corrected_record.keys())
        - set(EXTRACTION_FIELDS)
    )

    if unexpected_fields:
        raise ValueError(
            "Gemini returned unexpected fields: "
            f"{sorted(unexpected_fields)}"
        )

    corrected_record = {
        field: str(
            corrected_record.get(field, "")
        )
        for field in EXTRACTION_FIELDS
    }

    return corrected_record
