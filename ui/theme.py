import streamlit as st


def apply_app_theme():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(
                135deg,
                #f8fbff 0%,
                #eef6ff 50%,
                #f7f2ff 100%
            );
        }

        .ai-hero {
            padding: 28px;
            margin-bottom: 20px;
            border-radius: 20px;
            background: linear-gradient(
                135deg,
                #0f5bea,
                #6546d9,
                #8b5cf6
            );
            color: white;
        }

        .ai-hero h1 {
            color: white !important;
            margin: 0;
        }

        .ai-hero p {
            color: white !important;
            margin-bottom: 0;
        }

        .ai-badge {
            display: inline-block;
            padding: 5px 12px;
            margin-bottom: 10px;
            border-radius: 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 12px;
            font-weight: bold;
        }

        .status-grid {
            display: grid;
            grid-template-columns:
                repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }

        .status-card {
            padding: 18px;
            border-radius: 14px;
            background: white;
            border: 1px solid #dbe7f5;
            box-shadow:
                0 4px 14px rgba(15,23,42,0.06);
        }

        .status-title {
            color: #64748b;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .status-value {
            color: #172554;
            font-size: 15px;
            font-weight: bold;
            margin-top: 5px;
        }

        .workflow {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 25px;
        }

        .workflow-step {
            flex: 1;
            padding: 10px;
            text-align: center;
            border-radius: 10px;
            background: white;
            border: 1px solid #dbe7f5;
            color: #475569;
            font-weight: bold;
            font-size: 13px;
        }

        .workflow-arrow {
            color: #8b5cf6;
            font-weight: bold;
        }

        @media (max-width: 768px) {
            .status-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .workflow {
                flex-direction: column;
            }

            .workflow-arrow {
                display: none;
            }

            .workflow-step {
                width: 100%;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_ai_hero():
    st.markdown(
        """
        <div class="ai-hero">
            <div class="ai-badge">
                AI DOCUMENT INTELLIGENCE
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
    st.markdown(
        """
        <div class="status-grid">

            <div class="status-card">
                <div class="status-title">
                    AI Engine
                </div>
                <div class="status-value">
                    Gemini
                </div>
            </div>

            <div class="status-card">
                <div class="status-title">
                    Database
                </div>
                <div class="status-value">
                    Supabase PostgreSQL
                </div>
            </div>

            <div class="status-card">
                <div class="status-title">
                    Security
                </div>
                <div class="status-value">
                    RLS Protected
                </div>
            </div>

            <div class="status-card">
                <div class="status-title">
                    Processing
                </div>
                <div class="status-value">
                    PDF Intelligence
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow():
    st.markdown(
        """
        <div class="workflow">

            <div class="workflow-step">
                1. Upload
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                2. AI Extract
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                3. Review
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                4. Correct
            </div>

            <div class="workflow-arrow">
                →
            </div>

            <div class="workflow-step">
                5. Save
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
