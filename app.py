import streamlit as st

from ui.theme import (
    apply_app_theme,
    render_ai_hero,
    render_status_cards,
    render_workflow,
)

from ui.auth_ui import (
    get_supabase_client,
    render_auth_ui,
    logout_user,
)

from ui.upload_ui import render_upload_ui
from ui.review_ui import render_review_ui
from ui.correction_ui import render_correction_ui
from ui.records_ui import render_records_ui
from ui.workspace_ui import render_workspace_ui


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    
    page_title="Credential Extraction Chatbot",
    page_icon="📄",
    layout="wide",
)

apply_app_theme()

# ============================================================
# SUPABASE CLIENT
# ============================================================

supabase = get_supabase_client()


# ============================================================
# AUTHENTICATION
# ============================================================

authenticated = render_auth_ui(
    supabase
)

if not authenticated:
    st.stop()


# ============================================================
# APPLICATION HEADER
# ============================================================

render_ai_hero()
render_status_cards()
render_workflow()

# ============================================================
# V2 WORKSPACE MANAGEMENT
# ============================================================

render_workspace_ui(
    supabase
)
# ============================================================
# USER INFORMATION / LOGOUT
# ============================================================

user_email = st.session_state.get(
    "user_email"
)

if user_email:

    col1, col2 = st.columns(
        [4, 1]
    )

    with col1:

        st.caption(
            f"Logged in as: {user_email}"
        )

    with col2:

        if st.button(
            "Logout",
            key="logout_button",
        ):

            logout_user(
                supabase
            )

            st.rerun()


# ============================================================
# DOCUMENT SELECTION & PROCESSING
# ============================================================

render_upload_ui()


# ============================================================
# HUMAN REVIEW
# ============================================================

render_review_ui()


# ============================================================
# NATURAL-LANGUAGE AI CORRECTION
# ============================================================

render_correction_ui()


# ============================================================
# SAVED RECORDS
# ============================================================

render_records_ui()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Credential Extraction Chatbot • "
    "Supabase PostgreSQL • Google Gemini"
)
