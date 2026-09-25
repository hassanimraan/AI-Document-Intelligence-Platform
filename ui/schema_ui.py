import streamlit as st

def _get_active_workspace_id():
return st.session_state.get("active_workspace_id")

def render_schema_ui(supabase):
st.header("📋 Registers")
st.write("Schema UI loaded successfully.")
