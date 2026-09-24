```python
import streamlit as st
from supabase import create_client

from config.schema import EXTRACTION_FIELDS


class DatabaseManager:
    """
    Handles authenticated access to Supabase PostgreSQL.

    Normal application operations use the Supabase publishable
    key together with the authenticated user's session.

    RLS remains the database-level security boundary.
    """

    TABLE_NAME = "credentials"

    def __init__(self):
        self.url = st.secrets["SUPABASE_URL"]
        self.key = st.secrets[
            "SUPABASE_PUBLISHABLE_KEY"
        ]

        self.supabase = create_client(
            self.url,
            self.key,
        )

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    def set_user_session(
        self,
        access_token,
        refresh_token,
    ):
        """
        Attach the authenticated Supabase session.

        The access and refresh tokens are supplied by the
        application's authentication workflow.
        """

        if not access_token:
            raise ValueError(
                "Access token is missing."
            )

        if not refresh_token:
            raise ValueError(
                "Refresh token is missing."
            )

        try:
            self.supabase.auth.set_session(
                access_token,
                refresh_token,
            )

        except Exception as exc:
            raise ValueError(
                "Your authentication session could not "
                "be restored. Please log in again."
            ) from exc

    def get_current_user(self):
        """
        Return the currently authenticated Supabase user.

        get_user() is used instead of trusting user information
        supplied by the UI.
        """

        try:
            response = (
                self.supabase.auth.get_user()
            )

        except Exception as exc:
            raise ValueError(
                "Unable to verify the authenticated user. "
                "Please log in again."
            ) from exc

        user = response.user

        if user is None:
            raise ValueError(
                "No authenticated user was found."
            )

        return user

    # ========================================================
    # RECORD VALIDATION
    # ========================================================

    def _validate_record(self, record):
        """
        Validate the structure of a credential record before
        sending it to Supabase.
        """

        if not isinstance(record, dict):
            raise TypeError(
                "Credential record must be a dictionary."
            )

        unexpected_fields = (
            set(record.keys())
            - set(EXTRACTION_FIELDS)
        )

        if unexpected_fields:
            raise ValueError(
                "Credential record contains unexpected "
                f"fields: {sorted(unexpected_fields)}"
            )

    # ========================================================
    # INSERT
    # ========================================================

    def insert_credential(
        self,
        record,
        document_filename=None,
    ):
        """
        Insert a verified credential record.

        user_id is ALWAYS obtained from the authenticated
        Supabase user.

        The UI can never supply or override user_id.
        """

        self._validate_record(
            record
        )

        user = self.get_current_user()

        user_id = getattr(
            user,
            "id",
            None,
        )

        if not user_id:
            raise ValueError(
                "Authenticated user ID is unavailable."
            )

        # ----------------------------------------------------
        # Only map known application fields.
        # ----------------------------------------------------

        row = {
            "user_id": user_id,

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

            "document_filename": (
                document_filename
                if document_filename
                else None
            ),
        }

        try:

            response = (
                self.supabase
                .table(self.TABLE_NAME)
                .insert(row)
                .execute()
            )

        except Exception as exc:

            raise ValueError(
                "The credential record could not be saved "
                "to the database."
            ) from exc

        if not response.data:

            raise ValueError(
                "The database did not return the saved "
                "credential record."
            )

        return response.data[0]

    # ========================================================
    # RETRIEVE
    # ========================================================

    def get_user_credentials(self):
        """
        Retrieve credentials belonging to the authenticated
        user.

        RLS performs the actual database-level isolation.
        """

        # Force authentication verification before querying.
        self.get_current_user()

        try:

            response = (
                self.supabase
                .table(self.TABLE_NAME)
                .select("*")
                .order(
                    "created_at",
                    desc=True,
                )
                .execute()
            )

        except Exception as exc:

            raise ValueError(
                "Your credential records could not be loaded "
                "from the database."
            ) from exc

        return response.data or []

    # ========================================================
    # DELETE
    # ========================================================

    def delete_credential(
        self,
        credential_id,
    ):
        """
        Delete one credential.

        The authenticated user's RLS policy determines whether
        the requested record actually belongs to that user.
        """

        if not credential_id:
            raise ValueError(
                "Credential ID is required."
            )

        # Ensure a valid authenticated user exists before
        # attempting the database operation.
        self.get_current_user()

        try:

            response = (
                self.supabase
                .table(self.TABLE_NAME)
                .delete()
                .eq(
                    "id",
                    credential_id,
                )
                .execute()
            )

        except Exception as exc:

            raise ValueError(
                "The credential record could not be deleted."
            ) from exc

        return response.data or []
```
