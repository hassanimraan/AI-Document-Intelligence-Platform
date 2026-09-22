"""Supabase database module — implemented in a later phase."""
class DatabaseManager:
    def __init__(self, supabase_url=None, supabase_key=None):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
