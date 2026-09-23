import streamlit as st
from supabase import create_client


class DatabaseManager:
    """Handles authenticated access to Supabase PostgreSQL."""

    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets["SUPABASE_PUBLISHABLE_KEY"]

        self.supabase = create_client(
            self.url,
            self.key
        )

    def set_user_session(
        self,
        access_token,
        refresh_token
    ):
        """Attach the authenticated Supabase session."""

        if not access_token or not refresh_token:
            raise ValueError(
                "Valid authentication tokens are required."
            )

        self.supabase.auth.set_session(
            access_token,
            refresh_token
        )

    def get_current_user(self):
        """Return the currently authenticated user."""

        response = self.supabase.auth.get_user()

        return response.user

    def insert_credential(
        self,
        record,
        document_filename=None
    ):
        """
        Insert a verified credential record.

        user_id is obtained from the authenticated
        Supabase user and is never accepted from
        the UI as a user-supplied value.
        """

        user = self.get_current_user()

        if user is None:
            raise ValueError(
                "No authenticated user found."
            )

        row = {
            "user_id": user.id,

            "client_pma": record.get(
                "Client (PMA)"
            ),

            "system": record.get(
                "System (LMBS, PMBS, MMBS, OLMRTS)"
            ),

            "contract": record.get(
                "Contract"
            ),

            "document_type": record.get(
                "Document Type"
            ),

            "document_number": record.get(
                "Document Number"
            ),

            "date_of_issuance": record.get(
                "Date of Issuance"
            ),

            "amount": record.get(
                "Amount"
            ),

            "initiated_by": record.get(
                "Initiated By"
            ),

            "reviewed_by": record.get(
                "Reviewed By"
            ),

            "approved_by": record.get(
                "Approved by"
            ),

            "document_filename": document_filename,
        }

        response = (
            self.supabase
            .table("credentials")
            .insert(row)
            .execute()
        )

        if not response.data:
            raise ValueError(
                "Database insert returned no data."
            )

        return response.data[0]

    def get_user_credentials(self):
        """
        Retrieve credentials belonging to the
        authenticated user.

        RLS provides the database-level isolation.
        """

        response = (
            self.supabase
            .table("credentials")
            .select("*")
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return response.data

    def delete_credential(
        self,
        credential_id
    ):
        """Delete one credential belonging to the user."""

        if not credential_id:
            raise ValueError(
                "Credential ID is required."
            )

        response = (
            self.supabase
            .table("credentials")
            .delete()
            .eq("id", credential_id)
            .execute()
        )

        return response.data
