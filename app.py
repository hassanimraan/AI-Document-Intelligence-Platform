import json

import pandas as pd
import streamlit as st
from supabase import create_client

from config.schema import EXTRACTION_FIELDS
from utils.validation import validate_pdf, normalize_record
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_extractor import (
    extract_structured_data,
    apply_natural_language_correction,
)
from utils.database import DatabaseManager


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Credential Extraction Chatbot",
    page_icon="📄",
    layout="wide",
)


# ============================================================
# SUPABASE CLIENT
# ============================================================

@st.cache_resource
def get_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_PUBLISHABLE_KEY"],
    )


supabase = get_supabase_client()


# ============================================================
# AUTHENTICATION STATE
# ============================================================

def initialize_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "access_token" not in st.session_state:
        st.session_state.access_token = None

    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None

    if "user_email" not in st.session_state:
        st.session_state.user_email = None


def restore_session():
    try:
        session = supabase.auth.get_session()

        if session is not None:
            if session.access_token and session.refresh_token:
                st.session_state.access_token = session.access_token
                st.session_state.refresh_token = session.refresh_token
                st.session_state.authenticated = True

                if session.user:
                    st.session_state.user_email = session.user.email

                return True

    except Exception:
        pass

    return False


def login_user(email, password):
    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    session = response.session
    user = response.user

    if session is None or user is None:
        raise ValueError("Login failed.")

    st.session_state.access_token = session.access_token
    st.session_state.refresh_token = session.refresh_token
    st.session_state.authenticated = True
    st.session_state.user_email = user.email


def signup_user(email, password):
    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )

    if response.user is None:
        raise ValueError("Account creation failed.")

    if response.session is not None:
        st.session_state.access_token = response.session.access_token
        st.session_state.refresh_token = response.session.refresh_token
        st.session_state.authenticated = True
        st.session_state.user_email = response.user.email

    return response


def logout_user():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None

    # Clear temporary workflow state.
    keys_to_clear = [
        "uploaded_file_name",
        "extracted_text",
        "extracted_data",
        "edited_data",
        "corrected_data",
        "final_data",
        "confirmation",
        "verified_data",
    ]

    for key in keys_to_clear:
        st.session_state.pop(key, None)


# ============================================================
# INITIALIZE AUTH
# ============================================================

initialize_auth_state()

if not st.session_state.authenticated:
    restore_session()


# ============================================================
# LOGIN / SIGNUP SCREEN
# ============================================================

if not st.session_state.authenticated:

    st.title("📄 Credential Extraction Chatbot")

    st.write(
        "Secure document extraction and credential management."
    )

    login_tab, signup_tab = st.tabs(
        ["Login", "Create Account"]
    )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    with login_tab:

        st.subheader("Login")

        login_email = st.text_input(
            "Email",
            key="login_email",
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            key="login_button",
        ):

            if not login_email or not login_password:
                st.error(
                    "Please enter your email and password."
                )

            else:

                try:

                    login_user(
                        login_email.strip(),
                        login_password,
                    )

                    st.success("Login successful.")

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Login failed: {exc}"
                    )

    # --------------------------------------------------------
    # SIGNUP
    # --------------------------------------------------------

    with signup_tab:

        st.subheader("Create Account")

        signup_email = st.text_input(
            "Email",
            key="signup_email",
        )

        signup_password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
        )

        signup_password_confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_password_confirm",
        )

        if st.button(
            "Create Account",
            type="primary",
            key="signup_button",
        ):

            if not signup_email or not signup_password:
                st.error(
                    "Please enter an email and password."
                )

            elif signup_password != signup_password_confirm:
                st.error(
                    "Passwords do not match."
                )

            else:

                try:

                    response = signup_user(
                        signup_email.strip(),
                        signup_password,
                    )

                    if response.session is None:

                        st.success(
                            "Account created. "
                            "Please check your email "
                            "to confirm your account."
                        )

                    else:

                        st.success(
                            "Account created successfully."
                        )

                        st.rerun()

                except Exception as exc:

                    st.error(
                        f"Account creation failed: {exc}"
                    )

    st.stop()


# ============================================================
# AUTHENTICATED APPLICATION
# ============================================================

st.title("📄 Credential Extraction Chatbot")

st.caption(
    "Phase 8 — Persistent Supabase Database"
)

# ------------------------------------------------------------
# USER INFORMATION
# ------------------------------------------------------------

user_col1, user_col2 = st.columns(
    [5, 1]
)

with user_col1:

    st.success(
        f"Logged in as: {st.session_state.user_email}"
    )

