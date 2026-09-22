import json
import re
from typing import Any, Dict, List
from google import genai
from google.genai import types
import streamlit as st


class GeminiExtractor:
    """Manages multi-modal PDF extraction using Google's GenAI SDK

    and enforces structured JSON output based on the master Excel schema.
    """

    def __init__(self):
        # Retrieve credentials and model configuration from Streamlit secrets
        self.api_key = st.secrets.get("GEMINI_API_KEY")
        self.model_name = st.secrets.get("GEMINI_MODEL", "gemini-1.5-pro")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing from Streamlit secrets. "
                "Please configure it under App Settings > Secrets."
            )

        # Initialize official GenAI client
        self.client = genai.Client(api_key=self.api_key)

    def _build_system_instruction(
        self, target_fields: List[str]
    ) -> str:
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
        """Uploads PDF bytes to Gemini API and parses structured JSON output."""
        system_prompt = self._build_system_instruction(target_fields)

        # Prepare multimodal document payload
        pdf_part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type="application/pdf",
        )

        try:
            # Request structured response from Gemini
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[pdf_part, "Extract all required credential metadata from this document into JSON format."],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1,  # Low temperature for deterministic extraction
                ),
            )

            raw_text = response.text.strip() if response.text else "{}"
            
            # Clean potential markdown wrapping if present
            cleaned_text = re.sub(r"^```json\s*", "", raw_text)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text).strip()

            extracted_data = json.loads(cleaned_text)

            # Ensure all requested fields exist in output dictionary
            final_data = {}
            for field in target_fields:
                final_data[field] = extracted_data.get(field)

            return final_data

        except json.JSONDecodeError as err:
            raise ValueError(f"Gemini returned invalid JSON structure: {err}")
        except Exception as err:
            raise RuntimeError(f"Gemini API extraction failed: {str(err)}")
