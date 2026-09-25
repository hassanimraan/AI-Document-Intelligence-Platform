import streamlit as st

def _get_active_workspace_id():
"""Return the currently selected workspace ID."""

```
workspace_id = st.session_state.get(
    "active_workspace_id"
)

if not workspace_id:
    raise ValueError(
        "Please select a workspace first."
    )

return workspace_id
```

def load_schemas(supabase):
"""Load active registers belonging to the active workspace."""

```
workspace_id = _get_active_workspace_id()

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
```

def create_schema(
supabase,
name,
description,
):
"""Create a new document register/schema."""

```
name = name.strip()
description = description.strip()

if not name:
    raise ValueError(
        "Register name is required."
    )

workspace_id = _get_active_workspace_id()

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
    raise ValueError(
        "Register could not be created."
    )

return response.data[0]
```

def get_record_count(
supabase,
schema_id,
):
"""Return the number of records associated with a register."""

```
response = (
    supabase
    .table("document_records")
    .select("id")
    .eq("schema_id", schema_id)
    .execute()
)

return len(response.data or [])
```

def deactivate_schema(
supabase,
schema_id,
):
"""Deactivate a register without deleting its records."""

```
workspace_id = _get_active_workspace_id()

response = (
    supabase
    .table("document_schemas")
    .update(
        {
            "is_active": False,
        }
    )
    .eq("id", schema_id)
    .eq("workspace_id", workspace_id)
    .eq("is_active", True)
    .execute()
)

if not response.data:
    raise ValueError(
        "Register could not be deleted."
    )

# Clear active register state if this was the active register.
if (
    st.session_state.get("active_schema_id")
    == schema_id
):

    st.session_state.pop(
        "active_schema_id",
        None,
    )

    st.session_state.pop(
        "active_schema_name",
        None,
    )

    st.session_state.pop(
        "structure_headers",
        None,
    )
```

def render_schema_ui(supabase):
"""Render register/schema management."""

```
active_workspace_id = st.session_state.get(
    "active_workspace_id"
)

active_workspace_name = st.session_state.get(
    "active_workspace_name"
)

if not active_workspace_id:

    st.info(
        "Please open a workspace before managing registers."
    )

    return

st.header(
    "📋 Registers"
)

st.caption(
    f"Workspace: {active_workspace_name}"
)

# ========================================================
# CREATE REGISTER
# ========================================================

with st.expander(
    "➕ Create New Register",
    expanded=True,
):

    with st.form(
        "create_schema_form",
        clear_on_submit=True,
    ):

        schema_name = st.text_input(
            "Register Name",
            placeholder="e.g. Credential Register",
        )

        schema_description = st.text_area(
            "Description",
            placeholder=(
                "Describe the type of records "
                "this register will contain."
            ),
        )

        submitted = st.form_submit_button(
            "Create Register",
            type="primary",
        )

        if submitted:

            try:

                create_schema(
                    supabase,
                    schema_name,
                    schema_description,
                )

                st.success(
                    "Register created successfully."
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Register could not be created: {exc}"
                )

# ========================================================
# EXISTING REGISTERS
# ========================================================

st.subheader(
    "Registers in This Workspace"
)

try:

    schemas = load_schemas(
        supabase
    )

except Exception as exc:

    st.error(
        f"Registers could not be loaded: {exc}"
    )

    return

if not schemas:

    st.info(
        "No registers have been created in this workspace yet."
    )

    return

# ========================================================
# REGISTER LIST
# ========================================================

for schema in schemas:

    schema_id = schema.get(
        "id"
    )

    schema_name = schema.get(
        "name",
        "Unnamed Register",
    )

    schema_description = schema.get(
        "description"
    )

    with st.container(
        border=True
    ):

        col1, col2, col3 = st.columns(
            [4, 1, 1]
        )

        with col1:

            st.markdown(
                f"### {schema_name}"
            )

            if schema_description:

                st.caption(
                    schema_description
                )

            st.caption(
                f"Register ID: {schema_id}"
            )

        # ------------------------------------------------
        # OPEN
        # ------------------------------------------------

        with col2:

            if st.button(
                "Open",
                key=f"open_schema_{schema_id}",
                use_container_width=True,
            ):

                st.session_state[
                    "active_schema_id"
                ] = schema_id

                st.session_state[
                    "active_schema_name"
                ] = schema_name

                # Force the structure editor to reload
                # the newly selected register.
                st.session_state.pop(
                    "structure_headers",
                    None,
                )

                st.rerun()

        # ------------------------------------------------
        # DELETE
        # ------------------------------------------------

        with col3:

            if st.button(
                "🗑️ Delete",
                key=f"delete_schema_{schema_id}",
                use_container_width=True,
            ):

                st.session_state[
                    "pending_delete_schema_id"
                ] = schema_id

                st.session_state[
                    "pending_delete_schema_name"
                ] = schema_name

                st.rerun()

# ========================================================
# DELETE CONFIRMATION
# ========================================================

pending_delete_schema_id = st.session_state.get(
    "pending_delete_schema_id"
)

pending_delete_schema_name = st.session_state.get(
    "pending_delete_schema_name"
)

if pending_delete_schema_id:

    st.divider()

    st.warning(
        f"⚠️ You are about to remove "
        f"**{pending_delete_schema_name}** "
        "from the active register list."
    )

    try:

        record_count = get_record_count(
            supabase,
            pending_delete_schema_id,
        )

    except Exception:

        record_count = None

    if record_count is not None:

        if record_count > 0:

            st.info(
                f"This register currently has "
                f"**{record_count} record(s)**. "
                "Those records will be preserved."
            )

        else:

            st.info(
                "This register currently has no saved records."
            )

    st.markdown(
        "**The register will be archived, not permanently erased.**"
    )

    confirm_col1, confirm_col2 = st.columns(
        2
    )

    with confirm_col1:

        if st.button(
            "❌ Cancel",
            key="cancel_delete_schema",
            use_container_width=True,
        ):

            st.session_state.pop(
                "pending_delete_schema_id",
                None,
            )

            st.session_state.pop(
                "pending_delete_schema_name",
                None,
            )

            st.rerun()

    with confirm_col2:

        if st.button(
            "Archive Register",
            key="confirm_delete_schema",
            type="primary",
            use_container_width=True,
        ):

            try:

                deactivate_schema(
                    supabase,
                    pending_delete_schema_id,
                )

                st.session_state.pop(
                    "pending_delete_schema_id",
                    None,
                )

                st.session_state.pop(
                    "pending_delete_schema_name",
                    None,
                )

                st.success(
                    "Register archived successfully."
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Register could not be archived: {exc}"
                )

# ========================================================
# ACTIVE REGISTER
# ========================================================

active_schema_id = st.session_state.get(
    "active_schema_id"
)

active_schema_name = st.session_state.get(
    "active_schema_name"
)

if active_schema_id:

    st.divider()

    st.subheader(
        "Active Register"
    )

    st.success(
        f"Currently selected: {active_schema_name}"
    )

    st.caption(
        f"Register ID: {active_schema_id}"
    )
```
