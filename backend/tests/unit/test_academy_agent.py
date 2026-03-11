"""Tests for AcademyAgent — AI topic identification and explanation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.academy import AcademyAgent, AI_TOPICS
from app.agents.base import AgentContext


@pytest.fixture
def academy():
    agent = AcademyAgent()
    agent.llm = AsyncMock()
    agent.llm.generate = AsyncMock(return_value=MagicMock(content="RAG is like a librarian..."))
    return agent


class TestTopicIdentification:
    def test_identifies_rag(self, academy):
        assert academy._identify_topic("What is RAG?") == "rag"

    def test_identifies_embeddings(self, academy):
        assert academy._identify_topic("How do embeddings work?") == "embeddings"

    def test_identifies_llm(self, academy):
        assert academy._identify_topic("Tell me about LLM models") == "llm"

    def test_identifies_agents(self, academy):
        assert academy._identify_topic("What are AI agents?") == "agents"

    def test_identifies_prompting(self, academy):
        assert academy._identify_topic("Teach me prompting techniques") == "prompting"

    def test_identifies_memory(self, academy):
        assert academy._identify_topic("How does AI memory work?") == "memory"

    def test_identifies_fine_tuning(self, academy):
        assert academy._identify_topic("What is fine-tuning?") == "fine-tuning"

    def test_unknown_topic(self, academy):
        assert academy._identify_topic("What is quantum computing?") == "general"


class TestExplain:
    @pytest.mark.asyncio
    async def test_returns_explanation(self, academy):
        response = await academy.explain("What is RAG?")
        assert response.content == "RAG is like a librarian..."
        assert response.data["topic"] == "rag"

    @pytest.mark.asyncio
    async def test_prompt_includes_base_knowledge(self, academy):
        await academy.explain("Explain embeddings to me")
        call_args = academy.llm.generate.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "embeddings" in prompt.lower()
        assert AI_TOPICS["embeddings"][:20] in prompt

    @pytest.mark.asyncio
    async def test_general_topic_no_base_knowledge(self, academy):
        await academy.explain("What is blockchain?")
        call_args = academy.llm.generate.call_args
        prompt = call_args.kwargs.get("prompt", call_args.args[0] if call_args.args else "")
        assert "Base context:" not in prompt


class TestProcess:
    @pytest.mark.asyncio
    async def test_process_delegates_to_explain(self, academy):
        ctx = AgentContext(user_id="test")
        response = await academy.process("What is RAG?", ctx)
        assert response.data["topic"] == "rag"
