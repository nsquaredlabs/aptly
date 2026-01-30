from supabase import create_client, Client
from src.config import settings

# Initialize Supabase client with service role key (bypasses RLS)
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)
