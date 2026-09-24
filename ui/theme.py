import streamlit as st


def apply_app_theme():
    """Apply the global visual theme."""

    st.markdown(
        """
        <style>
        .stApp {
            background:
                linear-gradient(
                    135deg,
                    #f8fbff 0%,
                    #eef6ff 50%,
                    #f7f2ff 100%
                );
        }

        .main .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: #172554;
        }

        [data-testid="stFileUploader"] {
            background: #f8fbff;
            border: 2px solid #bfdbfe;
            border-radius: 16px;
            padding: 0.5rem;
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 700;
        }

        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
        }

        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_ai_hero():
    """Render the main application header."""

    st.markdown(
        "### ✦ AI DOCUMENT INTELLIGENCE"
    )

    st.title("Credential Intelligence")

    st.markdown(
        """
        **AI-powered document extraction, human verification,
        and secure credential management.**
        """
    )

    st.divider()


def render_status_cards():
    """Render application status information."""

    st.subheader("System Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.info(
            "**✦ AI ENGINE**\n\n"
            "Gemini"
        )

    with col2:
        st.success(
            "**● DATABASE**\n\n"
            "Supabase PostgreSQL"
        )

    with col3:
        st.success(
            "**🔒 SECURITY**\n\n"
            "RLS Protected"
        )

    with col4:
        st.info(
            "**📄 PROCESSING**\n\n"
            "PDF Intelligence"
        )

    st.divider()


def render_workflow():
    """Render the document processing workflow."""

    st.subheader("Document Processing Workflow")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown("### ①")
        st.caption("Upload")

    with col2:
        st.markdown("### ②")
        st.caption("AI Extract")

    with col3:
        st.markdown("### ③")
        st.caption("Review")

    with col4:
        st.markdown("### ④")
        st.caption("Correct")

    with col5:
        st.markdown("### ⑤")
        st.caption("Save")

    st.divider()
