import re

import streamlit as st
from supabase import create_client


MIN_PASSWORD_LENGTH = 6
MAX_EMAIL_LENGTH = 320
MAX_PASSWORD_LENGTH = 256

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


# ============================================================
# SUPABASE CLIENT
# ============================================================

@st.cache_resource
def get_supabase_client():
    """Create and cache the application's Supabase client."""

    try:
        url = st.secrets["SUPABASE_URL"]
        publishable_key = st.secrets[
            "SUPABASE_PUBLISHABLE_KEY"
        ]
    except Exception as exc:
        raise RuntimeError(
            "Supabase authentication configuration is missing."
        ) from exc

    if not url or not publishable_key:
        raise RuntimeError(
            "Supabase authentication configuration is incomplete."
        )

    try:
        return create_client(
            url,
            publishable_key,
        )
    except Exception as exc:
        raise RuntimeError(
            "Unable to initialize the Supabase client."
        ) from exc


# ============================================================
# AUTHENTICATION STATE
# ============================================================

def initialize_auth_state():
    """Initialize temporary authentication state."""

    defaults = {
        "authenticated": False,
        "access_token": None,
        "refresh_token": None,
        "user_email": None,
        "user_id": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _clear_auth_state():
    """Clear temporary authentication state."""

    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None
    st.session_state.user_id = None


def _clear_workflow_state():
    """
    Clear temporary document-processing state.

    Nothing in this function affects the permanent Supabase
    database.
    """

    workflow_keys = [
        "selected_pdf_index",
        "uploaded_file_count",
        "uploaded_file_signature",
        "selected_file_names",
        "active_pdf_selector",
        "advance_to_next_pdf",
        "processing_complete",
        "processed_pdf_name",
        "extracted_text",
        "extracted_data",
        "edited_data",
        "corrected_data",
        "final_data",
        "verified_data",
        "final_confirmation",
        "final_confirmation_checkbox",
        "correction_instruction",
        "correction_instruction_input",
        "my_credentials",
    ]

    for key in workflow_keys:
        st.session_state.pop(
            key,
            None,
        )


def _clear_login_form_state():
    """Clear temporary login/signup form values."""

    form_keys = [
        "login_",
        "login_password",
        "signup__form",
        "signup_password_form",
        "signup_password_confirm_form",
    ]

    for key in form_keys:
        st.session_state.pop(
            key,
            None,
        )


# ============================================================
# INPUT VALIDATION
# ============================================================

def _validate_email(email):
    """Validate and normalize an email address."""

    if not isinstance(
        email,
        str,
    ):
        raise ValueError(
            "Email address is invalid."
        )

    email = email.strip()

    if not email:
        raise ValueError(
            "Please enter an email address."
        )

    if len(email) > MAX_EMAIL_LENGTH:
        raise ValueError(
            "Email address is too long."
        )

    if not EMAIL_PATTERN.match(email):
        raise ValueError(
            "Please enter a valid email address."
        )

    return email


def _validate_password(password):
    """Validate password input before sending it to Supabase."""

    if not isinstance(
        password,
        str,
    ):
        raise ValueError(
            "Password is invalid."
        )

    if not password:
        raise ValueError(
            "Please enter a password."
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must contain at least "
            f"{MIN_PASSWORD_LENGTH} characters."
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            "Password is too long."
        )

    return password


# ============================================================
# SESSION RESTORATION
# ============================================================

def restore_session(supabase):
    """
    Restore and validate an existing Supabase session.

    Returns:
        True  -> valid authenticated session
        False -> no valid session
    """

    try:
        session = supabase.auth.get_session()

        if session is None:
            _clear_auth_state()
            return False

        access_token = getattr(
            session,
            "access_token",
            None,
        )

        refresh_token = getattr(
            session,
            "refresh_token",
            None,
        )

        user = getattr(
            session,
            "user",
            None,
        )

        if not access_token or not refresh_token or user is None:
            _clear_auth_state()
            return False

        user_email = getattr(
            user,
            "email",
            None,
        )

        if not user_email:
            _clear_auth_state()
            return False

        st.session_state.access_token = (
            access_token
        )

        st.session_state.refresh_token = (
            refresh_token
        )

        st.session_state.user_email = (
            user_email
        )
        
        st.session_state.user_id = (
            user.id
        )
        st.session_state.authenticated = True

        return True

    except Exception:
        _clear_auth_state()
        return False


# ============================================================
# LOGIN
# ============================================================

def login_user(
    supabase,
    email,
    password,
):
    """Authenticate an existing Supabase user."""

    email = _validate_email(
        email
    )

    password = _validate_password(
        password
    )

    try:
        response = (
            supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )
        )

    except Exception as exc:
        raise ValueError(
            "Login failed. Please verify your email "
            "and password."
        ) from exc

    session = response.session
    user = response.user

    if session is None or user is None:
        raise ValueError(
            "Login failed. Please verify your credentials."
        )

    access_token = getattr(
        session,
        "access_token",
        None,
    )

    refresh_token = getattr(
        session,
        "refresh_token",
        None,
    )

    user_email = getattr(
        user,
        "email",
        None,
    )

    if (
        not access_token
        or not refresh_token
        or not user_email
    ):
        raise ValueError(
            "Login succeeded but the authentication "
            "session was incomplete."
        )

    st.session_state.access_token = (
        access_token
    )

    st.session_state.refresh_token = (
        refresh_token
    )

    st.session_state.authenticated = True

    st.session_state.user_email = (
        user_email
    )
    
    st.session_state.user_id = (
        user.id
    )

