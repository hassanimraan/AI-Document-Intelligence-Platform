import json

import streamlit as st
from supabase import create_client

from config.schema import EXTRACTION_FIELDS

from utils.validation import (
    validate_pdf,
    normalize_record,
)

from utils.pdf_processor import (
    extract_text_from_pdf
)

from utils.gemini_extractor import (
    extract_structured_data,
    apply_natural_language_correction,
)

from utils.database import (
    DatabaseManager
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Credential Extraction Assistant",
    page_icon="📄",
    layout="wide"
)


# =========================================================
# SUPABASE
# =========================================================

@st.cache_resource
def get_supabase_client():
    """
    Create the Supabase client using the publishable key.

    The secret/service-role key is intentionally NOT used
    for normal user authentication.
    """

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_PUBLISHABLE_KEY"]

    return create_client(
        url,
        key
    )


supabase = get_supabase_client()


# =========================================================
# AUTHENTICATION HELPERS
# =========================================================

def initialize_auth_state():
    """Initialize temporary authentication state."""

    defaults = {
        "authenticated": False,
        "access_token": None,
        "refresh_token": None,
        "user_email": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


def restore_session():
    """
    Restore the Supabase session from Streamlit session state.

    Streamlit session_state is temporary UI/session state only.
    It is NOT used as the permanent database.
    """

    access_token = st.session_state.get(
        "access_token"
    )

    refresh_token = st.session_state.get(
        "refresh_token"
    )

    if not access_token or not refresh_token:
        return False

    try:

        response = supabase.auth.set_session(
            access_token,
            refresh_token
        )

        session = response.session

        if session is None:
            return False

        st.session_state["authenticated"] = True
        st.session_state["access_token"] = session.access_token
        st.session_state["refresh_token"] = session.refresh_token

        user_response = supabase.auth.get_user()

        if user_response.user:

            st.session_state["user_email"] = (
                user_response.user.email
            )

        return True

    except Exception:

        st.session_state["authenticated"] = False
        st.session_state["access_token"] = None
        st.session_state["refresh_token"] = None
        st.session_state["user_email"] = None

        return False


def login_user(email, password):
    """Authenticate an existing Supabase user."""

    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    session = response.session
    user = response.user

    if session is None or user is None:

        raise ValueError(
            "Login did not create an active session. "
            "Your email may not have been confirmed yet."
        )

    st.session_state["authenticated"] = True
    st.session_state["access_token"] = session.access_token
    st.session_state["refresh_token"] = session.refresh_token
    st.session_state["user_email"] = user.email


def signup_user(email, password):
    """Create a new Supabase user."""

    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )

    user = response.user
    session = response.session

    if user is None:

        raise ValueError(
            "Supabase did not return a user."
        )

    # Confirm Email is enabled in this project.
    if session is None:

        return (
            "signup_confirmation_required",
            user
        )

    # Handles the case where confirmation is disabled.
    st.session_state["authenticated"] = True
    st.session_state["access_token"] = session.access_token
    st.session_state["refresh_token"] = session.refresh_token
    st.session_state["user_email"] = user.email

    return (
        "signup_authenticated",
        user
    )


def logout_user():
    """Sign out the current user."""

    try:

        supabase.auth.sign_out()

    except Exception:

        pass

    # Clear authentication state.
    st.session_state["authenticated"] = False
    st.session_state["access_token"] = None
    st.session_state["refresh_token"] = None
    st.session_state["user_email"] = None

    # Clear application workflow state.
    for key in [
        "extracted_data",
        "document_text",
        "processed_filename",
        "corrected_data",
        "correction_instruction",
        "verified_data",
        "last_saved_record",
        "final_confirmation",
        "manual_confirmation",
    ]:

        st.session_state.pop(
            key,
            None
        )


# =========================================================
# INITIALIZE AUTH STATE
# =========================================================

initialize_auth_state()


# Restore an existing temporary session.
if not st.session_state["authenticated"]:

    restore_session()


