import streamlit as st


def apply_app_theme():
    """Apply the visual theme for the AI Credential Intelligence app."""

    st.markdown(
        """
        <style>

        /* =========================================================
           GLOBAL
        ========================================================= */

        .stApp {
            background:
                linear-gradient(
                    135deg,
                    #f8fbff 0%,
                    #eef6ff 45%,
                    #f7f2ff 100%
                );
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        /* =========================================================
           MAIN TITLE
        ========================================================= */

        .ai-hero {
            padding: 1.8rem 2rem;
            margin-bottom: 1.5rem;
            border-radius: 22px;
            background:
                linear-gradient(
                    135deg,
                    #0f5bea 0%,
                    #6546d9 55%,
                    #8b5cf6 100%
                );
            box-shadow:
                0 12px 35px rgba(37, 99, 235, 0.18);
            color: white;
        }

        .ai-hero h1 {
            margin: 0;
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.5px;
        }

        .ai-hero p {
            margin: 0.45rem 0 0 0;
            font-size: 1rem;
            opacity: 0.92;
        }

        .ai-badge {
            display: inline-block;
            margin-bottom: 0.7rem;
            padding: 0.28rem 0.75rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.18);
            border: 1px solid rgba(255,255,255,0.28);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.4px;
        }

        /* =========================================================
           SECTION HEADERS
           ========================================================= */

        h1, h2, h3 {
            color: #172554;
            font-weight: 750;
        }

        .section-card {
            padding: 1.25rem 1.4rem;
            margin: 1rem 0;
            border-radius: 16px;
            background: rgba(255,255,255,0.88);
            border: 1px solid #dbe7f5;
            box-shadow:
                0 5px 18px rgba(15, 23, 42, 0.05);
        }

        /* =========================================================
           STATUS CARDS
           ========================================================= */

        .status-grid {
            display: grid;
            grid-template-columns:
                repeat(4, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 1rem 0 1.5rem 0;
        }

        .status-card {
            padding: 1rem;
            border-radius: 15px;
            background: rgba(255,255,255,0.9);
            border: 1px solid #dbe7f5;
            box-shadow:
                0 5px 16px rgba(15, 23, 42, 0.05);
        }

        .status-title {
            font-size: 0.75rem;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-value {
            margin-top: 0.25rem;
            font-size: 0.95rem;
            font-weight: 750;
            color: #172554;
        }

        /* =========================================================
           WORKFLOW
           ========================================================= */

        .workflow {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.35rem;
            margin: 1rem 0 1.6rem 0;
        }

        .workflow-step {
            flex: 1;
            text-align: center;
            padding: 0.7rem 0.35rem;
            border-radius: 12px;
            background: #ffffff;
            border: 1px solid #dbe7f5;
            color: #64748b;
            font-size: 0.78rem;
            font-weight: 700;
        }

        .workflow-arrow {
            color: #8b5cf6;
            font-weight: 800;
        }

        /* =========================================================
           FILE UPLOADER
           ========================================================= */

        [data-testid="stFileUploader"] {
            background:
                linear-gradient(
                    135deg,
                    #eaf6ff 0%,
                    #f1edff 100%
                );
            border: 2px solid #9fc5ff;
            border-radius: 16px;
            padding: 0.7rem;
            box-shadow:
                0 6px 18px rgba(37, 99, 235, 0.08);
        }

        [data-testid="stFileUploader"] label {
            color: #172554 !important;
            font-weight: 800 !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255,255,255,0.72);
            border-radius: 12px;
        }

        /* =========================================================
           SELECTBOX
           ========================================================= */

        [data-testid="stSelectbox"] label {
            color: #172554 !important;
            font-weight: 800 !important;
        }

        [data-testid="stSelectbox"] > div > div {
            border-radius: 10px;
            border: 1.5px solid #9fc5ff;
            background: #ffffff;
        }

        /* =========================================================
           BUTTONS
           ========================================================= */

        .stButton > button {
            border-radius: 10px;
            font-weight: 750;
            border: 1px solid #c7d8f5;
            transition:
                transform 0.15s ease,
                box-shadow 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow:
                0 6px 15px rgba(37, 99, 235, 0.14);
        }

        /* =========================================================
           INPUTS
           ========================================================= */

        .stTextInput label,
        .stTextArea label,
        .stNumberInput label {
            color: #172554 !important;
            font-weight: 700 !important;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {
            border-radius: 9px;
            border: 1px solid #cbdcf4;
        }

        /* =========================================================
           DATAFRAME
           ========================================================= */

        [data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid #dbe7f5;
            box-shadow:
                0 5px 16px rgba(15, 23, 42, 0.05);
        }

        /* =========================================================
           INFO / SUCCESS / WARNING
           ========================================================= */

        [data-testid="stAlert"] {
            border-radius: 12px;
        }

        /* =========================================================
           DIVIDERS
           ========================================================= */

        hr {
            border: none;
            border-top: 1px solid #dbe7f5;
            margin: 1.5rem 0;
        }

        /* =========================================================
           MOBILE
           ========================================================= */

        @media (max-width: 768px) {

            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .ai-hero {
                padding: 1.35rem;
                border-radius: 17px;
            }

            .ai-hero h1 {
                font-size: 1.7rem;
            }

            .status-grid {
                grid-template-columns:
                    repeat(2, minmax(0, 1fr));
            }

            .workflow {
                flex-direction: column;
            }

            .workflow-step {
                width: 100%;
            }

            .workflow-arrow {
                display: none;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_ai_hero():
    """Render the main AI application header."""

    st.markdown(
        """
        <div class="ai-hero">

            <div class="ai-badge">
                ✦ AI DOCUMENT INTELLIGENCE
            </div>

            <h1>
                Credential Intelligence
            </h1>

            <p>
                AI-powered document extraction,
                human verification and secure
                credential management.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_cards():
    """Render high-level application status cards."""

    st.markdown(
        """
        <div class="status-grid">

            <div class="status-card">
                <div class="status-title">
                    AI Engine
                </div>
                <div class="status-value">
                    ✦ Gemini
                </div>
            </div>

            <div class="status-card">
                <div class="status-title">
                    Database
                </div>
                <div class="status-value">
                    ● Supabase PostgreSQL
                </div>
            </div>

            <div class="status-card">
                <div class="status-title">
                    Security
                </div>
                <div class="status-value">
                    🔒 RLS Protected
                </div>
            </div>

            <div class="status-card">
                <div class="status-title">
                    Processing
                </div>
                <div class="status-value">
                    📄 PDF Intelligence
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow():
    """Render the document processing workflow."""

    st.markdown(
        """
        <div class="workflow">

            <div class="workflow-step">
                ① Upload
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                ② AI Extract
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                ③ Review
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                ④ Correct
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                ⑤ Save
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
