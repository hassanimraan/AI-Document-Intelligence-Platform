import streamlit as st


def _get_user_id():
    """Return the authenticated user ID."""
    user_id = st.session_state.get("user_id")

    if not user_id:
        raise ValueError("Authenticated user ID is not available.")

    return user_id


def load_workspaces(supabase):
    """Load active workspaces for the current user."""
    user_id = _get_user_id()

    response = (
        supabase
        .table("workspaces")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("created_at")
        .execute()
    )

    return response.data or []


def load_registers(supabase, workspace_id):
    """Load active registers belonging to a workspace."""
    response = (
        supabase
        .table("document_schemas")
        .select("*")
        .eq("workspace_id", workspace_id)
        .eq("is_active", True)
        .order("created_at")
        .execute()
    )

    return response.data or []


def create_workspace(supabase, name, description):
    """Create a new workspace."""
    name = name.strip()
    description = description.strip()

    if not name:
        raise ValueError("Workspace name is required.")

    user_id = _get_user_id()

    response = (
        supabase
        .table("workspaces")
        .insert(
            {
                "user_id": user_id,
                "name": name,
                "description": description or None,
                "is_active": True,
            }
        )
        .execute()
    )

    if not response.data:
        raise ValueError("Workspace could not be created.")

    return response.data[0]


def create_register(supabase, workspace_id, name, description):
    """Create a new register inside a workspace."""
    name = name.strip()
    description = description.strip()

    if not name:
        raise ValueError("Register name is required.")

    response = (
        supabase
        .table("document_schemas")
        .insert(
            {
                "workspace_id": workspace_id,
                "name": name,
                "description": description or None,
                "version": 1,
                "is_active": True,
            }
        )
        .execute()
    )

    if not response.data:
        raise ValueError("Register could not be created.")

    return response.data[0]


