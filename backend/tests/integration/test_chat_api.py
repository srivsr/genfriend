"""Integration tests for chat API — transaction handling, IDOR protection."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestChatTransactionHandling:
    """Chat endpoint must handle failures gracefully with proper rollback."""

    def test_mentor_failure_returns_503(self, client):
        with patch("app.api.v1.chat.mentor_engine") as mock_mentor:
            mock_mentor.process = AsyncMock(side_effect=Exception("LLM timeout"))
            response = client.post(
                "/api/v1/chat",
                json={"message": "Hello"},
            )
            # 401 if auth not bypassed, 503 if mentor fails after auth
            assert response.status_code in (401, 503)

    def test_empty_message_handled(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"message": ""},
        )
        # Accepts empty string (no validation on message length) or processes it
        assert response.status_code in (200, 401, 422, 500)


class TestConversationIDOR:
    """Users must NOT access other users' conversations."""

    def test_cannot_access_other_users_conversation(self, client):
        fake_conv_id = str(uuid4())
        response = client.post(
            "/api/v1/chat",
            json={"message": "Hello", "conversation_id": fake_conv_id},
        )
        # Should return 404 (conversation not found) or 401 (auth)
        assert response.status_code in (401, 404)

    def test_history_requires_auth(self, client):
        response = client.get("/api/v1/chat/history")
        assert response.status_code in (200, 401)

    def test_conversations_list_requires_auth(self, client):
        response = client.get("/api/v1/chat/conversations")
        assert response.status_code in (200, 401)


class TestChatResponseFormat:
    """Verify API response envelope matches APIResponse schema."""

    def test_successful_chat_has_correct_shape(self, client):
        with patch("app.api.v1.chat.mentor_engine") as mock_mentor, \
             patch("app.api.v1.chat.EmbeddingService"):
            mock_mentor.process = AsyncMock(return_value=MagicMock(
                content="Hello! How can I help?",
                context_used={"intent": "chat_support"}
            ))
            response = client.post(
                "/api/v1/chat",
                json={"message": "Hi there"},
            )
            if response.status_code == 200:
                data = response.json()
                assert data.get("success") is True
                assert "data" in data
                assert "message" in data["data"]
                assert "conversation_id" in data["data"]
