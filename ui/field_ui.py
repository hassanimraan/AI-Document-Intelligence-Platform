import streamlit as st


def _get_active_schema_id():
    """Return the currently selected register ID."""

    schema_id = st.session_state.get("active_schema_id")

    if not schema_id:
        raise ValueError(
            "Please open a register first."
        )

    return schema_id


def load_fields(supabase):
    """Load headers for the active register."""

    schema_id = _get_active_schema_id()

    response = (
        supabase
        .table("schema_fields")
        .select("*")
        .eq("schema_id", schema_id)
        .order("display_order")
        .order("created_at")
        .execute()
    )

    return response.data or []


def initialize_structure(supabase):
    """Load the saved structure into temporary editor state."""

    schema_id = _get_active_schema_id()

    current_schema_id = st.session_state.get(
        "structure_editor_schema_id"
    )

    if current_schema_id == schema_id:
        return

    fields = load_fields(supabase)

    st.session_state.structure_editor_schema_id = schema_id

    st.session_state.structure_headers = [
        {
            "id": field.get("id"),
            "name": field.get("field_name", ""),
        }
        for field in fields
    ]


def add_header():
    """Add one blank header."""

    st.session_state.structure_headers.append(
        {
            "id": None,
            "name": "",
        }
    )


def delete_header(index):
    """Delete a header from the editor."""

    headers = st.session_state.structure_headers

    if 0 <= index < len(headers):
        headers.pop(index)


def save_structure(supabase):
    """Save the current register structure."""

    schema_id = _get_active_schema_id()

    headers = st.session_state.get(
        "structure_headers",
        [],
    )

    cleaned_headers = []

    for header in headers:

        name = header.get(
            "name",
            "",
        ).strip()

        if name:
            cleaned_headers.append(
                {
                    "id": header.get("id"),
                    "name": name,
                }
            )

    if not cleaned_headers:

        raise ValueError(
            "Please add at least one header."
        )

    # --------------------------------------------------------
    # Prevent duplicate header names
    # --------------------------------------------------------

    normalized_names = [
        header["name"].strip().lower()
        for header in cleaned_headers
    ]

    if len(normalized_names) != len(
        set(normalized_names)
    ):

        raise ValueError(
            "Header names must be unique."
        )

    # --------------------------------------------------------
    # Existing database headers
    # --------------------------------------------------------

    existing_fields = load_fields(
        supabase
    )

    existing_ids = {
        field["id"]
        for field in existing_fields
        if field.get("id")
    }

    current_ids = {
        header["id"]
        for header in cleaned_headers
        if header.get("id")
    }

    # --------------------------------------------------------
    # Delete removed headers
    # --------------------------------------------------------

    for field_id in (
        existing_ids - current_ids
    ):

        (
            supabase
            .table("schema_fields")
            .delete()
            .eq("id", field_id)
            .execute()
        )

    # --------------------------------------------------------
    # Update existing headers / create new headers
    # --------------------------------------------------------

    for display_order, header in enumerate(
        cleaned_headers
    ):

        field_id = header.get("id")
        field_name = header["name"]

        if field_id:

            (
                supabase
                .table("schema_fields")
                .update(
                    {
                        "field_name": field_name,
                        "display_order": display_order,
                    }
                )
                .eq(
                    "id",
                    field_id,
                )
                .execute()
            )

        else:

            response = (
                supabase
                .table("schema_fields")
                .insert(
                    {
                        "schema_id": schema_id,
                        "field_name": field_name,
                        "field_type": "text",
                        "is_required": False,
                        "ai_extract": True,
                        "display_order": display_order,
                        "options": None,
                        "description": None,
                    }
                )
                .execute()
            )

            if not response.data:

                raise ValueError(
                    f"Header '{field_name}' could not be created."
                )

            header["id"] = response.data[0]["id"]

    # --------------------------------------------------------
    # Update temporary state
    # --------------------------------------------------------

    st.session_state.structure_headers = [
        {
            "id": header.get("id"),
            "name": header["name"],
        }
        for header in cleaned_headers
    ]


def render_field_ui(supabase):
    """Render the simplified register structure editor."""

    active_schema_id = st.session_state.get(
        "active_schema_id"
    )

    active_schema_name = st.session_state.get(
        "active_schema_name"
    )

    if not active_schema_id:

        st.info(
            "Please open a register before defining its structure."
        )

        return

    initialize_structure(
        supabase
    )

    st.header(
        "📊 Register Structure"
    )

    st.caption(
        f"Register: {active_schema_name}"
    )

    st.write(
        "Define the column headers for this register."
    )

    # ========================================================
    # HEADER EDITOR
    # ========================================================

    headers = st.session_state.structure_headers

    if headers:

        for index, header in enumerate(
            headers
        ):

            col1, col2, col3 = st.columns(
                [0.5, 6, 0.8]
            )

            with col1:

                st.markdown(
                    f"**{index + 1}**"
                )

            with col2:

                new_name = st.text_input(
                    "Header name",
                    value=header.get(
                        "name",
                        "",
                    ),
                    key=(
                        f"header_name_"
                        f"{active_schema_id}_"
                        f"{index}"
                    ),
                    label_visibility="collapsed",
                    placeholder="Enter header name",
                )

                st.session_state.structure_headers[
                    index
                ]["name"] = new_name

            with col3:

                if st.button(
                    "🗑️",
                    key=(
                        f"delete_header_"
                        f"{active_schema_id}_"
                        f"{index}"
                    ),
                    help="Delete this header",
                ):

                    delete_header(
                        index
                    )

                    st.rerun()

    else:

        st.info(
            "No headers have been added yet."
        )

    # ========================================================
    # ADD HEADER
    # ========================================================

    st.divider()

    if st.button(
        "➕ Add Header",
        use_container_width=True,
        key=f"add_header_{active_schema_id}",
    ):

        add_header()

        st.rerun()

    # ========================================================
    # SAVE STRUCTURE
    # ========================================================

    if st.button(
        "💾 Save Register Structure",
        type="primary",
        use_container_width=True,
        key=f"save_structure_{active_schema_id}",
    ):

        try:

            save_structure(
                supabase
            )

            st.success(
                "Register structure saved successfully."
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Register structure could not be saved: {exc}"
            )
