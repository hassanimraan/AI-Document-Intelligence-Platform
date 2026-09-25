import streamlit as st


def _get_active_workspace_id():
    """Return the currently selected workspace ID."""
    return st.session_state.get("active_workspace_id")


def load_schemas(supabase):
    """Load active registers for the selected workspace."""
    workspace_id = _get_active_workspace_id()

    if not workspace_id:
        return []

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


def create_schema(supabase, name, description):
    """Create a new register."""
    workspace_id = _get_active_workspace_id()

    if not workspace_id:
        raise ValueError("Please select a workspace first.")

    name = name.strip()

    if not name:
        raise ValueError("Register name is required.")

    response = (
        supabase
        .table("document_schemas")
        .insert(
            {
                "workspace_id": workspace_id,
                "name": name,
                "description": description.strip(),
                "version": 1,
                "is_active": True,
            }
        )
        .execute()
    )

    if not response.data:
        raise ValueError("Register could not be created.")

    return response.data[0]


def deactivate_schema(supabase, schema_id):
    """Archive a register without deleting its historical records."""
    workspace_id = _get_active_workspace_id()

    if not workspace_id:
        raise ValueError("Please select a workspace first.")

    response = (
        supabase
        .table("document_schemas")
        .update({"is_active": False})
        .eq("id", schema_id)
        .eq("workspace_id", workspace_id)
        .eq("is_active", True)
        .execute()
    )

    if not response.data:
        raise ValueError("Register could not be archived.")

    if st.session_state.get("active_schema_id") == schema_id:
        st.session_state.pop("active_schema_id", None)
        st.session_state.pop("active_schema_name", None)
        st.session_state.pop("structure_headers", None)


def render_schema_ui(supabase):
    """Render register management UI."""
    st.header("📋 Registers")

    workspace_id = _get_active_workspace_id()

    if not workspace_id:
        st.info("Please create or open a workspace first.")
        return

    schemas = load_schemas(supabase)

    st.subheader("Create Register")

    with st.form("create_register_form"):
        name = st.text_input(
            "Register Name",
            placeholder="e.g. Credential Register",
        )

        description = st.text_area(
            "Description",
            placeholder="Optional description",
        )

        submitted = st.form_submit_button("Create Register")

        if submitted:
            try:
                schema = create_schema(
                    supabase,
                    name,
                    description,
                )

                st.success(
                    f"Register '{schema['name']}' created successfully."
                )

                st.rerun()

            except Exception as exc:
                st.error(str(exc))

    st.divider()

    st.subheader("Active Registers")

    if not schemas:
        st.info("No active registers found.")
        return

    for schema in schemas:
        schema_id = schema["id"]
        schema_name = schema["name"]

        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            st.write(f"**{schema_name}**")

        with col2:
            if st.button(
                "Open",
                key=f"open_schema_{schema_id}",
            ):
                st.session_state["active_schema_id"] = schema_id
                st.session_state["active_schema_name"] = schema_name

                st.success(
                    f"Selected register: {schema_name}"
                )

        with col3:
            if st.button(
                "Archive",
                key=f"archive_schema_{schema_id}",
            ):
                st.session_state[
                    f"confirm_archive_{schema_id}"
                ] = True

        if st.session_state.get(
            f"confirm_archive_{schema_id}",
            False,
        ):
            st.warning(
                f"Archive '{schema_name}'? "
                "Existing records will be preserved."
            )

            confirm_col1, confirm_col2 = st.columns(2)

            with confirm_col1:
                if st.button(
                    "Yes, Archive",
                    key=f"confirm_yes_{schema_id}",
                ):
                    try:
                        deactivate_schema(
                            supabase,
                            schema_id,
                        )

                        st.session_state.pop(
                            f"confirm_archive_{schema_id}",
                            None,
                        )

                        st.success(
                            f"Register '{schema_name}' archived."
                        )

                        st.rerun()

                    except Exception as exc:
                        st.error(str(exc))

            with confirm_col2:
                if st.button(
                    "Cancel",
                    key=f"confirm_no_{schema_id}",
                ):
                    st.session_state.pop(
                        f"confirm_archive_{schema_id}",
                        None,
                    )

                    st.rerun()

    active_schema_name = st.session_state.get(
        "active_schema_name"
    )

    if active_schema_name:
        st.info(
            f"Currently selected: {active_schema_name}"
        )