with user_col2:

    if st.button(
        "Logout",
        key="logout_button",
    ):

        logout_user()
        st.rerun()


# ============================================================
# PDF PROCESSING WORKFLOW
# ============================================================

st.header("📥 Process Credential Document")

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"],
    key="credential_pdf_uploader",
)


# ------------------------------------------------------------
# NEW PDF DETECTION
# ------------------------------------------------------------

if uploaded_file is not None:

    current_file_name = uploaded_file.name

    previous_file_name = st.session_state.get(
        "uploaded_file_name"
    )

    if current_file_name != previous_file_name:

        st.session_state.uploaded_file_name = (
            current_file_name
        )

        st.session_state.pop(
            "extracted_text",
            None
        )

        st.session_state.pop(
            "extracted_data",
            None
        )

        st.session_state.pop(
            "edited_data",
            None
        )

        st.session_state.pop(
            "corrected_data",
            None
        )

        st.session_state.pop(
            "final_data",
            None
        )

        st.session_state.pop(
            "confirmation",
            None
        )

        st.session_state.pop(
            "verified_data",
            None
        )


# ------------------------------------------------------------
# PROCESS PDF
# ------------------------------------------------------------

if uploaded_file is not None:

    if st.button(
        "🔍 Process PDF",
        type="primary",
        key="process_pdf_button",
    ):

        try:

            validate_pdf(uploaded_file)

            with st.spinner(
                "Extracting text from PDF..."
            ):

                extracted_text = extract_text_from_pdf(
                    uploaded_file
                )

            if not extracted_text:

                raise ValueError(
                    "No text could be extracted from the PDF."
                )

            st.session_state.extracted_text = (
                extracted_text
            )

            with st.spinner(
                "Extracting structured credential data..."
            ):

                structured_data = (
                    extract_structured_data(
                        extracted_text
                    )
                )

            if isinstance(
                structured_data,
                str
            ):

                structured_data = json.loads(
                    structured_data
                )

            st.session_state.extracted_data = (
                structured_data
            )

            st.session_state.edited_data = (
                structured_data.copy()
            )

            st.session_state.pop(
                "corrected_data",
                None
            )

            st.session_state.pop(
                "final_data",
                None
            )

            st.session_state.pop(
                "confirmation",
                None
            )

            st.session_state.pop(
                "verified_data",
                None
            )

            st.success(
                "PDF processed successfully."
            )

        except Exception as exc:

            st.error(
                f"Unable to process PDF: {exc}"
            )


# ============================================================
# EXTRACTED TEXT
# ============================================================

if st.session_state.get(
    "extracted_text"
):

    with st.expander(
        "📄 Extracted Text",
        expanded=False,
    ):

        st.text(
            st.session_state.extracted_text
        )


# ============================================================
# MANUAL REVIEW
# ============================================================

if st.session_state.get(
    "extracted_data"
):

    st.header("✏️ Review Extracted Data")

    source_data = st.session_state.get(
        "edited_data",
        st.session_state.extracted_data,
    )

    edited_data = {}

    for field in EXTRACTION_FIELDS:

        current_value = source_data.get(
            field
        )

        if current_value is None:
            current_value = ""

        edited_data[field] = st.text_input(
            field,
            value=str(current_value),
            key=f"edit_{field}",
        )

    if st.button(
        "💾 Apply Manual Edits",
        key="apply_manual_edits",
    ):

        st.session_state.edited_data = (
            edited_data
        )

        st.session_state.pop(
            "corrected_data",
            None
        )

        st.session_state.pop(
            "final_data",
            None
        )

        st.session_state.pop(
            "confirmation",
            None
        )

        st.success(
            "Manual edits applied."
        )


# ============================================================
# NATURAL LANGUAGE CORRECTION
# ============================================================

if st.session_state.get(
    "edited_data"
):

    st.header(
        "💬 Natural Language Correction"
    )

    correction_instruction = st.text_area(
        "Describe the correction you want",
        placeholder=(
            "Example: Change the system to OLMRTS "
            "and the contract to O&M Contract."
        ),
        key="correction_instruction",
    )

    if st.button(
        "🤖 Apply AI Correction",
        key="apply_ai_correction",
    ):

        if not correction_instruction.strip():

            st.warning(
                "Please enter a correction instruction."
            )

        else:

            try:

                with st.spinner(
                    "Applying AI correction..."
                ):

                    corrected_data = (
                        apply_natural_language_correction(
                            st.session_state.edited_data,
                            correction_instruction,
                        )
                    )

                if isinstance(
                    corrected_data,
                    str
                ):

                    corrected_data = json.loads(
                        corrected_data
                    )

                st.session_state.corrected_data = (
                    corrected_data
                )

                st.session_state.pop(
                    "final_data",
                    None
                )

                st.session_state.pop(
                    "confirmation",
                    None
                )

                st.success(
                    "AI correction applied."
                )

            except Exception as exc:

                st.error(
                    f"Unable to apply correction: {exc}"
                )


