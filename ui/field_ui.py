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

        if not options:

            raise ValueError(
                "Dropdown fields require at least one option."
            )

        cleaned_options = [
            option.strip()
            for option in options
            if option.strip()
        ]

        if not cleaned_options:

            raise ValueError(
                "Dropdown fields require valid options."
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

        with st.form(
            "create_field_form",
            clear_on_submit=True,
        ):

            field_name = st.text_input(
                "Field Name",
                placeholder="e.g. Client",
            )

            field_type = st.selectbox(
                "Field Type",
                FIELD_TYPES,
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

    for index, field in enumerate(fields, start=1):

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
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {index}. {field_name}"
            )

            st.caption(
                f"Type: {field_type}"
            )

            col1, col2 = st.columns(
                2
            )

            with col1:

                st.write(
                    f"Required: {'Yes' if is_required else 'No'}"
                )

            with col2:

                st.write(
                    f"AI Extract: {'Yes' if ai_extract else 'No'}"
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
