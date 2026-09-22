import json
import os
import google.generativeai as genai
import streamlit as st

def initialize_gemini():
    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in secrets or environment.")
    genai.configure(api_key=api_key)

def apply_nlp_correction(current_data: dict, user_instruction: str, expected_fields: list) -> dict:
    """
    Applies user natural language corrections to the current extracted data.
    Returns updated data as a dictionary.
    """
    initialize_gemini()
    
    model_name = st.secrets.get("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""
    You are an expert administrative assistant managing a structured database.
    
    CURRENT EXTRACTED DATA:
    {json.dumps(current_data, indent=2)}
    
    USER INSTRUCTION:
    "{user_instruction}"
    
    EXPECTED FIELDS:
    {json.dumps(expected_fields)}
    
    TASK:
    1. Update the fields in the CURRENT EXTRACTED DATA based strictly on the USER INSTRUCTION.
    2. Maintain all unmentioned fields exactly as they are.
    3. Ensure the output strictly contains ONLY the keys present in EXPECTED FIELDS.
    4. Respond ONLY with valid JSON inside a ```json ``` code block.
    """
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Extract JSON content
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        json_str = response_text.split("```")[1].split("```")[0].strip()
    else:
        json_str = response_text
        
    updated_data = json.loads(json_str)
    return updated_data
