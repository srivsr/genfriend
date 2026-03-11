"""Tests for authentication and authorization — dev mode bypass, Clerk token validation."""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException


class TestDevModeAuth:
    """Dev mode MUST be explicitly enabled — never default to bypass."""

    def test_dev_mode_requires_explicit_env(self):
        from app.dependencies import IS_DEV_MODE, ENVIRONMENT
        # In test environment (set in conftest), IS_DEV_MODE should be True
        assert ENVIRONMENT in ("development", "dev", "local", "test")
        assert IS_DEV_MODE is True

    @pytest.mark.asyncio
    async def test_dev_mode_returns_dev_user(self):
        from app.dependencies import get_current_user_id, DEV_USER_UUID
        with patch("app.dependencies.IS_DEV_MODE", True), \
             patch("app.dependencies.CLERK_SECRET_KEY", None):
            user_id = await get_current_user_id(credentials=None)
            assert user_id == DEV_USER_UUID

    @pytest.mark.asyncio
    async def test_production_rejects_no_credentials(self):
        from app.dependencies import get_current_user_id
        with patch("app.dependencies.IS_DEV_MODE", False), \
             patch("app.dependencies.CLERK_SECRET_KEY", None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id(credentials=None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_clerk_key_non_dev_raises_503(self):
        from app.dependencies import verify_clerk_token
        with patch("app.dependencies.CLERK_SECRET_KEY", None), \
             patch("app.dependencies.IS_DEV_MODE", False):
            with pytest.raises(HTTPException) as exc_info:
                await verify_clerk_token("some-token")
            assert exc_info.value.status_code == 503


class TestClerkTokenVerification:
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        from app.dependencies import verify_clerk_token
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sub": "user_123", "email": "test@example.com"}

        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "email_addresses": [{"email_address": "test@example.com"}]
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_response, mock_user_response])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.dependencies.CLERK_SECRET_KEY", "sk_test_123"), \
             patch("app.dependencies.IS_DEV_MODE", False), \
             patch("httpx.AsyncClient", return_value=mock_client):
            result = await verify_clerk_token("valid-token")
            assert result["user_id"] == "user_123"
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        from app.dependencies import verify_clerk_token
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.dependencies.CLERK_SECRET_KEY", "sk_test_123"), \
             patch("app.dependencies.IS_DEV_MODE", False), \
             patch("httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(HTTPException) as exc_info:
                await verify_clerk_token("expired-token")
            assert exc_info.value.status_code == 401


class TestEnsureUserExists:
    @pytest.mark.asyncio
    async def test_creates_user_if_not_exists(self):
        from app.dependencies import ensure_user_exists, _user_cache
        _user_cache.discard("new-user-id")  # Clear cache

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # User doesn't exist

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        await ensure_user_exists("new-user-id", "test@example.com", mock_db)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        _user_cache.discard("new-user-id")  # Cleanup

    @pytest.mark.asyncio
    async def test_skips_if_cached(self):
        from app.dependencies import ensure_user_exists, _user_cache
        _user_cache.add("cached-user")

        mock_db = AsyncMock()
        await ensure_user_exists("cached-user", "test@example.com", mock_db)
        mock_db.execute.assert_not_called()

        _user_cache.discard("cached-user")  # Cleanup
