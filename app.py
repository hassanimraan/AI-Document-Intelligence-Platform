import streamlit as st

from ui.theme import apply_app_theme

from ui.auth_ui import (
    get_supabase_client,
    render_auth_ui,
    logout_user,
)

from ui.dashboard_ui import render_dashboard


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="📄",
    layout="wide",
)


# ============================================================
# APPLICATION THEME
# ============================================================

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
# MAIN DASHBOARD
# ============================================================

render_dashboard(
    supabase
)


# ============================================================
# USER INFORMATION / LOGOUT
# ============================================================

user_email = st.session_state.get(
    "user_email"
)

if user_email:

    st.divider()

    col1, col2 = st.columns(
        [5, 1]
    )

    with col1:

        st.caption(
            f"Logged in as: {user_email}"
        )

    with col2:

        if st.button(
            "Logout",
            key="logout_button",
            use_container_width=True,
        ):

            logout_user(
                supabase
            )

            st.rerun()


# ============================================================
# TEMPORARILY DISABLED OLD PROCESSING UI
# ============================================================
#
# These modules remain in the project.
# They will be connected to the new workflow later:
#
# render_upload_ui()
# render_review_ui()
# render_correction_ui()
# render_records_ui()
#
# Do NOT delete those files.
# ============================================================


# ============================================================
# FOOTER
# ============================================================

st.caption(
    "AI Document Intelligence • "
    "Supabase PostgreSQL • Google Gemini"
)
