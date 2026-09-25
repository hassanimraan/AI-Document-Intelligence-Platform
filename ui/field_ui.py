import streamlit as st


FIELD_TYPES = [
    "text",
    "long_text",
    "number",
    "amount",
    "date",
    "boolean",
    "dropdown",
    "email",
    "phone",
    "document_number",
]


def _get_active_schema_id():
    """Return the currently selected register/schema ID."""

    schema_id = st.session_state.get(
        "active_schema_id"
    )

    if not schema_id:
        raise ValueError(
            "Please open a register first."
        )

    return schema_id


def load_fields(supabase):
    """Load fields belonging to the active register."""

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


def create_field(
    supabase,
    field_name,
    field_type,
    is_required,
    ai_extract,
    description,
    options,
):
    """Create a field in the active register."""

    schema_id = _get_active_schema_id()

    field_name = field_name.strip()
    description = description.strip()

    if not field_name:
        raise ValueError(
            "Field name is required."
        )

    if field_type not in FIELD_TYPES:
        raise ValueError(
            "Invalid field type."
        )

    existing_fields = load_fields(
        supabase
    )

    display_order = len(
        existing_fields
    )

    cleaned_options = None

    if field_type == "dropdown":

        cleaned_options = [
            option.strip()
            for option in options
            if option.strip()
        ]

        if not cleaned_options:
            raise ValueError(
                "Dropdown fields require at least one option."
            )

    response = (
        supabase
        .table("schema_fields")
        .insert(
            {
                "schema_id": schema_id,
                "field_name": field_name,
                "field_type": field_type,
                "is_required": is_required,
                "ai_extract": ai_extract,
                "display_order": display_order,
                "options": cleaned_options,
                "description": description or None,
            }
        )
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Field could not be created."
        )

    return response.data[0]


def update_field(
    supabase,
    field_id,
    field_name,
    field_type,
    is_required,
    ai_extract,
    description,
    options,
):
    """Update an existing field."""

    field_name = field_name.strip()
    description = description.strip()

    if not field_name:
        raise ValueError(
            "Field name is required."
        )

    if field_type not in FIELD_TYPES:
        raise ValueError(
            "Invalid field type."
        )

    cleaned_options = None

    if field_type == "dropdown":

        cleaned_options = [
            option.strip()
            for option in options
            if option.strip()
        ]

        if not cleaned_options:
            raise ValueError(
                "Dropdown fields require at least one option."
            )

    response = (
        supabase
        .table("schema_fields")
        .update(
            {
                "field_name": field_name,
                "field_type": field_type,
                "is_required": is_required,
                "ai_extract": ai_extract,
                "options": cleaned_options,
                "description": description or None,
            }
        )
        .eq("id", field_id)
        .execute()
    )

    if not response.data:
        raise ValueError(
            "Field could not be updated."
        )

    return response.data[0]


def delete_field(
    supabase,
    field_id,
):
    """Delete an existing field."""

    response = (
        supabase
        .table("schema_fields")
        .delete()
        .eq("id", field_id)
        .execute()
    )

    return response


def move_field(
    supabase,
    field_a,
    field_b,
):
    """Swap the display order of two fields."""

    order_a = field_a.get(
        "display_order",
        0,
    )

    order_b = field_b.get(
        "display_order",
        0,
    )

    (
        supabase
        .table("schema_fields")
        .update(
            {
                "display_order": order_b
            }
        )
        .eq(
            "id",
            field_a["id"],
        )
        .execute()
    )

    (
        supabase
        .table("schema_fields")
        .update(
            {
                "display_order": order_a
            }
        )
        .eq(
            "id",
            field_b["id"],
        )
        .execute()
    )