# ============================================================
# CORRECTED DATA REVIEW
# ============================================================

if st.session_state.get(
    "corrected_data"
):

    st.header(
        "🔎 Review Corrected Data"
    )

    corrected_data = (
        st.session_state.corrected_data
    )

    for field in EXTRACTION_FIELDS:

        value = corrected_data.get(
            field
        )

        st.write(
            f"**{field}:** {value if value is not None else ''}"
        )

    if st.button(
        "Use Corrected Data",
        key="use_corrected_data",
    ):

        st.session_state.final_data = (
            corrected_data.copy()
        )

        st.success(
            "Corrected data selected for final verification."
        )


# ============================================================
# FINAL CONFIRMATION
# ============================================================

if st.session_state.get(
    "final_data"
):

    st.header(
        "✅ Final Verification"
    )

    final_data = st.session_state.final_data

    st.json(final_data)

    confirmation = st.checkbox(
        "I have reviewed the extracted information "
        "and confirm that it is correct.",
        key="final_confirmation",
    )

    if st.button(
        "💾 Confirm & Save Record",
        type="primary",
        key="confirm_save_button",
    ):

        if not confirmation:

            st.warning(
                "Please confirm that the record is correct."
            )

        else:

            try:

                normalized_record = normalize_record(
                    final_data
                )

                db = DatabaseManager()

                db.set_user_session(
                    st.session_state.access_token,
                    st.session_state.refresh_token,
                )

                saved_record = db.insert_credential(
                    normalized_record,
                    document_filename=st.session_state.get(
                        "uploaded_file_name"
                    ),
                )

                st.session_state.verified_data = (
                    normalized_record
                )

                st.success(
                    "✓ Record verified and saved successfully "
                    "to the Supabase database."
                )

                st.write(
                    "**Database Record ID:**"
                )

                st.code(
                    saved_record["id"]
                )

            except Exception as exc:

                st.error(
                    f"Unable to save record: {exc}"
                )


# ============================================================
# MY CREDENTIAL RECORDS
# ============================================================

st.divider()

st.header("📚 My Credential Records")

st.write(
    "Records stored in Supabase for the currently "
    "authenticated user."
)

if st.button(
    "🔄 Load My Records",
    key="load_my_records_button",
):

    try:

        db = DatabaseManager()

        db.set_user_session(
            st.session_state.access_token,
            st.session_state.refresh_token,
        )

        records = db.get_user_credentials()

        if not records:

            st.info(
                "No saved credential records found."
            )

        else:

            display_rows = []

            for record in records:

                display_rows.append(
                    {
                        "Sr. No.": 0,

                        "Client (PMA)": record.get(
                            "client_pma"
                        ),

                        "System (LMBS, PMBS, MMBS, OLMRTS)": (
                            record.get("system")
                        ),

                        "Contract": record.get(
                            "contract"
                        ),

                        "Document Type": record.get(
                            "document_type"
                        ),

                        "Document Number": record.get(
                            "document_number"
                        ),

                        "Date of Issuance": record.get(
                            "date_of_issuance"
                        ),

                        "Amount": record.get(
                            "amount"
                        ),

                        "Initiated By": record.get(
                            "initiated_by"
                        ),

                        "Reviewed By": record.get(
                            "reviewed_by"
                        ),

                        "Approved by": record.get(
                            "approved_by"
                        ),
                    }
                )

            # Generate display-only serial numbers.
            for index, row in enumerate(
                display_rows,
                start=1,
            ):

                row["Sr. No."] = index

            records_df = pd.DataFrame(
                display_rows
            )

            records_df = records_df[
                [
                    "Sr. No.",
                    "Client (PMA)",
                    "System (LMBS, PMBS, MMBS, OLMRTS)",
                    "Contract",
                    "Document Type",
                    "Document Number",
                    "Date of Issuance",
                    "Amount",
                    "Initiated By",
                    "Reviewed By",
                    "Approved by",
                ]
            ]

            st.dataframe(
                records_df,
                use_container_width=True,
                hide_index=True,
            )

            st.success(
                f"Loaded {len(records_df)} "
                f"saved record(s)."
            )

    except Exception as exc:

        st.error(
            f"Unable to load records: {exc}"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Production-Grade Credential Extraction & "
    "Persistent Excel Database Chatbot"
)
