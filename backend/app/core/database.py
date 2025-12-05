"""
Database connection and initialization
"""
from supabase import create_client, Client
from app.core.config import settings
from typing import Optional

_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """Get Supabase client singleton"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


def get_supabase_admin() -> Client:
    """Get Supabase admin client (with service key)"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


async def init_db():
    """Initialize database connections"""
    # Test connection
    client = get_supabase()
    try:
        # Simple query to test connection
        client.table("departments").select("id").limit(1).execute()
    except Exception as e:
        print(f"Database connection warning: {e}")
    print("Database initialized")