# ============================================================
# SIGNUP
# ============================================================

def signup_user(
    supabase,
    email,
    password,
):
    """Create a new Supabase user account."""

    email = _validate_email(
        email
    )

    password = _validate_password(
        password
    )

    try:
        response = (
            supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                }
            )
        )

    except Exception as exc:
        raise ValueError(
            "Account creation failed. "
            "Please verify the information and try again."
        ) from exc

    if response.user is None:
        raise ValueError(
            "Account creation failed."
        )

    # Supabase may return a user without a session when
    # email confirmation is enabled.
    if response.session is not None:

        access_token = getattr(
            response.session,
            "access_token",
            None,
        )

        refresh_token = getattr(
            response.session,
            "refresh_token",
            None,
        )

        if not access_token or not refresh_token:
            raise ValueError(
                "Account was created but the authentication "
                "session could not be established."
            )

        st.session_state.access_token = (
            access_token
        )

        st.session_state.refresh_token = (
            refresh_token
        )

        st.session_state.authenticated = True

        st.session_state.user_email = (
            response.user.email
        )

        st.session_state.user_id = (
        response.user.id
        )
    return response


# ============================================================
# LOGOUT
# ============================================================

def logout_user(supabase):
    """Log out the current user and clear temporary state."""

    try:
        supabase.auth.sign_out()
    except Exception:
        # Local authentication state must still be cleared
        # even if the remote sign-out request fails.
        pass

    _clear_auth_state()
    _clear_workflow_state()
    _clear_login_form_state()


# ============================================================
# LOGIN / SIGNUP UI
# ============================================================

def render_auth_ui(supabase):
    """
    Render the login and account-creation interface.

    Returns:
        True  -> authenticated user
        False -> unauthenticated user
    """

    initialize_auth_state()

    # --------------------------------------------------------
    # Restore existing Supabase session.
    # --------------------------------------------------------

    if not st.session_state.authenticated:
        restore_session(
            supabase
        )

    if st.session_state.authenticated:
        return True

    st.title(
        "📄 Credential Extraction Chatbot"
    )

    st.write(
        "Secure document extraction and credential management."
    )

    login_tab, signup_tab = st.tabs(
        [
            "Login",
            "Create Account",
        ]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        st.subheader(
            "Login"
        )

        login_email = st.text_input(
            "Email",
            key="login_email",
            autocomplete="email",
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            autocomplete="current-password",
        )

        if st.button(
            "Login",
            type="primary",
            key="login_button",
        ):

            try:

                login_user(
                    supabase,
                    login_email,
                    login_password,
                )

                # Clear form values after successful login.
                _clear_login_form_state()

                st.success(
                    "Login successful."
                )

                st.rerun()

            except ValueError as exc:

                st.error(
                    str(exc)
                )

            except Exception:

                st.error(
                    "Login could not be completed. "
                    "Please try again."
                )

    # ========================================================
    # SIGNUP
    # ========================================================

    with signup_tab:

        st.subheader(
            "Create Account"
        )

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

            try:

                email = _validate_email(
                    signup_email
                )

                password = _validate_password(
                    signup_password
                )

                if password != signup_password_confirm:
                    raise ValueError(
                        "Passwords do not match."
                    )

                response = signup_user(
                    supabase,
                    email,
                    password,
                )

                if response.session is None:

                    st.success(
                        "Account created successfully. "
                        "Please check your email to confirm "
                        "your account before logging in."
                    )

                else:

                    _clear_login_form_state()

                    st.success(
                        "Account created successfully."
                    )

                    st.rerun()

            except ValueError as exc:

                st.error(
                    str(exc)
                )

            except Exception:

                st.error(
                    "Account creation could not be completed. "
                    "Please try again."
                )

    return False