def render_dashboard(supabase):
    """Render the main application dashboard."""

    # ========================================================
    # COMPACT CENTERED HEADER
    # ========================================================

    st.markdown(
        "<div style='text-align:center; "
        "font-size:0.78rem; font-weight:700; "
        "letter-spacing:0.08em; color:#475569;'>"
        "✦ AI DOCUMENT INTELLIGENCE"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='text-align:center; "
        "font-size:2.4rem; font-weight:800; "
        "color:#172554; margin-top:0.05rem;'>"
        "Credential Intelligence"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='text-align:center; "
        "font-size:0.9rem; color:#64748b; "
        "margin-top:0.15rem;'>"
        "AI-powered document extraction, human verification, "
        "and secure credential management."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<hr style='margin:0.8rem 0 1.2rem 0; "
        "border:none; border-top:1px solid #e2e8f0;'>",
        unsafe_allow_html=True,
    )

    # ========================================================
    # COMPACT STYLING
    # ========================================================

    st.markdown(
        """
        <style>

        .system-item {
            padding: 0.55rem 0.7rem;
            margin-bottom: 0.45rem;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid #e2e8f0;
        }

        .system-label {
            font-size: 0.72rem;
            font-weight: 800;
            color: #475569;
        }

        .system-value {
            font-size: 0.82rem;
            color: #1e293b;
            margin-top: 0.1rem;
        }

        .workflow-step {
            padding: 0.3rem 0;
            font-size: 0.82rem;
            color: #334155;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # TWO-COLUMN DASHBOARD
    # ========================================================

    left_column, main_column = st.columns(
        [1, 3.6],
        gap="large",
    )

    # ========================================================
    # LEFT COLUMN
    # ========================================================

    with left_column:

        st.markdown("### System Overview")

        st.markdown(
            """
            <div class="system-item">
                <div class="system-label">✦ AI ENGINE</div>
                <div class="system-value">Gemini</div>
            </div>

            <div class="system-item">
                <div class="system-label">● DATABASE</div>
                <div class="system-value">Supabase PostgreSQL</div>
            </div>

            <div class="system-item">
                <div class="system-label">🔒 SECURITY</div>
                <div class="system-value">RLS Protected</div>
            </div>

            <div class="system-item">
                <div class="system-label">📄 PROCESSING</div>
                <div class="system-value">PDF Intelligence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Document Processing")

        st.markdown(
            """
            <div class="workflow-step">① Upload</div>
            <div class="workflow-step">② AI Extract</div>
            <div class="workflow-step">③ Review</div>
            <div class="workflow-step">④ Correct</div>
            <div class="workflow-step">⑤ Save</div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # MAIN COLUMN — WORKSPACES
    # ========================================================

    with main_column:

        st.markdown(
            "<div style='font-size:1.45rem; "
            "font-weight:750; color:#172554; "
            "margin-bottom:0.7rem;'>"
            "YOUR WORKSPACES"
            "</div>",
            unsafe_allow_html=True,
        )

        workspaces = load_workspaces(supabase)

        if not workspaces:

            st.info(
                "No workspaces yet. Create your first workspace below."
            )

        # ----------------------------------------------------
        # WORKSPACE BUTTONS
        # ----------------------------------------------------

        for workspace in workspaces:

            workspace_id = workspace["id"]
            workspace_name = workspace["name"]

            # Workspace button
            if st.button(
                f"Workspace — {workspace_name}",
                key=f"workspace_{workspace_id}",
                use_container_width=True,
            ):

                st.session_state[
                    "active_workspace_id"
                ] = workspace_id

                st.session_state[
                    "active_workspace_name"
                ] = workspace_name

                st.rerun()

            # Show registers directly under the workspace
            if (
                st.session_state.get(
                    "active_workspace_id"
                )
                == workspace_id
            ):

                registers = load_registers(
                    supabase,
                    workspace_id,
                )

                if not registers:

                    st.caption(
                        "└─ No registers yet"
                    )

                else:

                    for register in registers:

                        register_id = register["id"]
                        register_name = register["name"]

                        if st.button(
                            f"　└─ Register — {register_name}",
                            key=f"register_{register_id}",
                            use_container_width=True,
                        ):

                            st.session_state[
                                "active_schema_id"
                            ] = register_id

                            st.session_state[
                                "active_schema_name"
                            ] = register_name

                            st.session_state[
                                "register_setup_mode"
                            ] = True

                            st.rerun()

                st.markdown(
                    "<div style='height:0.45rem;'></div>",
                    unsafe_allow_html=True,
                )

        # ====================================================
        # ACTION BOXES
        # ====================================================

        action_col1, action_col2 = st.columns(2)

        # ----------------------------------------------------
        # ADD WORKSPACE
        # ----------------------------------------------------

        with action_col1:

            with st.container(border=True):

                st.markdown("**＋ Add Workspace**")

                with st.form(
                    "dashboard_add_workspace_form"
                ):

                    workspace_name = st.text_input(
                        "Workspace name",
                        placeholder="e.g. PMA Documents",
                    )

                    workspace_description = st.text_input(
                        "Description",
                        placeholder="Optional",
                    )

                    submitted = st.form_submit_button(
                        "Create Workspace",
                        use_container_width=True,
                    )

                    if submitted:

                        try:

                            create_workspace(
                                supabase,
                                workspace_name,
                                workspace_description,
                            )

                            st.success(
                                "Workspace created."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(str(exc))

        # ----------------------------------------------------
        # ADD REGISTER
        # ----------------------------------------------------

        with action_col2:

            with st.container(border=True):

                st.markdown("**＋ Add Register**")

                if not workspaces:

                    st.caption(
                        "Create a workspace first."
                    )

                else:

                    workspace_options = {
                        workspace["name"]: workspace["id"]
                        for workspace in workspaces
                    }

                    with st.form(
                        "dashboard_add_register_form"
                    ):

                        selected_workspace = st.selectbox(
                            "Workspace",
                            list(
                                workspace_options.keys()
                            ),
                        )

                        register_name = st.text_input(
                            "Register name",
                            placeholder="e.g. Credential Register",
                        )

                        register_description = st.text_input(
                            "Description",
                            placeholder="Optional",
                        )

                        submitted = st.form_submit_button(
                            "Create Register",
                            use_container_width=True,
                        )

                        if submitted:

                            try:

                                schema = create_register(
                                    supabase,
                                    workspace_options[
                                        selected_workspace
                                    ],
                                    register_name,
                                    register_description,
                                )

                                st.session_state[
                                    "active_schema_id"
                                ] = schema["id"]

                                st.session_state[
                                    "active_schema_name"
                                ] = schema["name"]

                                st.session_state[
                                    "register_setup_mode"
                                ] = True

                                st.success(
                                    "Register created."
                                )

                                st.rerun()

                            except Exception as exc:

                                st.error(str(exc))
