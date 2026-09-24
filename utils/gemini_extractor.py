import json
import os
import time

import streamlit as st
from google import genai
from google.genai import types

from config.schema import EXTRACTION_FIELDS


# ============================================================
# GEMINI MODEL CONFIGURATION
# ============================================================

MODEL_PRIORITY = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

# Deliberately low to prevent unnecessary API usage.
MAX_TRANSIENT_RETRIES = 1

# Delay before one controlled retry.
RETRY_DELAY_SECONDS = 2


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():
    """
    Create and return the Gemini API client.
    """

    api_key = (
        st.secrets.get("GEMINI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    try:
        return genai.Client(
            api_key=api_key
        )

    except Exception as exc:
        raise RuntimeError(
            "Gemini could not be initialized. "
            "Please verify the API configuration."
        ) from exc


# ============================================================
# MODEL DISCOVERY
# ============================================================

def get_available_models(client):
    """
    Return available models from the application's
    controlled priority list.

    Model discovery does not perform document generation.
    """

    available_models = []

    try:

        models = client.models.list()

        for model in models:

            model_name = (
                model.name
                .replace("models/", "")
            )

            supported_methods = getattr(
                model,
                "supported_actions",
                [],
            )

            if (
                model_name in MODEL_PRIORITY
                and (
                    not supported_methods
                    or "generateContent"
                    in supported_methods
                )
            ):
                available_models.append(
                    model_name
                )

    except Exception as exc:

        raise RuntimeError(
            "Unable to check Gemini model availability."
        ) from exc

    return [
        model
        for model in MODEL_PRIORITY
        if model in available_models
    ]


def get_gemini_model():
    """
    Return the configured Gemini model.

    Streamlit Secrets takes priority over the environment.
    """

    return (
        st.secrets.get("GEMINI_MODEL")
        or os.environ.get("GEMINI_MODEL")
        or "gemini-3.8-flash"
    )


def _get_model_sequence(
    available_models,
):
    """
    Build the controlled model sequence.

    The configured model is attempted first.

    Remaining supported models are used only when the
    current model is unavailable or temporarily unavailable.

    Daily quota exhaustion NEVER triggers model fallback.
    """

    configured_model = get_gemini_model()

    ordered_models = []

    if configured_model in available_models:
        ordered_models.append(
            configured_model
        )

    for model_name in available_models:

        if model_name not in ordered_models:
            ordered_models.append(
                model_name
            )

    return ordered_models


# ============================================================
# ERROR CLASSIFICATION
# ============================================================

def _get_exception_status_code(exc):
    """
    Attempt to retrieve an HTTP/status code from a Gemini
    exception.
    """

    for attribute in (
        "status_code",
        "code",
        "http_status",
    ):

        value = getattr(
            exc,
            attribute,
            None,
        )

        if isinstance(value, int):
            return value

    return None


def _classify_gemini_error(exc):
    """
    Classify a Gemini exception into a controlled action.

    Possible results:

        quota_exhausted
        rate_limit
        service_unavailable
        not_found
        bad_request
        authentication
        permission
        server_error
        other
    """

    message = str(exc).lower()

    status_code = (
        _get_exception_status_code(exc)
    )

    # --------------------------------------------------------
    # DAILY / EXHAUSTED QUOTA
    # --------------------------------------------------------

    if (
        "quota exceeded" in message
        or "quota_exceeded" in message
        or "generate_content_free_tier_requests"
        in message
        or "daily quota" in message
        or "daily limit" in message
    ):
        return "quota_exhausted"

    # --------------------------------------------------------
    # HTTP 429
    # --------------------------------------------------------

    if status_code == 429:

        if (
            "quota" in message
            or "daily" in message
            or "resource_exhausted" in message
        ):
            return "quota_exhausted"

        return "rate_limit"

    if (
        "429" in message
        and (
            "rate limit" in message
            or "too many requests" in message
        )
    ):
        return "rate_limit"

    # --------------------------------------------------------
    # HTTP 503
    # --------------------------------------------------------

    if status_code == 503:
        return "service_unavailable"

    if (
        "503" in message
        or "service unavailable" in message
        or "temporarily unavailable" in message
        or "high demand" in message
    ):
        return "service_unavailable"

    # --------------------------------------------------------
    # HTTP 404
    # --------------------------------------------------------

    if status_code == 404:
        return "not_found"

    if (
        "404" in message
        or "not found" in message
        or "model not found" in message
    ):
        return "not_found"

    # --------------------------------------------------------
    # HTTP 400
    # --------------------------------------------------------

    if status_code == 400:
        return "bad_request"

    if (
        "400" in message
        or "invalid argument" in message
        or "invalid request" in message
        or "bad request" in message
    ):
        return "bad_request"

    # --------------------------------------------------------
    # HTTP 401
    # --------------------------------------------------------

    if status_code == 401:
        return "authentication"

    if (
        "401" in message
        or "unauthorized" in message
        or "api key" in message
    ):
        return "authentication"

    # --------------------------------------------------------
    # HTTP 403
    # --------------------------------------------------------

    if status_code == 403:
        return "permission"

    if (
        "403" in message
        or "permission denied" in message
        or "forbidden" in message
    ):
        return "permission"

    # --------------------------------------------------------
    # HTTP 500 / 504
    # --------------------------------------------------------

    if status_code in (
        500,
        504,
    ):
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


# ============================================================
# USER-FACING ERROR MESSAGES
# ============================================================

def _build_quota_error_message():
    """
    Return a clear quota message without exposing
    low-level Gemini API details.
    """

    return (
        "Gemini daily quota has been reached. "
        "No additional Gemini requests will be attempted. "
        "Please try again after the quota resets or "
        "update the Gemini API usage/billing tier."
    )


def _build_failure_message(
    operation,
    errors,
):
    """
    Build a controlled failure message.

    Detailed API exception text is deliberately not exposed
    to the user in production.
    """

    attempted_models = []

    for error in errors:

        model_name = (
            error.split(":", 1)[0]
            if ":" in error
            else "unknown"
        )

        if model_name not in attempted_models:
            attempted_models.append(
                model_name
            )

    models_text = ", ".join(
        attempted_models
    )

    return (
        f"{operation} could not be completed. "
        f"Gemini models attempted: {models_text}. "
        "Please try again later."
    )


# ============================================================
# CONTROLLED GEMINI REQUEST ENGINE
# ============================================================

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

    Policy:

    Daily quota:
        Stop immediately.

    Temporary rate limit:
        One retry, then stop.

    503 service unavailable:
        One retry, then move to next model.

    404 model unavailable:
        Move to next model.

    500 / 504:
        One retry, then move to next model.

    Authentication / permission / invalid request:
        Stop immediately.

    Unknown errors:
        Stop immediately.
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

                response = (
                    client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config,
                    )
                )

                if not getattr(
                    response,
                    "text",
                    None,
                ):

                    raise ValueError(
                        "Gemini returned an empty response."
                    )

                return response

            except Exception as exc:

                error_type = (
                    _classify_gemini_error(
                        exc
                    )
                )

                errors.append(
                    f"{model_name}: {error_type}"
                )

                # ------------------------------------------------
                # DAILY QUOTA
                # ------------------------------------------------

                if error_type == "quota_exhausted":

                    raise RuntimeError(
                        _build_quota_error_message()
                    ) from exc

                # ------------------------------------------------
                # AUTHENTICATION
                # ------------------------------------------------

                if error_type == "authentication":

                    raise RuntimeError(
                        "Gemini authentication failed. "
                        "Please verify the configured API key."
                    ) from exc

                # ------------------------------------------------
                # PERMISSION
                # ------------------------------------------------

                if error_type == "permission":

                    raise RuntimeError(
                        "Gemini API permission was denied. "
                        "Please check the API key and project permissions."
                    ) from exc

                # ------------------------------------------------
                # INVALID REQUEST
                # ------------------------------------------------

                if error_type == "bad_request":

                    raise RuntimeError(
                        f"{operation} was rejected as an invalid "
                        "Gemini request. The request will not "
                        "be retried."
                    ) from exc

                # ------------------------------------------------
                # RATE LIMIT
                # ------------------------------------------------

                if error_type == "rate_limit":

                    if (
                        transient_retry_count
                        < MAX_TRANSIENT_RETRIES
                    ):

                        transient_retry_count += 1

                        time.sleep(
                            RETRY_DELAY_SECONDS
                        )

                        continue

                    raise RuntimeError(
                        f"{operation} was temporarily "
                        "rate-limited. One controlled retry "
                        "was attempted."
                    ) from exc

                # ------------------------------------------------
                # SERVICE UNAVAILABLE
                # ------------------------------------------------

                if error_type == "service_unavailable":

                    if (
                        transient_retry_count
                        < MAX_TRANSIENT_RETRIES
                    ):

                        transient_retry_count += 1

                        time.sleep(
                            RETRY_DELAY_SECONDS
                        )

                        continue

                    break

                # ------------------------------------------------
                # MODEL NOT FOUND
                # ------------------------------------------------

                if error_type == "not_found":
                    break

                # ------------------------------------------------
                # SERVER ERROR
                # ------------------------------------------------

                if error_type == "server_error":

                    if (
                        transient_retry_count
                        < MAX_TRANSIENT_RETRIES
                    ):

                        transient_retry_count += 1

                        time.sleep(
                            RETRY_DELAY_SECONDS
                        )

                        continue

                    break

                # ------------------------------------------------
                # UNKNOWN ERROR
                # ------------------------------------------------

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


# ============================================================
# GEMINI CONNECTION TEST
# ============================================================

def test_gemini_connection():
    """
    Test the configured Gemini model with one minimal request.

    No model fallback is performed because this function is
    intended only as a controlled connection test.
    """

    client = get_gemini_client()

    configured_model = (
        get_gemini_model()
    )

    response = (
        _generate_content_with_policy(
            client=client,
            model_sequence=[
                configured_model
            ],
            contents=(
                "Reply with exactly: "
                "Gemini connection successful."
            ),
            operation="Gemini connection test",
        )
    )

    return response.text.strip()


# ============================================================
# STRUCTURED OUTPUT SCHEMA
# ============================================================

def _build_extraction_schema():
    """
    Build the JSON schema used by Gemini structured output.

    Sr. No. is intentionally absent because it is generated
    by the application/export layer.
    """

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


# ============================================================
# STRUCTURED JSON VALIDATION
# ============================================================

def _parse_and_validate_structured_response(
    response_text,
    operation,
):
    """
    Parse and validate a Gemini structured JSON response.

    Returns:
        dict containing exactly EXTRACTION_FIELDS.
    """

    if not response_text:

        raise ValueError(
            f"{operation} returned an empty response."
        )

    try:

        data = json.loads(
            response_text
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            f"{operation} returned invalid JSON."
        ) from exc

    if not isinstance(
        data,
        dict,
    ):

        raise ValueError(
            f"{operation} returned an invalid "
            "record structure."
        )

    actual_fields = set(
        data.keys()
    )

    expected_fields = set(
        EXTRACTION_FIELDS
    )

    unexpected_fields = (
        actual_fields - expected_fields
    )

    if unexpected_fields:

        raise ValueError(
            f"{operation} returned unexpected fields: "
            f"{sorted(unexpected_fields)}"
        )

    missing_fields = (
        expected_fields - actual_fields
    )

    if missing_fields:

        raise ValueError(
            f"{operation} did not return all required fields: "
            f"{sorted(missing_fields)}"
        )

    validated = {}

    for field in EXTRACTION_FIELDS:

        value = data.get(
            field
        )

        if value is None:
            value = ""

        if not isinstance(
            value,
            str,
        ):
            value = str(value)

        validated[field] = value

    return validated


# ============================================================
# STRUCTURED DOCUMENT EXTRACTION
# ============================================================

def extract_structured_data(
    document_text,
):
    """
    Extract the required credential fields from document text.

    Returns:
        JSON string containing exactly EXTRACTION_FIELDS.

    One Gemini generation request is normally used.
    Controlled retry/fallback occurs only for temporary
    Gemini service conditions.
    """

    if (
        not document_text
        or not document_text.strip()
    ):

        raise ValueError(
            "No document text was provided."
        )

    client = get_gemini_client()

    available_models = (
        get_available_models(
            client
        )
    )

    if not available_models:

        raise RuntimeError(
            "None of the configured Gemini models "
            "are currently available."
        )

    model_sequence = (
        _get_model_sequence(
            available_models
        )
    )

    schema = (
        _build_extraction_schema()
    )

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
10. Do not infer information that is not supported by
    the document.

Required fields:

{EXTRACTION_FIELDS}

Document:
----------------
{document_text}
----------------
"""

    response = (
        _generate_content_with_policy(
            client=client,
            model_sequence=model_sequence,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
            operation="Structured Gemini extraction",
        )
    )

    validated = (
        _parse_and_validate_structured_response(
            response.text,
            "Structured Gemini extraction",
        )
    )

    # Return JSON to preserve compatibility with the current
    # upload_ui.py workflow.
    return json.dumps(
        validated,
        ensure_ascii=False,
    )


# ============================================================
# OCR
# ============================================================

def extract_text_from_image(
    image_bytes,
    mime_type="image/png",
):
    """
    Extract text from a scanned document page using Gemini Vision.

    Each scanned page requires one Gemini generation request.

    The same controlled quota/retry/fallback policy applies.
    """

    if not image_bytes:

        raise ValueError(
            "No image data was provided for OCR."
        )

    if not mime_type:

        raise ValueError(
            "Image MIME type is required for OCR."
        )

    client = get_gemini_client()

    available_models = (
        get_available_models(
            client
        )
    )

    if not available_models:

        raise RuntimeError(
            "None of the configured Gemini models "
            "are currently available."
        )

    model_sequence = (
        _get_model_sequence(
            available_models
        )
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

    try:

        image_part = (
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )
        )

    except Exception as exc:

        raise ValueError(
            "The scanned page could not be prepared "
            "for Gemini OCR."
        ) from exc

    response = (
        _generate_content_with_policy(
            client=client,
            model_sequence=model_sequence,
            contents=[
                image_part,
                prompt,
            ],
            operation="Gemini OCR",
        )
    )

    text = (
        response.text
        if response.text
        else ""
    )

    return text.strip()


# ============================================================
# NATURAL-LANGUAGE CORRECTION
# ============================================================

def apply_natural_language_correction(
    current_record,
    correction_instruction,
):
    """
    Apply an explicit user-requested natural-language
    correction to the current extracted record.

    Nothing is saved to the database here.

    The corrected record is returned for human review.
    """

    if not isinstance(
        current_record,
        dict,
    ):

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

    # --------------------------------------------------------
    # Build a strictly controlled representation of the
    # current record.
    # --------------------------------------------------------

    current_data = {
        field: str(
            current_record.get(
                field,
                "",
            )
        )
        for field in EXTRACTION_FIELDS
    }

    schema = (
        _build_extraction_schema()
    )

    prompt = f"""
You are a professional document-record correction assistant.

The user has already reviewed a document extraction
and wants to make a correction using natural language.

CURRENT RECORD:
----------------
{json.dumps(
    current_data,
    ensure_ascii=False,
    indent=2,
)}
----------------

USER CORRECTION:
----------------
{correction_instruction.strip()}
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

    available_models = (
        get_available_models(
            client
        )
    )

    if not available_models:

        raise RuntimeError(
            "None of the configured Gemini models "
            "are currently available."
        )

    model_sequence = (
        _get_model_sequence(
            available_models
        )
    )

    response = (
        _generate_content_with_policy(
            client=client,
            model_sequence=model_sequence,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
            operation=(
                "Natural-language Gemini correction"
            ),
        )
    )

    corrected_record = (
        _parse_and_validate_structured_response(
            response.text,
            "Natural-language Gemini correction",
        )
    )

    return corrected_record