# =========================================================
# LOGIN / SIGNUP SCREEN
# =========================================================

if not st.session_state["authenticated"]:

    st.title(
        "📄 Credential Extraction Assistant"
    )

    st.info(
        "Please sign in to access the credential "
        "extraction workspace."
    )

    login_tab, signup_tab = st.tabs(
        [
            "🔑 Login",
            "📝 Create Account",
        ]
    )


    # =====================================================
    # LOGIN
    # =====================================================

    with login_tab:

        st.subheader(
            "Login"
        )

        login_email = st.text_input(
            "Email",
            key="login_email"
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔐 Login",
            type="primary",
            key="login_button"
        ):

            if not login_email.strip():

                st.error(
                    "Please enter your email."
                )

            elif not login_password:

                st.error(
                    "Please enter your password."
                )

            else:

                try:

                    login_user(
                        login_email.strip(),
                        login_password
                    )

                    st.success(
                        "✓ Login successful."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Login failed: {e}"
                    )


    # =====================================================
    # SIGN UP
    # =====================================================

    with signup_tab:

        st.subheader(
            "Create Account"
        )

        signup_email = st.text_input(
            "Email",
            key="signup_email"
        )

        signup_password = st.text_input(
            "Password",
            type="password",
            key="signup_password"
        )

        signup_password_confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_password_confirm"
        )

        if st.button(
            "📝 Create Account",
            type="primary",
            key="signup_button"
        ):

            if not signup_email.strip():

                st.error(
                    "Please enter your email."
                )

            elif not signup_password:

                st.error(
                    "Please enter a password."
                )

            elif len(signup_password) < 6:

                st.error(
                    "Password must be at least 6 characters."
                )

            elif signup_password != signup_password_confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                try:

                    status, user = signup_user(
                        signup_email.strip(),
                        signup_password
                    )

                    if status == "signup_confirmation_required":

                        st.success(
                            "✓ Account created successfully."
                        )

                        st.info(
                            "Please check your email and click "
                            "the confirmation link before logging in."
                        )

                    else:

                        st.success(
                            "✓ Account created and logged in."
                        )

                        st.rerun()

                except Exception as e:

                    st.error(
                        f"Account creation failed: {e}"
                    )


    st.stop()


# =========================================================
# AUTHENTICATED APPLICATION
# =========================================================

st.title(
    "📄 Credential Extraction Assistant"
)

st.info(
    "Phase 8 — Persistent Supabase Database"
)


# =========================================================
# USER INFORMATION / LOGOUT
# =========================================================

user_col1, user_col2 = st.columns(
    [4, 1]
)

with user_col1:

    st.success(
        f"Signed in as: "
        f"**{st.session_state.get('user_email', 'Unknown user')}**"
    )


with user_col2:

    if st.button(
        "🚪 Logout",
        key="logout_button"
    ):

        logout_user()

        st.rerun()


st.divider()


# =========================================================
# PDF UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "Upload a PDF document",
    type=["pdf"]
)


if uploaded_file:

    st.write(
        f"**File:** {uploaded_file.name}"
    )

    if st.button(
        "Process PDF",
        type="primary"
    ):

        try:

            # -------------------------------------------------
            # Step 1 — Validate PDF
            # -------------------------------------------------

            validate_pdf(
                uploaded_file
            )

            st.success(
                "✓ PDF validation successful."
            )


            # -------------------------------------------------
            # Step 2 — Extract PDF text
            # -------------------------------------------------

            with st.spinner(
                "Reading PDF..."
            ):

                document_text = (
                    extract_text_from_pdf(
                        uploaded_file
                    )
                )

            st.success(
                "✓ PDF text/OCR extraction successful."
            )


            # -------------------------------------------------
            # Step 3 — Gemini extraction
            # -------------------------------------------------

            with st.spinner(
                "Gemini is analyzing the document..."
            ):

                result = extract_structured_data(
                    document_text
                )

            st.success(
                "✓ Gemini extraction successful."
            )


            # -------------------------------------------------
            # Step 4 — Parse JSON
            # -------------------------------------------------

            try:

                extracted_data = json.loads(
                    result
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    "Gemini returned invalid JSON."
                ) from exc


            # -------------------------------------------------
            # Step 5 — Store temporary data
            # -------------------------------------------------

            st.session_state[
                "extracted_data"
            ] = extracted_data

            st.session_state[
                "document_text"
            ] = document_text

            st.session_state[
                "processed_filename"
            ] = uploaded_file.name

            # Clear previous workflow state.
            st.session_state.pop(
                "corrected_data",
                None
            )

            st.session_state.pop(
                "correction_instruction",
                None
            )

            st.session_state.pop(
                "verified_data",
                None
            )

            st.session_state.pop(
                "last_saved_record",
                None
            )

            st.session_state.pop(
                "final_confirmation",
                None
            )

            st.session_state.pop(
                "manual_confirmation",
                None
            )


        except Exception as e:

            st.error(
                f"Processing failed: {e}"
            )