def render_field_ui(supabase):
    """Render dynamic field management."""

    active_schema_id = st.session_state.get(
        "active_schema_id"
    )

    active_schema_name = st.session_state.get(
        "active_schema_name"
    )

    if not active_schema_id:

        st.info(
            "Please open a register before managing fields."
        )

        return

    st.header(
        "🧩 Fields"
    )

    st.caption(
        f"Register: {active_schema_name}"
    )

    # ========================================================
    # CREATE FIELD
    # ========================================================

    with st.expander(
        "➕ Add New Field",
        expanded=True,
    ):

        # Field Type is intentionally OUTSIDE the form.
        # This allows Streamlit to immediately show
        # Dropdown Options when "dropdown" is selected.

        field_type = st.selectbox(
            "Field Type",
            FIELD_TYPES,
            key="new_field_type",
        )

        options_text = ""

        if field_type == "dropdown":

            options_text = st.text_area(
                "Dropdown Options",
                placeholder=(
                    "Enter one option per line.\n"
                    "Example:\n"
                    "LMBS\n"
                    "PMBS\n"
                    "MMBS\n"
                    "OLMRTS"
                ),
                key="new_dropdown_options",
            )

        with st.form(
            "create_field_form",
            clear_on_submit=True,
        ):

            field_name = st.text_input(
                "Field Name",
                placeholder="e.g. Client",
            )

            is_required = st.checkbox(
                "Required field",
                value=False,
            )

            ai_extract = st.checkbox(
                "Extract using AI",
                value=True,
            )

            description = st.text_area(
                "Field Description",
                placeholder=(
                    "Explain what information this field should contain."
                ),
            )

            submitted = st.form_submit_button(
                "Add Field",
                type="primary",
            )

            if submitted:

                try:

                    options = (
                        options_text.splitlines()
                        if field_type == "dropdown"
                        else []
                    )

                    create_field(
                        supabase,
                        field_name,
                        field_type,
                        is_required,
                        ai_extract,
                        description,
                        options,
                    )

                    st.success(
                        "Field added successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    st.error(
                        f"Field could not be added: {exc}"
                    )

    # ========================================================
    # EXISTING FIELDS
    # ========================================================

    st.subheader(
        "Fields in This Register"
    )

    try:

        fields = load_fields(
            supabase
        )

    except Exception as exc:

        st.error(
            f"Fields could not be loaded: {exc}"
        )

        return

    if not fields:

        st.info(
            "No fields have been added to this register yet."
        )

        return

    # ========================================================
    # FIELD LIST
    # ========================================================

    for index, field in enumerate(
        fields,
        start=1,
    ):

        field_id = field.get(
            "id"
        )

        field_name = field.get(
            "field_name",
            "Unnamed Field",
        )

        field_type = field.get(
            "field_type",
            "text",
        )

        is_required = field.get(
            "is_required",
            False,
        )

        ai_extract = field.get(
            "ai_extract",
            True,
        )

        description = field.get(
            "description"
        )

        options = field.get(
            "options"
        ) or []

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {index}. {field_name}"
            )

            col1, col2, col3, col4 = st.columns(
                [2, 2, 1, 1]
            )

            with col1:

                st.write(
                    f"**Type:** {field_type}"
                )

            with col2:

                st.write(
                    f"**Required:** "
                    f"{'Yes' if is_required else 'No'}"
                )

            with col3:

                st.write(
                    f"**AI:** "
                    f"{'Yes' if ai_extract else 'No'}"
                )

            with col4:

                st.write(
                    f"**Order:** {index}"
                )

            if description:

                st.caption(
                    f"Description: {description}"
                )

            if field_type == "dropdown" and options:

                st.caption(
                    "Options: "
                    + ", ".join(options)
                )

            # ==================================================
            # FIELD ACTIONS
            # ==================================================

            action_col1, action_col2, action_col3, action_col4 = st.columns(
                [1, 1, 1, 3]
            )

            # --------------------------------------------------
            # MOVE UP
            # --------------------------------------------------

            with action_col1:

                if st.button(
                    "⬆️",
                    key=f"move_up_{field_id}",
                    disabled=(index == 1),
                    help="Move field up",
                ):

                    move_field(
                        supabase,
                        field,
                        fields[index - 2],
                    )

                    st.rerun()

            # --------------------------------------------------
            # MOVE DOWN
            # --------------------------------------------------

            with action_col2:

                if st.button(
                    "⬇️",
                    key=f"move_down_{field_id}",
                    disabled=(index == len(fields)),
                    help="Move field down",
                ):

                    move_field(
                        supabase,
                        field,
                        fields[index],
                    )

                    st.rerun()

            # --------------------------------------------------
            # EDIT
            # --------------------------------------------------

            with action_col3:

                if st.button(
                    "✏️ Edit",
                    key=f"edit_button_{field_id}",
                ):

                    st.session_state[
                        f"editing_field_{field_id}"
                    ] = True

                    st.rerun()

            # --------------------------------------------------
            # DELETE
            # --------------------------------------------------

            with action_col4:

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_button_{field_id}",
                ):

                    st.session_state[
                        f"confirm_delete_{field_id}"
                    ] = True

                    st.rerun()

            # ==================================================
            # EDIT FORM
            # ==================================================

            if st.session_state.get(
                f"editing_field_{field_id}",
                False,
            ):

                st.divider()

                st.markdown(
                    "#### ✏️ Edit Field"
                )

                edit_type = st.selectbox(
                    "Field Type",
                    FIELD_TYPES,
                    index=(
                        FIELD_TYPES.index(field_type)
                        if field_type in FIELD_TYPES
                        else 0
                    ),
                    key=f"edit_type_{field_id}",
                )

                edit_options_text = ""

                if edit_type == "dropdown":

                    edit_options_text = st.text_area(
                        "Dropdown Options",
                        value="\n".join(options),
                        placeholder=(
                            "Enter one option per line."
                        ),
                        key=f"edit_options_{field_id}",
                    )

                with st.form(
                    f"edit_form_{field_id}",
                ):

                    edit_name = st.text_input(
                        "Field Name",
                        value=field_name,
                        key=f"edit_name_{field_id}",
                    )

                    edit_required = st.checkbox(
                        "Required field",
                        value=is_required,
                        key=f"edit_required_{field_id}",
                    )

                    edit_ai_extract = st.checkbox(
                        "Extract using AI",
                        value=ai_extract,
                        key=f"edit_ai_{field_id}",
                    )

                    edit_description = st.text_area(
                        "Field Description",
                        value=description or "",
                        key=f"edit_description_{field_id}",
                    )

                    save_edit = st.form_submit_button(
                        "Save Changes",
                        type="primary",
                    )

                    cancel_edit = st.form_submit_button(
                        "Cancel"
                    )

                    if save_edit:

                        try:

                            edit_options = (
                                edit_options_text.splitlines()
                                if edit_type == "dropdown"
                                else []
                            )

                            update_field(
                                supabase,
                                field_id,
                                edit_name,
                                edit_type,
                                edit_required,
                                edit_ai_extract,
                                edit_description,
                                edit_options,
                            )

                            st.session_state[
                                f"editing_field_{field_id}"
                            ] = False

                            st.success(
                                "Field updated successfully."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                f"Field could not be updated: {exc}"
                            )

                    if cancel_edit:

                        st.session_state[
                            f"editing_field_{field_id}"
                        ] = False

                        st.rerun()

            # ==================================================
            # DELETE CONFIRMATION
            # ==================================================

            if st.session_state.get(
                f"confirm_delete_{field_id}",
                False,
            ):

                st.warning(
                    f"Delete field '{field_name}'? "
                    "This removes the field from this register."
                )

                confirm_col1, confirm_col2 = st.columns(
                    2
                )

                with confirm_col1:

                    if st.button(
                        "Yes, Delete",
                        key=f"confirm_yes_{field_id}",
                        type="primary",
                    ):

                        try:

                            delete_field(
                                supabase,
                                field_id,
                            )

                            st.session_state[
                                f"confirm_delete_{field_id}"
                            ] = False

                            st.success(
                                "Field deleted successfully."
                            )

                            st.rerun()

                        except Exception as exc:

                            st.error(
                                f"Field could not be deleted: {exc}"
                            )

                with confirm_col2:

                    if st.button(
                        "Cancel",
                        key=f"confirm_no_{field_id}",
                    ):

                        st.session_state[
                            f"confirm_delete_{field_id}"
                        ] = False

                        st.rerun()
