import streamlit as st


def _get_user_id():
    """
    Get the authenticated Supabase user ID.

    The authentication system already establishes the
    authenticated session. We use the Supabase user ID
    as the ownership key for workspace operations.
    """

    user_id = st.session_state.get("user_id")

    if not user_id:
        raise ValueError(
            "Authenticated user ID is not available."
        )

    return user_id


def _get_supabase_client():
    """
    Reuse the authenticated Supabase client already
    created by the application.
    """

    supabase = st.session_state.get(
        "supabase_client"
    )

    if supabase is None:
        raise ValueError(
            "Supabase client is not available."
        )

    return supabase


def load_workspaces():
    """
    Load workspaces belonging to the authenticated user.

    RLS remains the final database-level security boundary.
    """

    supabase = _get_supabase_client()
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


def create_workspace(
    name,
    description,
):
    """
    Create a new workspace for the authenticated user.
    """

    name = name.strip()
    description = description.strip()

    if not name:
        raise ValueError(
            "Workspace name is required."
        )

    supabase = _get_supabase_client()
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
        raise ValueError(
            "Workspace could not be created."
        )

    return response.data[0]


def render_workspace_ui():
    """
    Render the V2 workspace management interface.
    """

    st.header(
        "🏢 Workspaces"
    )

    st.caption(
        "Create and manage independent document workspaces."
    )

    # --------------------------------------------------------
    # CREATE WORKSPACE
    # --------------------------------------------------------

    with st.expander(
        "➕ Create New Workspace",
        expanded=True,
    ):

        with st.form(
            "create_workspace_form",
            clear_on_submit=True,
        ):

            workspace_name = st.text_input(
                "Workspace Name",
                placeholder="e.g. PMA Documents",
            )

            workspace_description = st.text_area(
                "Description",
                placeholder=(
                    "Describe what documents or records "
                    "this workspace will contain."
                ),
            )

            submitted = st.form_submit_button(
                "Create Workspace",
                type="primary",
            )

            if submitted:

                try:

                    create_workspace(
                        workspace_name,
                        workspace_description,
                    )

                    st.success(
                        "Workspace created successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Workspace could not be created: {exc}"
                    )

    # --------------------------------------------------------
    # EXISTING WORKSPACES
    # --------------------------------------------------------

    st.subheader(
        "Your Workspaces"
    )

    try:

        workspaces = load_workspaces()

    except Exception as exc:

        st.error(
            f"Workspaces could not be loaded: {exc}"
        )

        return

    if not workspaces:

        st.info(
            "No workspaces have been created yet."
        )

        return

    for workspace in workspaces:

        workspace_id = workspace.get(
            "id"
        )

        workspace_name = workspace.get(
            "name",
            "Unnamed Workspace",
        )

        workspace_description = workspace.get(
            "description"
        )

        with st.container(
            border=True
        ):

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.markdown(
                    f"### {workspace_name}"
                )

                if workspace_description:

                    st.caption(
                        workspace_description
                    )

                st.caption(
                    f"Workspace ID: {workspace_id}"
                )

            with col2:

                if st.button(
                    "Open",
                    key=f"open_workspace_{workspace_id}",
                    use_container_width=True,
                ):

                    st.session_state[
                        "active_workspace_id"
                    ] = workspace_id

                    st.session_state[
                        "active_workspace_name"
                    ] = workspace_name

                    st.rerun()

    # --------------------------------------------------------
    # ACTIVE WORKSPACE
    # --------------------------------------------------------

    active_workspace_id = st.session_state.get(
        "active_workspace_id"
    )

    active_workspace_name = st.session_state.get(
        "active_workspace_name"
    )

    if active_workspace_id:

        st.divider()

        st.subheader(
            "Active Workspace"
        )

        st.success(
            f"Currently selected: {active_workspace_name}"
        )

        st.caption(
            f"Workspace ID: {active_workspace_id}"
        )