# =========================================================
# HUMAN VERIFICATION
# =========================================================

if "extracted_data" in st.session_state:

    st.divider()

    st.header(
        "🔎 Review & Verify Extracted Data"
    )

    st.warning(
        "Please carefully review every field. "
        "You can manually correct information "
        "or use the natural-language correction "
        "assistant below."
    )

    extracted_data = st.session_state[
        "extracted_data"
    ]


    # =====================================================
    # MANUAL EDITING
    # =====================================================

    st.subheader(
        "Extracted Information"
    )

    edited_data = {}

    for field in EXTRACTION_FIELDS:

        current_value = extracted_data.get(
            field,
            ""
        )

        edited_data[field] = st.text_input(
            field,
            value=str(current_value),
            key=f"manual_{field}"
        )


    # =====================================================
    # NATURAL-LANGUAGE CORRECTION
    # =====================================================

    st.divider()

    st.subheader(
        "💬 Natural-Language Correction"
    )

    st.write(
        "Instead of editing a field manually, "
        "you can describe the correction in normal language."
    )

    st.caption(
        'Example: "Change the amount to PKR 4,500,000."'
    )

    correction_instruction = st.text_area(
        "Describe your correction",
        placeholder=(
            "Example: Change the client name to ABC Construction "
            "and the amount to PKR 4,500,000."
        ),
        height=100,
        key="correction_instruction"
    )


    if st.button(
        "✨ Apply Correction",
        type="secondary"
    ):

        if not correction_instruction.strip():

            st.error(
                "Please enter a correction instruction."
            )

        else:

            try:

                # Build the current record from the
                # manually edited fields.
                current_record = {
                    field: edited_data.get(
                        field,
                        ""
                    )
                    for field in EXTRACTION_FIELDS
                }

                with st.spinner(
                    "Gemini is applying your correction..."
                ):

                    corrected_data = (
                        apply_natural_language_correction(
                            current_record,
                            correction_instruction
                        )
                    )

                st.session_state[
                    "corrected_data"
                ] = corrected_data

                # Reset final confirmation because
                # the record has changed.
                st.session_state.pop(
                    "final_confirmation",
                    None
                )

                st.success(
                    "✓ Correction applied. "
                    "Please review the updated values below."
                )


            except Exception as e:

                st.error(
                    f"Correction failed: {e}"
                )


    # =====================================================
    # CORRECTED DATA
    # =====================================================

    if "corrected_data" in st.session_state:

        st.divider()

        st.subheader(
            "🔄 Corrected Record — Review Again"
        )

        st.warning(
            "The correction has NOT been saved. "
            "Review these values carefully before confirmation."
        )

        corrected_data = st.session_state[
            "corrected_data"
        ]

        final_data = {}

        for field in EXTRACTION_FIELDS:

            final_value = corrected_data.get(
                field,
                ""
            )

            final_data[field] = st.text_input(
                field,
                value=str(final_value),
                key=f"corrected_{field}"
            )


        st.divider()

        st.subheader(
            "Confirm Record"
        )

        st.write(
            "After reviewing the final values, "
            "confirm that the record is correct."
        )

        confirmed = st.checkbox(
            "I have reviewed and verified all fields.",
            key="final_confirmation"
        )


        # =================================================
        # SAVE CORRECTED RECORD
        # =================================================

        if st.button(
            "✓ Confirm & Save Record",
            type="primary",
            key="corrected_save_button"
        ):

            if not confirmed:

                st.error(
                    "Please confirm that you have reviewed "
                    "all fields before saving."
                )

            else:

                try:

                    # -----------------------------------------
                    # Normalize final human-approved data
                    # -----------------------------------------

                    normalized_record = normalize_record(
                        final_data
                    )


                    # -----------------------------------------
                    # Create database manager
                    # -----------------------------------------

                    db = DatabaseManager()


                    # -----------------------------------------
                    # Restore authenticated Supabase session
                    # -----------------------------------------

                    db.set_user_session(
                        st.session_state["access_token"],
                        st.session_state["refresh_token"]
                    )


                    # -----------------------------------------
                    # Save verified record
                    # -----------------------------------------

                    saved_record = db.insert_credential(
                        normalized_record,
                        document_filename=st.session_state.get(
                            "processed_filename"
                        )
                    )


                    # -----------------------------------------
                    # Temporary UI state
                    # -----------------------------------------

                    st.session_state[
                        "verified_data"
                    ] = normalized_record

                    st.session_state[
                        "last_saved_record"
                    ] = saved_record


                    st.success(
                        "✓ Record verified and saved successfully "
                        "to the Supabase database."
                    )

                    st.info(
                        f"Database Record ID: "
                        f"{saved_record['id']}"
                    )


                except Exception as exc:

                    st.error(
                        f"Unable to save record: {exc}"
                    )


    else:

        # =================================================
        # CONFIRMATION WITHOUT AI CORRECTION
        # =================================================

        st.divider()

        st.subheader(
            "Confirm Record"
        )

        st.write(
            "You can manually edit the fields above "
            "and confirm the record without using "
            "natural-language correction."
        )

        confirmed_manual = st.checkbox(
            "I have reviewed and verified all fields.",
            key="manual_confirmation"
        )


        if st.button(
            "✓ Confirm & Save Record",
            type="primary",
            key="manual_save_button"
        ):

            if not confirmed_manual:

                st.error(
                    "Please confirm that you have reviewed "
                    "all fields before saving."
                )

            else:

                try:

                    # -----------------------------------------
                    # Normalize final manually reviewed data
                    # -----------------------------------------

                    normalized_record = normalize_record(
                        edited_data
                    )


                    # -----------------------------------------
                    # Create database manager
                    # -----------------------------------------

                    db = DatabaseManager()


                    # -----------------------------------------
                    # Restore authenticated Supabase session
                    # -----------------------------------------

                    db.set_user_session(
                        st.session_state["access_token"],
                        st.session_state["refresh_token"]
                    )


                    # -----------------------------------------
                    # Save verified record
                    # -----------------------------------------

                    saved_record = db.insert_credential(
                        normalized_record,
                        document_filename=st.session_state.get(
                            "processed_filename"
                        )
                    )


                    # -----------------------------------------
                    # Temporary UI state
                    # -----------------------------------------

                    st.session_state[
                        "verified_data"
                    ] = normalized_record

                    st.session_state[
                        "last_saved_record"
                    ] = saved_record


                    st.success(
                        "✓ Record verified and saved successfully "
                        "to the Supabase database."
                    )

                    st.info(
                        f"Database Record ID: "
                        f"{saved_record['id']}"
                    )


                except Exception as exc:

                    st.error(
                        f"Unable to save record: {exc}"
                    )


# =========================================================
# LAST SAVED RECORD
# =========================================================

if "last_saved_record" in st.session_state:

    st.divider()

    st.subheader(
        "💾 Last Saved Record"
    )

    st.json(
        st.session_state[
            "last_saved_record"
        ]
    )
