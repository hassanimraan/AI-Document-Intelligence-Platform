```python
import io

import pandas as pd
import streamlit as st

from config.schema import MASTER_SCHEMA
from utils.database import DatabaseManager


def _records_to_dataframe(records):
    rows = []

    for index, record in enumerate(records, start=1):
        rows.append(
            {
                "Sr. No.": index,
                "Client (PMA)": record.get("client_pma"),
                "System (LMBS, PMBS, MMBS, OLMRTS)": (
                    record.get("system")
                ),
                "Contract": record.get("contract"),
                "Document Type": record.get("document_type"),
                "Document Number": record.get("document_number"),
                "Date of Issuance": record.get("date_of_issuance"),
                "Amount": record.get("amount"),
                "Initiated By": record.get("initiated_by"),
                "Reviewed By": record.get("reviewed_by"),
                "Approved by": record.get("approved_by"),
            }
        )

    return pd.DataFrame(
        rows,
        columns=MASTER_SCHEMA,
    )


def _create_excel_file(dataframe):
    """Create a formatted Excel workbook in memory."""

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        dataframe.to_excel(
            writer,
            index=False,
            sheet_name="Credentials",
        )

        worksheet = writer.sheets["Credentials"]

        # Freeze the header row.
        worksheet.freeze_panes = "A2"

        # Enable AutoFilter.
        worksheet.auto_filter.ref = (
            worksheet.dimensions
        )

        # Format header cells.
        from openpyxl.styles import Font, PatternFill, Alignment

        header_fill = PatternFill(
            fill_type="solid",
            fgColor="1F4E78",
        )

        header_font = Font(
            bold=True,
            color="FFFFFF",
        )

        header_alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # Set column widths.
        column_widths = {
            "A": 10,
            "B": 25,
            "C": 28,
            "D": 22,
            "E": 24,
            "F": 22,
            "G": 18,
            "H": 18,
            "I": 25,
            "J": 25,
            "K": 25,
        }

        for column, width in column_widths.items():
            worksheet.column_dimensions[column].width = width

        # Format date column.
        for cell in worksheet["G"][1:]:
            cell.number_format = "yyyy-mm-dd"

        # Format amount column.
        for cell in worksheet["H"][1:]:
            cell.number_format = '#,##0.00'

        # Align Sr. No.
        for cell in worksheet["A"][1:]:
            cell.alignment = Alignment(
                horizontal="center"
            )

    output.seek(0)

    return output.getvalue()


def load_user_records():
    database = DatabaseManager()

    access_token = st.session_state.get(
        "access_token"
    )

    refresh_token = st.session_state.get(
        "refresh_token"
    )

    database.set_user_session(
        access_token,
        refresh_token,
    )

    return database.get_user_credentials()


def render_records_ui():
    st.divider()

    st.header("📋 My Credential Records")

    st.write(
        "These are the credential records permanently "
        "saved in your Supabase database."
    )

    if st.button(
        "🔄 Load My Records",
        key="load_my_records_button",
    ):
        try:
            with st.spinner(
                "Loading your records..."
            ):
                records = load_user_records()

            if not records:
                st.info(
                    "No saved credential records found."
                )

                st.session_state.my_credentials = []

            else:
                st.session_state.my_credentials = records

                st.success(
                    f"{len(records)} credential "
                    "record(s) loaded successfully."
                )

        except Exception as exc:
            st.error(
                f"Unable to load records: {exc}"
            )

    records = st.session_state.get(
        "my_credentials"
    )

    if not records:
        return

    dataframe = _records_to_dataframe(
        records
    )

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(
        "📥 Export Records"
    )

    st.write(
        "Download your currently loaded credential "
        "records as an Excel workbook."
    )

    try:
        excel_file = _create_excel_file(
            dataframe
        )

        st.download_button(
            label="📊 Download Excel",
            data=excel_file,
            file_name="credential_records.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            key="download_credentials_excel",
        )

    except Exception as exc:
        st.error(
            f"Unable to create Excel file: {exc}"
        )
```
