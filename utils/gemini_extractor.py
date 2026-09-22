import json
import random
import re
import time
from typing import Any, Dict, List
from google import genai
from google.genai import types
import streamlit as st


class GeminiExtractor:
    """Manages multi-modal PDF extraction using Google's GenAI SDK.

    Includes retry logic and model fallback handling for capacity limits (503)
    and model versioning.
    """

    def __init__(self):
        # Retrieve credentials and model configuration from Streamlit secrets
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        # Default to 2.5/3.x flash if no model specified
        self.model_name = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from Streamlit secrets. "
                "Please configure it under App Settings > Secrets."
            )

        # Initialize official GenAI client
        self.client = genai.Client(api_key=self.api_key)

    def _build_system_instruction(self, target_fields: List[str]) -> str:
        """Constructs a strict system instruction prompt based on active schema fields."""
        formatted_fields = "\n".join([f"- {field}" for field in target_fields])

        return f"""
You are an expert document credential extraction assistant.
Your job is to analyze the provided PDF document and extract metadata accurately.

Target JSON Keys to Extract:
{formatted_fields}

STRICT EXTRACTION RULES:
1. Return ONLY a valid JSON object matching the requested keys above.
2. If a field value is explicitly found in the document, extract it exactly as written.
3. If a field value is NOT found, set its value to null.
4. Do NOT include markdown code blocks (such as ```json), introductory text, or explanatory prose.
5. Ensure dates follow clean readable formatting (e.g., YYYY-MM-DD or DD-MMM-YYYY) if available.
6. Ensure currency/amounts retain original numerical format.
"""

    def extract_from_pdf(
        self, pdf_bytes: bytes, target_fields: List[str]
    ) -> Dict[str, Any]:
        """Uploads PDF bytes to Gemini API and parses structured JSON output

        with retry and model fallback logic.
        """
        system_prompt = self._build_system_instruction(target_fields)

        # Prepare multimodal document payload
        pdf_part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type="application/pdf",
        )

        # Ordered model fallback list to prevent 404 / decommissioning issues
        candidate_models = [
            self.model_name,
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ]
        # Preserve uniqueness while maintaining order
        candidate_models = list(dict.fromkeys(candidate_models))

        last_error = None

        for model in candidate_models:
            # Try up to 3 retries per model for temporary 503 capacity spikes
            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=[
                            pdf_part,
                            (
                                "Extract all required credential metadata from"
                                " this document into JSON format."
                            ),
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            temperature=0.1,  # Deterministic output
                        ),
                    )

                    raw_text = response.text.strip() if response.text else "{}"

                    # Clean markdown wrappers if returned
                    cleaned_text = re.sub(r"^```json\s*", "", raw_text)
                    cleaned_text = re.sub(r"\s*```$", "", cleaned_text).strip()

                    extracted_data = json.loads(cleaned_text)

                    # Align output with master schema target fields
                    final_data = {}
                    for field in target_fields:
                        final_data[field] = extracted_data.get(field)

                    return final_data

                except Exception as err:
                    last_error = err
                    err_msg = str(err)

                    # Handle temporary capacity or rate limit spikes (503 / 429)
                    if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                        backoff_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                        time.sleep(backoff_time)
                        continue
                    # Handle missing or unsupported model names (404)
                    elif "404" in err_msg or "NOT_FOUND" in err_msg:
                        break
                    else:
                        raise err

        raise RuntimeError(
            f"Gemini extraction failed across candidate models: {str(last_error)}"
        )
