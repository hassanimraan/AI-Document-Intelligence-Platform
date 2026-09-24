import pandas as pd
import streamlit as st

from config.schema import MASTER_SCHEMA
from utils.database import DatabaseManager


# ============================================================
# DATABASE → MASTER EXCEL SCHEMA
# ============================================================

def _records_to_dataframe(records):
    """
    Convert Supabase database records into the locked
    master Excel schema.
    """

    rows = []

    for index, record in enumerate(records, start=1):

        rows.append(
            {
                "Sr. No.": index,

                "Client (PMA)": record.get(
                    "client_pma"
                ),

                "System (LMBS, PMBS, MMBS, OLMRTS)": (
                    record.get("system")
                ),

                "Contract": record.get(
                    "contract"
                ),

                "Document Type": record.get(
                    "document_type"
                ),

                "Document Number": record.get(
                    "document_number"
                ),

                "Date of Issuance": record.get(
                    "date_of_issuance"
                ),

                "Amount": record.get(
                    "amount"
                ),

                "Initiated By": record.get(
                    "initiated_by"
                ),

                "Reviewed By": record.get(
                    "reviewed_by"
                ),

                "Approved by": record.get(
                    "approved_by"
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=MASTER_SCHEMA,
    )


# ============================================================
# LOAD RECORDS
# ============================================================

def load_user_records():
    """
    Load the authenticated user's records from Supabase.
    """

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


# ============================================================
# RECORDS UI
# ============================================================

def render_records_ui():
    """
    Render the user's saved credential records.
    """

    st.divider()

    st.header("📋 My Credential Records")

    st.write(
        "These are the credential records permanently "
        "saved in your Supabase database."
    )

    # --------------------------------------------------------
    # LOAD RECORDS BUTTON
    # --------------------------------------------------------

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

                st.session_state.my_credentials = (
                    records
                )

                st.success(
                    f"{len(records)} credential record(s) "
                    "loaded successfully."
                )

        except Exception as exc:

            st.error(
                f"Unable to load records: {exc}"
            )

    # --------------------------------------------------------
    # DISPLAY LOADED RECORDS
    # --------------------------------------------------------

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
