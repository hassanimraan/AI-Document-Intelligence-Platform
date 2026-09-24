import streamlit as st
from supabase import create_client

from ui.common import reset_current_document_workflow


# ============================================================
# SUPABASE CLIENT
# ============================================================

@st.cache_resource
def get_supabase_client():
    """Create and cache the Supabase client."""

    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_PUBLISHABLE_KEY"],
    )


# ============================================================
# AUTHENTICATION STATE
# ============================================================

def initialize_auth_state():
    """Initialize temporary authentication state."""

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "access_token" not in st.session_state:
        st.session_state.access_token = None

    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None

    if "user_email" not in st.session_state:
        st.session_state.user_email = None


# ============================================================
# SESSION RESTORATION
# ============================================================

def restore_session(supabase):
    """
    Restore an existing Supabase authentication session.
    """

    try:

        session = supabase.auth.get_session()

        if session is not None:

            if session.access_token and session.refresh_token:

                st.session_state.access_token = (
                    session.access_token
                )

                st.session_state.refresh_token = (
                    session.refresh_token
                )

                st.session_state.authenticated = True

                if session.user:
                    st.session_state.user_email = (
                        session.user.email
                    )

                return True

    except Exception:
        pass

    return False


# ============================================================
# LOGIN
# ============================================================

def login_user(
    supabase,
    email,
    password,
):
    """Authenticate an existing user."""

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

    st.session_state.access_token = (
        session.access_token
    )

    st.session_state.refresh_token = (
        session.refresh_token
    )

    st.session_state.authenticated = True
    st.session_state.user_email = user.email


# ============================================================
# SIGNUP
# ============================================================

def signup_user(
    supabase,
    email,
    password,
):
    """Create a new Supabase user account."""

    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )

    if response.user is None:
        raise ValueError(
            "Account creation failed."
        )

    if response.session is not None:

        st.session_state.access_token = (
            response.session.access_token
        )

        st.session_state.refresh_token = (
            response.session.refresh_token
        )

        st.session_state.authenticated = True

        st.session_state.user_email = (
            response.user.email
        )

    return response


# ============================================================
# LOGOUT
# ============================================================

def logout_user(supabase):
    """Log out the current user."""

    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None

    workflow_keys = [
        "selected_pdf_index",
        "processed_pdf_name",
        "extracted_text",
        "extracted_data",
        "edited_data",
        "corrected_data",
        "final_data",
        "verified_data",
        "final_confirmation",
        "correction_instruction",
        "selected_file_names",
    ]

    for key in workflow_keys:
        st.session_state.pop(key, None)


# ============================================================
# LOGIN / SIGNUP UI
# ============================================================

def render_auth_ui(supabase):
    """
    Render the login and account-creation interface.

    Returns:
        True  -> authentication successful/currently active
        False -> user is not authenticated
    """

    initialize_auth_state()

    if not st.session_state.authenticated:
        restore_session(supabase)

    if st.session_state.authenticated:
        return True

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

            if not login_email:

                st.error(
                    "Please enter an email address."
                )

            elif not login_password:

                st.error(
                    "Please enter a password."
                )

            else:

                try:

                    login_user(
                        supabase,
                        login_email.strip(),
                        login_password,
                    )

                    st.success(
                        "Login successful."
                    )

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

        with st.form(
            "create_account_form",
            clear_on_submit=False,
        ):

            signup_email = st.text_input(
                "Email",
                key="signup_email_form",
                autocomplete="email",
            )

            signup_password = st.text_input(
                "Password",
                type="password",
                key="signup_password_form",
                autocomplete="new-password",
            )

            signup_password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                key="signup_password_confirm_form",
                autocomplete="new-password",
            )

            create_account_submitted = (
                st.form_submit_button(
                    "Create Account",
                    type="primary",
                )
            )

        if create_account_submitted:

            email = signup_email.strip()
            password = signup_password
            password_confirm = (
                signup_password_confirm
            )

            if not email:

                st.error(
                    "Please enter an email address."
                )

            elif not password:

                st.error(
                    "Please enter a password."
                )

            elif password != password_confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                try:

                    response = signup_user(
                        supabase,
                        email,
                        password,
                    )

                    if response.session is None:

                        st.success(
                            "Account created successfully. "
                            "Please check your email to "
                            "confirm your account."
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

    return False
