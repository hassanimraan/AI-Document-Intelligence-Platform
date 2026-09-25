import streamlit as st
import pandas as pd


def _get_active_schema_id():
    """Return the currently selected register/schema ID."""

    schema_id = st.session_state.get("active_schema_id")

    if not schema_id:
        raise ValueError(
            "Please open a register first."
        )

    return schema_id


def load_fields(supabase):
    """Load headers belonging to the active register."""

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
    """Load the saved register structure into temporary UI state."""

    schema_id = _get_active_schema_id()

    state_schema_id = st.session_state.get(
        "structure_editor_schema_id"
    )

    if state_schema_id == schema_id:
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
    """Add a new blank header to the temporary structure."""

    st.session_state.structure_headers.append(
        {
            "id": None,
            "name": "",
        }
    )


def delete_header(index):
    """Delete a header from the temporary structure."""

    if 0 <= index < len(
        st.session_state.structure_headers
    ):
        st.session_state.structure_headers.pop(index)


def move_header_up(index):
    """Move a header one position upward."""

    if index <= 0:
        return

    headers = st.session_state.structure_headers

    headers[index - 1], headers[index] = (
        headers[index],
        headers[index - 1],
    )


def move_header_down(index):
    """Move a header one position downward."""

    headers = st.session_state.structure_headers

    if index >= len(headers) - 1:
        return

    headers[index], headers[index + 1] = (
        headers[index + 1],
        headers[index],
    )


def save_structure(supabase):
    """Save the current header structure to Supabase."""

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

        if not name:
            continue

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
    # Check duplicate headers
    # --------------------------------------------------------

    names_lower = [
        header["name"].lower()
        for header in cleaned_headers
    ]

    if len(names_lower) != len(
        set(names_lower)
    ):

        raise ValueError(
            "Header names must be unique."
        )

    # --------------------------------------------------------
    # Load existing database fields
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

    ids_to_delete = (
        existing_ids - current_ids
    )

    for field_id in ids_to_delete:

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
    # Replace temporary state with clean saved structure
    # --------------------------------------------------------

    st.session_state.structure_headers = [
        {
            "id": header.get("id"),
            "name": header["name"],
        }
        for header in cleaned_headers
    ]

    st.session_state.structure_saved = True


def render_field_ui(supabase):
    """Render the simplified Excel-like register structure editor."""

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

    st.info(
        "You can add as many headers as needed. "
        "The headers can be changed later."
    )

    # ========================================================
    # ADD HEADER
    # ========================================================

    if st.button(
        "➕ Add Header",
        type="primary",
        key="add_structure_header",
    ):

        add_header()

        st.session_state.structure_saved = False

        st.rerun()

    # ========================================================
    # EMPTY STATE
    # ========================================================

    headers = st.session_state.structure_headers

    if not headers:

        st.info(
            "No headers yet. Click 'Add Header' to create your first column."
        )

        return

    # ========================================================
    # EXCEL-LIKE PREVIEW
    # ========================================================

    st.subheader(
        "Column Headers"
    )

    preview_names = [
        header.get("name", "").strip()
        or f"Header {index}"
        for index, header in enumerate(
            headers,
            start=1,
        )
    ]

    preview_data = {
        name: [name]
        for name in preview_names
    }

    preview_df = pd.DataFrame(
        preview_data,
        index=["Header"],
    )

    st.dataframe(
        preview_df,
        use_container_width=True,
        hide_index=False,
    )

    # ========================================================
    # HEADER EDITOR
    # ========================================================

    st.subheader(
        "Edit Headers"
    )

    st.caption(
        "Change the names below or use the arrow buttons to change their order."
    )

    for index, header in enumerate(
        headers
    ):

        current_name = header.get(
            "name",
            "",
        )

        col1, col2, col3, col4, col5 = st.columns(
            [0.5, 5, 0.8, 0.8, 1]
        )

        with col1:

            st.markdown(
                f"**{index + 1}**"
            )

        with col2:

            new_name = st.text_input(
                "Header",
                value=current_name,
                key=f"header_name_{active_schema_id}_{index}",
                label_visibility="collapsed",
                placeholder="Enter column header",
            )

            st.session_state.structure_headers[
                index
            ]["name"] = new_name

        with col3:

            if st.button(
                "⬆️",
                key=f"header_up_{active_schema_id}_{index}",
                disabled=(index == 0),
                help="Move header up",
            ):

                move_header_up(
                    index
                )

                st.session_state.structure_saved = False

                st.rerun()

        with col4:

            if st.button(
                "⬇️",
                key=f"header_down_{active_schema_id}_{index}",
                disabled=(index == len(headers) - 1),
                help="Move header down",
            ):

                move_header_down(
                    index
                )

                st.session_state.structure_saved = False

                st.rerun()

        with col5:

            if st.button(
                "🗑️",
                key=f"header_delete_{active_schema_id}_{index}",
                help="Delete header",
            ):

                delete_header(
                    index
                )

                st.session_state.structure_saved = False

                st.rerun()

    # ========================================================
    # SAVE STRUCTURE
    # ========================================================

    st.divider()

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

    # ========================================================
    # SAVED STRUCTURE
    # ========================================================

    st.divider()

    st.subheader(
        "Current Saved Structure"
    )

    try:

        saved_fields = load_fields(
            supabase
        )

        if saved_fields:

            saved_names = [
                field.get(
                    "field_name",
                    "",
                )
                for field in saved_fields
            ]

            saved_df = pd.DataFrame(
                {
                    "Column": range(
                        1,
                        len(saved_names) + 1,
                    ),
                    "Header": saved_names,
                }
            )

            st.dataframe(
                saved_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "The register structure has not been saved yet."
            )

    except Exception as exc:

        st.error(
            f"Saved structure could not be loaded: {exc}"
        )
