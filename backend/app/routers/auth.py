"""Auth router — OAuth flows (GitHub, GitLab, Bitbucket, Discord) and session management.

All OAuth logic is self-contained within the app.* namespace. No legacy imports.
Each provider module returns native data (OAuthResult) that this router converts
directly into FastAPI responses.

Requirements: 4.2
"""

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.auth.jwt import get_current_user
from app.auth.github import start_github_oauth, handle_github_callback
from app.auth.gitlab import start_gitlab_oauth, handle_gitlab_callback
from app.auth.bitbucket import start_bitbucket_oauth, handle_bitbucket_callback
from app.config import Settings
from app.dependencies import get_settings
from app.services.session_store import delete_all_user_sessions

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------


@router.get("/auth/github/start")
async def github_start(settings: Settings = Depends(get_settings)):
    """Initiate GitHub OAuth flow. Redirects to GitHub authorization URL."""
    try:
        redirect_url = await start_github_oauth(settings)
        return RedirectResponse(url=redirect_url, status_code=302)
    except Exception as e:
        logger.error("GitHub OAuth start error: %s", e)
        return JSONResponse(status_code=500, content={"error": "Configuration error"})


@router.get("/auth/github/callback")
async def github_callback(
    code: str = Query(default=None),
    settings: Settings = Depends(get_settings),
):
    """Handle GitHub OAuth callback. Exchanges code for token and redirects to frontend."""
    if not code:
        return JSONResponse(status_code=400, content={"detail": "Invalid request"})

    try:
        result = await handle_github_callback(code, settings)
        response = RedirectResponse(url=result.redirect_url, status_code=302)
        for cookie in result.cookies:
            response.headers.append("set-cookie", cookie)
        return response
    except Exception as e:
        logger.error("GitHub OAuth callback error: %s", e)
        return JSONResponse(status_code=401, content={"error": "Authentication failed"})


# ---------------------------------------------------------------------------
# GitLab OAuth
# ---------------------------------------------------------------------------


@router.get("/auth/gitlab/start")
async def gitlab_start(settings: Settings = Depends(get_settings)):
    """Initiate GitLab OAuth flow. Redirects to GitLab authorization URL."""
    try:
        redirect_url = await start_gitlab_oauth(settings)
        return RedirectResponse(url=redirect_url, status_code=302)
    except Exception as e:
        logger.error("GitLab OAuth start error: %s", e)
        return JSONResponse(status_code=500, content={"error": "Configuration error"})


@router.get("/auth/gitlab/callback")
async def gitlab_callback(
    code: str = Query(default=None),
    settings: Settings = Depends(get_settings),
):
    """Handle GitLab OAuth callback. Exchanges code for token and redirects to frontend."""
    if not code:
        return JSONResponse(status_code=400, content={"detail": "Invalid request"})

    try:
        result = await handle_gitlab_callback(code, settings)
        response = RedirectResponse(url=result.redirect_url, status_code=302)
        for cookie in result.cookies:
            response.headers.append("set-cookie", cookie)
        return response
    except Exception as e:
        logger.error("GitLab OAuth callback error: %s", e)
        return JSONResponse(status_code=401, content={"error": "Authentication failed"})


# ---------------------------------------------------------------------------
# Bitbucket OAuth
# ---------------------------------------------------------------------------


@router.get("/auth/bitbucket/start")
async def bitbucket_start(settings: Settings = Depends(get_settings)):
    """Initiate Bitbucket OAuth flow. Redirects to Bitbucket authorization URL."""
    try:
        redirect_url = await start_bitbucket_oauth(settings)
        return RedirectResponse(url=redirect_url, status_code=302)
    except Exception as e:
        logger.error("Bitbucket OAuth start error: %s", e)
        return JSONResponse(status_code=500, content={"error": "Configuration error"})


@router.get("/auth/bitbucket/callback")
async def bitbucket_callback(
    code: str = Query(default=None),
    settings: Settings = Depends(get_settings),
):
    """Handle Bitbucket OAuth callback. Exchanges code for token and redirects to frontend."""
    if not code:
        return JSONResponse(status_code=400, content={"detail": "Invalid request"})

    try:
        result = await handle_bitbucket_callback(code, settings)
        response = RedirectResponse(url=result.redirect_url, status_code=302)
        for cookie in result.cookies:
            response.headers.append("set-cookie", cookie)
        return response
    except Exception as e:
        logger.error("Bitbucket OAuth callback error: %s", e)
        return JSONResponse(status_code=401, content={"error": "Authentication failed"})


# ---------------------------------------------------------------------------
# Discord OAuth
# ---------------------------------------------------------------------------


@router.get("/auth/discord/start")
async def discord_start(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Initiate Discord OAuth flow. Requires authentication.

    The Discord OAuth start differs from other providers because it needs the
    authenticated user's ID to create a CSRF state linked to their account.
    """
    from app.services.discord_identity import start_oauth as discord_start_oauth

    user_id = user.get("sub")
    try:
        redirect_url = discord_start_oauth(user_id, settings)
        return RedirectResponse(url=redirect_url, status_code=302)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})


@router.get("/auth/discord/callback")
async def discord_callback(
    code: str = Query(default=None),
    state: str = Query(default=None),
    settings: Settings = Depends(get_settings),
):
    """Handle Discord OAuth callback. Uses state parameter for CSRF validation."""
    from app.services.discord_identity import handle_callback as discord_handle_callback

    if not code or not state:
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?discord=error", status_code=302
        )

    try:
        discord_handle_callback(code, state, settings)
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?discord=pending", status_code=302
        )
    except (ValueError, Exception) as e:
        logger.error("Discord callback failed: %s", str(e))
        return RedirectResponse(
            url=f"{settings.frontend_url}/dashboard?discord=error", status_code=302
        )


# ---------------------------------------------------------------------------
# Session management: /me and /logout
# ---------------------------------------------------------------------------


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Return the authenticated user's token payload.

    The get_current_user dependency already validates the JWT and returns
    the decoded payload including is_admin.
    """
    return JSONResponse(
        status_code=200,
        content={
            "user_id": user.get("sub"),
            "username": user.get("name"),
            "avatar_url": user.get("avatar"),
            "provider": user.get("provider", "github"),
            "is_admin": user.get("is_admin", False),
        },
    )


@router.post("/logout")
async def logout(
    user: dict = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    """Logout user by revoking all refresh tokens for the user."""
    user_id = user.get("sub")
    if user_id:
        try:
            delete_all_user_sessions(
                table_name=settings.progress_table,
                user_id=user_id,
            )
        except Exception as e:
            logger.error("Failed to revoke sessions during logout: %s", e)

    return JSONResponse(status_code=200, content={"message": "Logged out"})
