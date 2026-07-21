"""Discord OAuth flow for the FastAPI application.

Discord OAuth start/callback are handled via the app.services.discord_identity
module which bridges to the membership service layer. This module is kept as a
namespace placeholder — the actual logic is invoked directly from the auth router.

Note: Unlike other OAuth providers, Discord requires authentication for the start
endpoint and uses state-based CSRF for the callback.
"""

# This file is intentionally minimal. Discord OAuth is invoked directly
# from app/routers/auth.py using app.services.discord_identity functions.
