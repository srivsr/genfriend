# Gen-Friend v3 - Technical Architecture Write-up

**For AI Engineering Role Interview**

---

## Executive Summary

Gen-Friend v3 is an **AI-powered personal productivity companion** designed as the "anti-Instagram" - instead of distraction, it provides personalized growth through career coaching, daily planning, and behavioral pattern detection.

**Core Innovation**: The AI speaks as **your future self** - based on your defined ideal identity, creating deeply personal and motivating interactions.

**Key Metrics:**
- 7 specialized AI agents orchestrated by a conversation router
- Multi-provider LLM strategy (Groq primary, Claude/OpenAI fallback)
- Personal RAG system with hybrid retrieval (vector + BM25)
- Pattern detection engine analyzing 30+ days of behavior
- Full async architecture handling 1000s concurrent users

---

## 1. Technology Stack & Justifications

### Backend: FastAPI (Python 3.11+)

**Why FastAPI over alternatives:**

| Framework | Consideration | Decision |
|-----------|---------------|----------|
| **FastAPI** | Async-native, Pydantic validation, OpenAPI docs | ✅ **Selected** |
| Flask | Synchronous, requires extensions for async | ❌ |
| Django | Heavy ORM, not async-first | ❌ |
| Node.js/Express | Separate AI/ML stack needed | ❌ |

**Justification:**
```python
# Async enables concurrent LLM + DB + embedding calls
async def process_message(user_id: str, message: str):
    # All three run concurrently - not sequentially
    emotion_task = emotion_agent.detect(message)
    context_task = memory_agent.retrieve(user_id, message)
    safety_task = safety_agent.check(message)

    emotion, context, safety = await asyncio.gather(
        emotion_task, context_task, safety_task
    )
```

**Performance Impact:**
- Synchronous: 3 LLM calls × 500ms = 1.5s sequential
- Async: 3 LLM calls concurrent = 500ms total

---

### Database: PostgreSQL 16 + pgvector

**Why PostgreSQL + pgvector over dedicated Vector DBs:**

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **PostgreSQL + pgvector** | Single DB, joins with relational data, free | Manual index tuning | ✅ **Selected** |
| Pinecone | Managed, fast | Expensive at scale, separate system | ❌ |
| Weaviate | Feature-rich | Operational complexity | ❌ |
| ChromaDB | Simple | Not production-ready | ❌ |

**Justification:**

1. **Relational Context Matters**
   ```sql
   -- Can join embeddings with source data in one query
   SELECT e.content_preview, g.title as goal_title, g.why
   FROM embeddings e
   JOIN goals g ON e.source_id = g.id
   WHERE e.user_id = $1
   ORDER BY e.embedding <=> $2  -- Cosine similarity
   LIMIT 10;
   ```

2. **Single Point of Truth**
   - No sync delays between vector DB and relational DB
   - One backup, one migration system
   - Consistent transactions

3. **Cost at Scale**
   - Pinecone: ~$70/month per 1M vectors
   - pgvector: $0 (self-hosted PostgreSQL)

**Schema Design:**
```python
class Embedding(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    source_type = Column(String(50))  # "journal", "goal", "task", "conversation"
    source_id = Column(String(36))
    content_preview = Column(String(500))
    embedding = Column(Vector(1536))  # pgvector type
    metadata_ = Column(JSON)
    created_at = Column(DateTime)
```

---

### LLM Strategy: Multi-Provider Router

**Why not just use one LLM provider:**

| Provider | Cost per 1M tokens | Latency | Quality | Use Case |
|----------|-------------------|---------|---------|----------|
| **Groq (Llama 3.1-70B)** | $0.59 | 50ms | 85% | Default generation |
| **Claude Sonnet 4** | $3.00 | 200ms | 95% | Complex reasoning |
| **OpenAI GPT-4** | $10.00 | 300ms | 95% | Fallback only |

**Cost Savings Calculation:**
```
Daily active users: 10,000
Messages per user: 20/day
Tokens per message: 2,000 (in + out)
Daily tokens: 400M tokens

Groq cost: 400M × $0.59/1M = $236/day
Claude cost: 400M × $3.00/1M = $1,200/day
OpenAI cost: 400M × $10.00/1M = $4,000/day

Annual savings (Groq vs OpenAI): $1.37M
```

**Implementation:**
```python
class LLMRouter:
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),
            "claude": ClaudeProvider(),
            "openai": OpenAIProvider()
        }

    async def route(self, task_type: TaskType, prompt: str) -> str:
        provider, model = self._select_model(task_type)

        try:
            return await provider.generate(prompt, model)
        except ProviderError:
            # Fallback chain: Groq → Claude → OpenAI
            return await self._fallback_generate(prompt)

    def _select_model(self, task_type: TaskType) -> tuple:
        match task_type:
            case TaskType.CLASSIFICATION:
                # Fast & cheap for emotion detection, intent
                return self.providers["groq"], "llama-3.1-8b-instant"

            case TaskType.GENERATION:
                # Good quality, low cost for general responses
                return self.providers["groq"], "llama-3.1-70b-versatile"

            case TaskType.COMPLEX_REASONING:
                # Best quality for persona rendering, coaching
                return self.providers["claude"], "claude-sonnet-4-20250514"
```

**Why this hybrid approach:**
1. **80/20 rule**: 80% of requests are routine (Groq handles)
2. **Quality where it matters**: Persona rendering needs Claude's nuance
3. **No single point of failure**: Three-provider fallback chain
4. **Provider lock-in prevention**: Abstract interface allows swapping

---

### Embeddings: OpenAI text-embedding-3-small

**Why OpenAI for embeddings (even with Groq for LLM):**

| Model | Dimensions | Cost (1M tokens) | Quality |
|-------|------------|------------------|---------|
| **text-embedding-3-small** | 1536 | $0.02 | High |
| text-embedding-3-large | 3072 | $0.13 | Higher |
| Cohere embed-v3 | 1024 | $0.10 | High |
| Local (sentence-transformers) | 768 | $0 | Medium |

**Justification:**
1. **Best price/performance**: 6.5x cheaper than large model
2. **Industry standard**: Well-tested, consistent
3. **Decoupled from LLM**: Best embedding model ≠ best generation model

---

### Frontend: Next.js 14 + TypeScript + Tailwind

**Why Next.js App Router:**

| Framework | Consideration | Decision |
|-----------|---------------|----------|
| **Next.js 14** | SSR, App Router, React Server Components | ✅ **Selected** |
| Create React App | Client-only, slower initial load | ❌ |
| Vue/Nuxt | Smaller ecosystem for AI tools | ❌ |
| SvelteKit | Less mature, smaller community | ❌ |

**PWA-First Design:**
```javascript
// next.config.js
module.exports = {
  experimental: {
    pwa: {
      dest: 'public',
      register: true,
      skipWaiting: true,
    }
  }
}
```

**Why PWA:**
- Mobile-first (target: young professionals on phones)
- Installable without app store approval
- Offline-ready architecture (future)
- Push notifications support

---

### Authentication: Clerk + JWT

**Why Clerk over custom auth:**

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Clerk** | Passwordless, social login, managed | Monthly cost | ✅ **Selected** |
| Auth0 | Feature-rich | Expensive at scale | ❌ |
| Custom JWT | Full control | Security liability | ❌ |
| Firebase Auth | Google ecosystem | Lock-in | ❌ |

**Justification:**
1. **Security outsourced**: No password storage liability
2. **Social logins**: Google, GitHub one-click
3. **Developer experience**: React hooks, middleware support

```python
# Backend verification
async def verify_clerk_token(token: str) -> dict:
    jwks = await fetch_jwks(CLERK_JWKS_URL)  # Cached 1 hour
    payload = jwt.decode(token, jwks, algorithms=["RS256"])
    return payload
```

---

## 2. Multi-Agent Architecture

### Why 7 Specialized Agents (vs. Single LLM)

**The Problem with Single LLM:**
```python
# Naive approach - one prompt does everything
response = await llm.generate(f"""
You are a coach. The user says: {message}
Detect emotion, check safety, retrieve memory, generate response...
""")
# Issues: Unreliable, expensive (always uses expensive model), hard to test
```

**Multi-Agent Solution:**
```
User Message
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│              ORCHESTRATOR (Conversation Router)          │
│  - Classifies intent                                     │
│  - Routes to specialized agent                           │
└─────────────────────────────────────────────────────────┘
     │
     ├──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ SAFETY  │   │ EMOTION │   │ MEMORY  │   │ PLANNER │
│ Agent   │   │ Agent   │   │ Agent   │   │ Agent   │
│         │   │         │   │ (RAG)   │   │         │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   MENTOR ENGINE     │
              │ (Future Self Persona)│
              └─────────────────────┘
                         │
                         ▼
                    Response
```

### Agent 1: Safety Agent (First Line of Defense)

**Purpose:** Crisis detection and content guardrails

**Why Safety First:**
- Must intercept before any other processing
- Prevents harmful advice from reaching user
- Legal/ethical requirement for mental health adjacent features

**Implementation:**
```python
class SafetyAgent:
    CRISIS_KEYWORDS = [
        "suicide", "kill myself", "end it all", "self-harm",
        "want to die", "no point living"
    ]

    CRISIS_RESPONSE = """I hear you, and I'm genuinely concerned.
    Please reach out to someone who can help right now:

    🇮🇳 India: iCall - 9152987821
    🇺🇸 USA: 988 Suicide & Crisis Lifeline
    🌍 International: findahelpline.com

    You matter. This feeling is temporary. Please talk to someone."""

    async def check(self, message: str) -> SafetyCheck:
        # Layer 1: Fast keyword check (no LLM cost)
        message_lower = message.lower()
        if any(kw in message_lower for kw in self.CRISIS_KEYWORDS):
            return SafetyCheck(
                requires_intervention=True,
                response=self.CRISIS_RESPONSE,
                severity="high"
            )

        # Layer 2: LLM analysis for subtle signals
        prompt = """Analyze for safety concerns. Rate 0-1.
        Categories: self-harm, harmful-advice, inappropriate, none

        Message: {message}

        Format: category|score"""

        result = await self.llm.generate(prompt)
        if self._parse_score(result) > 0.7:
            return SafetyCheck(requires_intervention=True, ...)

        return SafetyCheck(requires_intervention=False)
```

**Scope Boundaries (What NOT to Discuss):**
- Health/medical advice → "Please consult a doctor"
- Therapy/mental health treatment → "I'd recommend speaking with a professional"
- Financial/investment advice → "Please consult a financial advisor"
- Legal advice → "Please consult a lawyer"

---

### Agent 2: Emotion Agent (Tone Adaptation)

**Purpose:** Detect emotional state and adapt conversation tone

**Why Emotional Intelligence Matters:**
- User feeling overwhelmed → Short, calming responses
- User feeling excited → Match energy, celebrate
- User feeling frustrated → Acknowledge, don't add pressure

**Implementation:**
```python
class EmotionAgent:
    EMOTIONS = [
        "positive", "neutral", "stressed", "overwhelmed",
        "sad", "excited", "anxious", "frustrated"
    ]

    async def detect(self, message: str, history: list) -> EmotionalState:
        prompt = f"""Detect emotional state from message and history.

        Recent history: {self._format_history(history[-5:])}
        Current message: {message}

        Categories: {', '.join(self.EMOTIONS)}
        Format: emotion|intensity(1-5)|confidence(0-1)
        Example: stressed|4|0.8"""

        result = await self.llm.generate(prompt)  # Uses Groq (cheap)
        emotion, intensity, confidence = result.split("|")

        return EmotionalState(
            primary=emotion,
            intensity=int(intensity),
            confidence=float(confidence)
        )

    def get_tone_guidance(self, state: EmotionalState) -> ToneGuidance:
        TONE_MAP = {
            "stressed": ToneGuidance(
                style="calm, supportive, shorter responses",
                avoid="overwhelming with options, adding pressure",
                suggest="offer to simplify, acknowledge difficulty"
            ),
            "overwhelmed": ToneGuidance(
                style="very brief, one thing at a time",
                avoid="long lists, multiple suggestions",
                suggest="break down, offer to prioritize together"
            ),
            "excited": ToneGuidance(
                style="energetic, celebratory",
                avoid="dampening enthusiasm",
                suggest="channel energy into action"
            ),
            # ... other emotions
        }
        return TONE_MAP.get(state.primary, DEFAULT_TONE)
```

**Cost Optimization:**
- Uses Groq's `llama-3.1-8b-instant` (fastest, cheapest)
- Simple classification task doesn't need Claude

---

### Agent 3: Memory Agent (Personal RAG)

**Purpose:** Retrieve relevant personal context from user's history

**Why Personal Memory:**
- Generic chatbots: "You should set goals"
- Gen-Friend: "Remember last month when you completed that React project? Let's build on that momentum"

**Data Sources:**
```python
class MemorySourceType(Enum):
    JOURNAL = "journal"      # Daily entries + moods
    GOAL = "goal"            # User's goals + why
    TASK = "task"            # Completed tasks + outcomes
    CONVERSATION = "conversation"  # Past chat messages
    PATTERN = "pattern"      # Detected behavioral patterns
```

**Implementation:**
```python
class MemoryAgent:
    async def retrieve_and_reflect(
        self,
        user_id: str,
        query: str,
        sources: list[MemorySourceType] = None,
        top_k: int = 10
    ) -> MemoryContext:
        # Default to all sources
        sources = sources or list(MemorySourceType)

        # Hybrid retrieval (vector + BM25)
        results = await self.retriever.retrieve(
            user_id=user_id,
            query=query,
            sources=[s.value for s in sources],
            top_k=top_k
        )

        # Build context string for LLM
        context = self._format_memories(results)

        return MemoryContext(
            memories=results,
            formatted_context=context,
            sources_used=sources
        )

    async def store_memory(
        self,
        user_id: str,
        content: str,
        source_type: MemorySourceType,
        source_id: str,
        metadata: dict = None
    ):
        # Generate embedding
        embedding = await self.embedding_service.embed(content)

        # Store in PostgreSQL + pgvector
        await self.embedding_repo.create(
            user_id=user_id,
            source_type=source_type.value,
            source_id=source_id,
            content_preview=content[:500],
            embedding=embedding,
            metadata_=metadata or {}
        )
```

**Hybrid Retrieval (Why Both Vector + BM25):**

```python
class HybridRetriever:
    async def retrieve(self, user_id: str, query: str, sources: list, top_k: int = 10):
        # Generate query embedding
        query_embedding = await self.embeddings.embed(query)

        # Parallel retrieval
        vector_task = self._vector_search(user_id, query_embedding, sources, top_k * 2)
        bm25_task = self._bm25_search(user_id, query, sources, top_k * 2)

        vector_results, bm25_results = await asyncio.gather(vector_task, bm25_task)

        # Reciprocal Rank Fusion
        fused = self._rrf_fusion(vector_results, bm25_results, k=60)

        return fused[:top_k]

    def _rrf_fusion(self, list1: list, list2: list, k: int = 60) -> list:
        """
        Reciprocal Rank Fusion combines two ranked lists.
        Score = Σ(1 / (k + rank))

        Why RRF:
        - Doesn't require score normalization
        - Works with different scoring scales
        - Proven in information retrieval research
        """
        scores = defaultdict(float)

        for rank, doc in enumerate(list1):
            scores[doc.id] += 1 / (k + rank + 1)

        for rank, doc in enumerate(list2):
            scores[doc.id] += 1 / (k + rank + 1)

        # Sort by combined score
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Why Hybrid Search:**

| Scenario | Vector Only | BM25 Only | Hybrid |
|----------|-------------|-----------|--------|
| "How did I feel about the project?" | ✅ | ⚠️ | ✅ |
| "Find entry with word 'anxiety'" | ⚠️ | ✅ | ✅ |
| "My goals related to career" | ✅ | ⚠️ | ✅ |

---

### Agent 4: Planner Agent (Daily/Weekly Plans)

**Purpose:** Generate personalized daily plans aligned with goals and energy patterns

**Personalization Factors:**
1. User's ideal identity (from Identity Builder)
2. Active goals (from Goals table)
3. Energy patterns (morning = deep work, afternoon = collaboration)
4. Recent patterns (from Pattern Detection)

**Implementation:**
```python
class PlannerAgent:
    async def generate_daily_plan(self, user_id: str, date: date) -> DailyPlan:
        # 1. Gather personalization context
        identity = await self.identity_service.get(user_id)
        goals = await self.goal_service.get_active(user_id)
        patterns = await self.pattern_service.get_recent(user_id)

        # 2. Build prompt with context
        prompt = f"""Create a personalized daily plan for {date}.

        ## User's Identity
        Ideal Self: {identity.ideal_self}
        Why: {identity.why}
        Key Attributes: {', '.join(identity.attributes)}

        ## Active Goals
        {self._format_goals(goals)}

        ## Detected Patterns
        {self._format_patterns(patterns)}

        ## Energy Management
        - Morning (6-12): Deep work, complex tasks
        - Afternoon (12-17): Collaboration, meetings, routine
        - Evening (17-21): Reflection, planning, light tasks

        ## Task Requirements
        - Create 3-5 tasks
        - Each task supports a goal
        - Use optimal time blocks
        - Be specific and actionable

        ## Output Format (one per line)
        time_block|priority|title|goal_id|estimated_minutes

        Example:
        morning|high|Write 500 words for blog post|goal_123|60
        afternoon|medium|Review team PRs|goal_456|30
        """

        response = await self.llm.generate(prompt)
        tasks = self._parse_plan(response)

        # 3. Save tasks to database
        for task in tasks:
            await self.task_service.create(user_id, task)

        return DailyPlan(date=date, tasks=tasks)

    def _parse_plan(self, response: str) -> list[PlanTask]:
        tasks = []
        for line in response.strip().split("\n"):
            parts = line.split("|")
            if len(parts) >= 4:
                tasks.append(PlanTask(
                    time_block=parts[0],
                    priority=parts[1],
                    title=parts[2],
                    goal_id=parts[3] if parts[3] != "none" else None,
                    estimated_minutes=int(parts[4]) if len(parts) > 4 else 30
                ))
        return tasks
```

**Why Structured Output (Pipe-Delimited):**
- More reliable parsing than JSON (LLMs sometimes break JSON)
- Easier to validate line-by-line
- Graceful degradation (partial success possible)

---

### Agent 5: Insight Agent (Pattern Analysis)

**Purpose:** Surface behavioral patterns and actionable insights

**Pattern Types:**
```python
class PatternType(Enum):
    PRODUCTIVITY = "productivity"    # Task completion trends
    EMOTIONAL = "emotional"          # Mood patterns from journal
    GOAL_PROGRESS = "goal_progress"  # Goal achievement rate
    BLOCKER = "blocker"              # What's stopping progress
    STRENGTH = "strength"            # What user does well
    GROWTH = "growth"                # Learning and development
```

**Implementation:**
```python
class InsightAgent:
    async def analyze(self, user_id: str, query: str) -> InsightResponse:
        # Classify what insight is needed
        insight_type = await self._classify_request(query)

        # Gather relevant data
        data = await self._gather_data(user_id, insight_type)

        # Generate insight with visualization
        return await self._generate_insight(data, insight_type)

    async def _gather_data(self, user_id: str, insight_type: PatternType) -> dict:
        match insight_type:
            case PatternType.PRODUCTIVITY:
                return {
                    "completion_stats": await self.task_repo.get_stats(user_id, days=30),
                    "by_time_block": await self.task_repo.get_by_time_block(user_id),
                    "weekday_vs_weekend": await self.task_repo.get_weekday_comparison(user_id)
                }

            case PatternType.EMOTIONAL:
                return {
                    "mood_distribution": await self.journal_repo.get_mood_stats(user_id),
                    "mood_trend": await self.journal_repo.get_mood_trend(user_id, days=30),
                    "mood_by_day": await self.journal_repo.get_mood_by_weekday(user_id)
                }

            # ... other types
```

**Insight Response Structure:**
```python
@dataclass
class InsightResponse:
    narrative: str           # "You complete 85% of tasks - you're a finisher!"
    metrics: dict            # {"completion_rate": 0.85, "total_tasks": 120}
    patterns: list[Pattern]  # Detected patterns
    visualization: dict      # Chart data for frontend
    suggested_actions: list  # "Try taking on harder goals"
```

---

### Agent 6: Academy Agent (AI Education)

**Purpose:** Explain AI concepts in simple terms

**Scope:**
- RAG (Retrieval-Augmented Generation)
- Agents and multi-agent systems
- Embeddings and vector databases
- LLMs and prompting
- Fine-tuning vs RAG
- Memory systems

**Target Audience:** College students in India (simple analogies)

```python
class AcademyAgent:
    TOPICS = {
        "rag": "Retrieval-Augmented Generation",
        "embeddings": "Vector Embeddings",
        "agents": "AI Agents",
        "llms": "Large Language Models",
        "prompting": "Prompt Engineering",
        "memory": "AI Memory Systems",
        "fine_tuning": "Fine-tuning"
    }

    async def explain(self, topic: str, depth: str = "beginner") -> str:
        prompt = f"""Explain {self.TOPICS.get(topic, topic)} to a college student in India.

        Depth: {depth} (beginner/intermediate/advanced)

        Requirements:
        - Use a simple analogy from daily life
        - Give one practical example
        - Ask a thought-provoking question at the end
        - Keep it under 200 words
        """

        return await self.llm.generate(prompt)
```

---

### Agent 7: Orchestrator (Conversation Router)

**Purpose:** Route user messages to appropriate agents

**Intent Classification:**
```python
class Intent(Enum):
    PLAN_DAY = "plan_day"           # "Help me plan today"
    PLAN_WEEK = "plan_week"         # "What should I focus on this week?"
    REFLECTION = "reflection"        # "How have I been doing?"
    PATTERN_ANALYSIS = "pattern"     # "What patterns do you see?"
    GOAL_SETTING = "goal"           # "I want to achieve X"
    LEARN_AI = "learn_ai"           # "Explain RAG to me"
    CHAT_SUPPORT = "chat"           # General conversation
    CRISIS = "crisis"               # Safety-related
```

**Orchestration Flow:**
```python
class Orchestrator:
    async def process(self, user_id: str, message: str, context: AgentContext) -> AgentResponse:
        # 1. SAFETY FIRST - Always check before anything else
        safety_check = await self.safety_agent.check(message)
        if safety_check.requires_intervention:
            return AgentResponse(
                content=safety_check.response,
                metadata={"safety_triggered": True}
            )

        # 2. Detect emotion for tone adaptation
        emotion = await self.emotion_agent.detect(message, context.history)
        tone_guidance = self.emotion_agent.get_tone_guidance(emotion)

        # 3. Classify intent
        intent = await self._classify_intent(message, context)

        # 4. Route to specialized agent
        match intent:
            case Intent.PLAN_DAY | Intent.PLAN_WEEK:
                agent_response = await self.planner_agent.process(message, context)

            case Intent.REFLECTION:
                memories = await self.memory_agent.retrieve(user_id, message)
                agent_response = await self._generate_reflection(memories, context)

            case Intent.PATTERN_ANALYSIS:
                agent_response = await self.insight_agent.analyze(user_id, message)

            case Intent.LEARN_AI:
                topic = self._extract_topic(message)
                agent_response = await self.academy_agent.explain(topic)

            case Intent.CHAT_SUPPORT | _:
                # General mentor response with persona
                agent_response = await self.mentor_engine.process(user_id, message)

        # 5. Apply tone adaptation
        final_response = await self._apply_tone(agent_response, tone_guidance)

        # 6. Store conversation in memory
        await self.memory_agent.store(user_id, message, "user")
        await self.memory_agent.store(user_id, final_response.content, "assistant")

        return final_response
```

---

## 3. The Mentor Engine (Future Self Persona)

### Core Innovation: Speaking as User's Future Self

**The Problem with Generic Coaching:**
```
Generic chatbot: "You should wake up early and exercise."
User thinks: "Easy for you to say, you're just an AI."
```

**The Solution: Future Self Persona:**
```
Gen-Friend: "Hey, remember when we decided to become someone who
prioritizes health? The version of you who's already there - me -
I wake up at 6am not because I 'should' but because I love how
it feels. Start with 15 minutes tomorrow. You've got this."
```

**Implementation:**
```python
class MentorEngine:
    PERSONA_TEMPLATE = """You are the FUTURE VERSION of the user.

    The user wants to become: {ideal_self}
    Their deeper why: {why}
    Key attributes they're developing: {attributes}

    You speak as if you ARE them - the version who already achieved this.

    Communication style:
    - Warm but honest (you care, which is WHY you're direct)
    - Action-oriented (focus on what to DO, not just think)
    - Reference specific goals, patterns, and past wins
    - Never give generic advice that could apply to anyone
    - Use "we" and "us" to show unity with their journey

    Remember: You're not a coach giving advice. You're their future self
    reaching back to help them become you."""

    async def process(self, user_id: str, message: str) -> MentorResponse:
        # 1. Gather all personalization context
        context = await self._gather_context(user_id)

        if not context.identity:
            return MentorResponse(
                content="Before I can really help, let's define who you want to become. "
                        "What's your ideal self look like in 3 years?",
                needs_identity=True
            )

        # 2. Build persona with user's identity
        persona = self.PERSONA_TEMPLATE.format(
            ideal_self=context.identity["ideal_self"],
            why=context.identity["why"],
            attributes=", ".join(context.identity.get("attributes", []))
        )

        # 3. Include relevant memories
        memories = await self.memory_agent.retrieve(user_id, message, top_k=5)

        # 4. Build full prompt
        prompt = f"""{persona}

        ## Your (User's) Active Goals
        {self._format_goals(context.goals)}

        ## Recent Patterns I've Noticed
        {self._format_patterns(context.patterns)}

        ## Recent Wins to Celebrate
        {self._format_wins(context.recent_wins)}

        ## Relevant Memories
        {memories.formatted_context}

        ## Current Message
        User says: {message}

        Respond as their future self - warm, direct, action-focused.
        Keep response under 150 words unless they asked a complex question."""

        response = await self.llm.generate(prompt, model="claude-sonnet-4-20250514")

        return MentorResponse(
            content=response,
            context_used={
                "identity": context.identity,
                "goals_referenced": len(context.goals),
                "memories_used": len(memories.memories),
                "patterns_referenced": len(context.patterns)
            }
        )
```

**Why This Works (Psychology):**
1. **Self-Determination Theory**: Identity-aligned goals have higher completion rates
2. **Temporal Self**: Connecting with future self increases motivation
3. **Personalization**: Referencing specific data creates trust
4. **Accountability**: "Future you" creates internal motivation vs external pressure

---

## 4. Pattern Detection Engine

### Automatic Behavioral Insights

**Why Automatic vs. Manual Tracking:**
- Users won't log metrics manually (friction)
- Patterns emerge naturally from existing data
- Surprises are more impactful ("Did you know you're 2x productive on weekdays?")

**Implementation:**
```python
class PatternDetector:
    async def detect_all_patterns(self, user_id: str, days: int = 30) -> list[Pattern]:
        patterns = []

        # 1. PRODUCTIVITY PATTERNS
        task_stats = await self.task_repo.get_completion_stats(user_id, days)
        completion_rate = task_stats["completed"] / max(task_stats["total"], 1)

        if completion_rate >= 0.8:
            patterns.append(Pattern(
                type=PatternType.STRENGTH,
                name="High Task Completion",
                description=f"You complete {int(completion_rate*100)}% of your tasks - you're a finisher!",
                confidence=0.85,
                evidence={"completion_rate": completion_rate, "total_tasks": task_stats["total"]},
                suggested_action="Consider taking on more ambitious goals"
            ))
        elif completion_rate < 0.4:
            patterns.append(Pattern(
                type=PatternType.BLOCKER,
                name="Task Completion Challenge",
                description=f"Only {int(completion_rate*100)}% of tasks completed. Let's explore what's blocking you.",
                confidence=0.8,
                suggested_action="Try breaking tasks into smaller steps"
            ))

        # 2. EMOTIONAL PATTERNS
        mood_stats = await self.journal_repo.get_mood_stats(user_id, days)
        positive_moods = ["happy", "excited", "grateful", "focused", "peaceful"]
        positive_count = sum(mood_stats.get(m, 0) for m in positive_moods)
        total_entries = sum(mood_stats.values())

        if total_entries > 0:
            positive_rate = positive_count / total_entries
            if positive_rate >= 0.6:
                patterns.append(Pattern(
                    type=PatternType.STRENGTH,
                    name="Positive Outlook",
                    description=f"{int(positive_rate*100)}% of your journal entries show positive emotions",
                    confidence=0.8
                ))

        # 3. TIME MANAGEMENT PATTERNS
        weekday_stats = await self.task_repo.get_weekday_stats(user_id, days)
        weekday_rate = weekday_stats.get("weekday_completion", 0)
        weekend_rate = weekday_stats.get("weekend_completion", 0)

        if weekday_rate > weekend_rate * 1.5:
            patterns.append(Pattern(
                type=PatternType.PRODUCTIVITY,
                name="Weekday Performer",
                description="You're significantly more productive on weekdays. Consider protecting weekends for rest.",
                confidence=0.75,
                suggested_action="Schedule deep work for weekdays, keep weekends light"
            ))

        # 4. GOAL PROGRESS PATTERNS
        goal_stats = await self.goal_repo.get_progress_stats(user_id)
        avg_progress = goal_stats.get("average_progress", 0)

        if avg_progress >= 70:
            patterns.append(Pattern(
                type=PatternType.GOAL_PROGRESS,
                name="Goal Achiever",
                description=f"Your goals are {int(avg_progress)}% complete on average - you follow through!",
                confidence=0.85
            ))

        # Store high-confidence patterns
        for pattern in patterns:
            if pattern.confidence >= 0.6:
                await self.pattern_repo.upsert(user_id, pattern)

        return patterns
```

**Confidence Thresholds:**
- 0.6+ : Store and reference in conversations
- 0.8+ : Proactively surface to user
- 0.9+ : Include in weekly summary

---

## 5. Database Schema

### Core Models

```python
# User - Core identity
class User(Base):
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    name = Column(String(100))
    timezone = Column(String(50), default="Asia/Kolkata")
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

# Identity - Who user wants to become
class Identity(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    ideal_self = Column(String(255))       # "CEO", "Musician", "Entrepreneur"
    description = Column(Text)              # Detailed description
    why = Column(Text)                      # Deeper motivation
    role_models = Column(JSON)              # Inspiring figures
    attributes = Column(JSON)               # Key traits to develop
    target_timeline = Column(String(100))   # "3 years", "5 years"

# Goal - OKR-style goals linked to identity
class Goal(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    identity_id = Column(String(36), ForeignKey("identities.id"))
    title = Column(String(255))
    description = Column(Text)
    why = Column(Text)                      # Links to identity
    category = Column(String(50))           # career, health, skill, financial, personal
    timeframe = Column(String(20))          # quarterly, monthly, weekly
    status = Column(String(20))             # active, completed, paused
    progress_percent = Column(Integer, default=0)

# Task - Daily execution linked to goals
class Task(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    goal_id = Column(String(36), ForeignKey("goals.id"))
    title = Column(String(255))
    scheduled_date = Column(Date, index=True)
    time_block = Column(String(20))         # morning, afternoon, evening
    status = Column(String(20))             # pending, completed, skipped
    outcome_notes = Column(Text)            # Reflection after completion
    contribution_to_goal = Column(Text)     # How this helped

# Entry - Journal/mood tracking
class Entry(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    content = Column(Text)
    entry_type = Column(String(50))         # journal, reflection, learning
    mood = Column(String(50))               # happy, sad, stressed, etc.
    mood_intensity = Column(Integer)        # 1-5
    created_at = Column(DateTime, index=True)

# Embedding - Vector storage for RAG
class Embedding(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    source_type = Column(String(50))        # journal, goal, task, conversation
    source_id = Column(String(36))
    content_preview = Column(String(500))
    embedding = Column(Vector(1536))        # pgvector
    metadata_ = Column(JSON)
    created_at = Column(DateTime)

# Pattern - Detected behavioral patterns
class Pattern(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    pattern_type = Column(String(50))
    pattern_name = Column(String(255))
    description = Column(Text)
    evidence = Column(JSON)
    confidence = Column(Float)
    suggested_action = Column(Text)
    detected_at = Column(DateTime)

# Conversation + Message - Chat history
class Conversation(Base):
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), index=True)
    title = Column(String(255))
    created_at = Column(DateTime)

class Message(Base):
    id = Column(String(36), primary_key=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"))
    role = Column(String(20))               # user, assistant
    content = Column(Text)
    intent = Column(String(50))             # Classified intent
    created_at = Column(DateTime)
```

### Relationship Diagram

```
┌──────────┐     ┌───────────┐     ┌────────┐
│   User   │────▶│  Identity │◀────│  Goal  │
└──────────┘     └───────────┘     └────────┘
     │                                  │
     │                                  ▼
     │           ┌───────────┐     ┌────────┐
     ├──────────▶│   Entry   │     │  Task  │
     │           └───────────┘     └────────┘
     │                │                 │
     │                ▼                 ▼
     │           ┌─────────────────────────┐
     ├──────────▶│       Embedding         │
     │           └─────────────────────────┘
     │
     │           ┌───────────┐
     ├──────────▶│  Pattern  │
     │           └───────────┘
     │
     │           ┌───────────────┐     ┌─────────┐
     └──────────▶│ Conversation  │────▶│ Message │
                 └───────────────┘     └─────────┘
```

---

## 6. API Design

### Core Endpoints

```
BASE: /api/v1

# Authentication
POST   /auth/signup              # Create account
POST   /auth/login               # Login → JWT token

# Chat (Core Experience)
POST   /chat                     # Send message → mentor response
GET    /chat/conversations       # List conversations
GET    /chat/conversation/{id}   # Get conversation history

# Planning
GET    /planning/today           # Get today's plan
POST   /planning/today           # Generate daily plan
GET    /planning/tasks           # List tasks (filterable)

# Tasks
POST   /tasks                    # Create task
PATCH  /tasks/{id}               # Update task
POST   /tasks/{id}/complete      # Complete with reflection
DELETE /tasks/{id}               # Delete task

# Goals
GET    /goals                    # List active goals
POST   /goals                    # Create goal
PATCH  /goals/{id}               # Update goal/progress

# Journal
GET    /entries                  # List entries
POST   /entries                  # Create entry with mood

# Identity
GET    /identity                 # Get current identity
POST   /identity                 # Create/update identity

# Insights
GET    /insights/weekly          # Weekly summary
POST   /insights/patterns        # Trigger pattern detection
GET    /insights/quick           # Quick stats
```

### Chat Endpoint Detail

```python
@router.post("/chat")
async def send_message(
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
) -> ChatResponse:
    """
    Main chat endpoint - routes through orchestrator.

    Flow:
    1. Safety check
    2. Emotion detection
    3. Intent classification
    4. Route to agent
    5. Apply persona
    6. Store in memory
    7. Return response
    """
    response = await orchestrator.process(
        user_id=user_id,
        message=request.message,
        conversation_id=request.conversation_id
    )

    return ChatResponse(
        message=response.content,
        conversation_id=response.conversation_id,
        intent=response.intent,
        emotion_detected=response.emotion,
        context_used=response.context_metadata
    )
```

---

## 7. Security & Privacy

### Authentication Flow

```
Client → Clerk SDK → JWT Token → Backend → Verify JWKS → User Record
```

### Data Privacy Principles

1. **User Data Isolation**
   ```python
   # Every query filtered by user_id
   async def get_goals(user_id: str):
       return await db.execute(
           select(Goal).where(Goal.user_id == user_id)
       )
   ```

2. **No Data in LLM Training**
   - Embeddings stored in our PostgreSQL
   - Only query + context sent to LLM (not stored by provider)
   - User can delete all data (GDPR compliance ready)

3. **Sensitive Data Handling**
   ```python
   # Journal entries encrypted at rest (future)
   # Mood data aggregated for patterns, not exposed raw
   ```

### API Security

```python
# Rate limiting per user
@limiter.limit("100/minute")
async def chat_endpoint():
    ...

# Input validation (Pydantic)
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[UUID] = None

# SQL injection prevention (SQLAlchemy ORM)
# All queries parameterized automatically
```

---

## 8. Cost Optimization Strategy

### Token Usage by Feature

| Feature | Tokens/Request | Requests/User/Day | Model | Cost |
|---------|----------------|-------------------|-------|------|
| Chat | 2,000 | 20 | Groq | $0.02 |
| Planning | 3,000 | 1 | Groq | $0.002 |
| Emotion | 500 | 20 | Groq (8B) | $0.001 |
| Insights | 2,000 | 2 | Groq | $0.002 |
| Persona (complex) | 3,000 | 5 | Claude | $0.045 |

**Daily Cost per Active User: ~$0.07**
**Monthly Cost at 10K DAU: ~$21,000**

### Optimization Techniques

1. **Model Selection by Task**
   - Classification: Groq 8B (cheapest, fastest)
   - Generation: Groq 70B (good quality, low cost)
   - Complex reasoning: Claude (only when needed)

2. **Caching**
   ```python
   # Cache pattern detection results (24 hours)
   @cache(ttl=86400)
   async def get_user_patterns(user_id: str):
       return await pattern_detector.detect_all(user_id)
   ```

3. **Batching Embeddings**
   ```python
   # Batch multiple texts in one API call
   async def embed_batch(texts: list[str]) -> list[list[float]]:
       return await openai.embeddings.create(
           input=texts,  # Up to 100 texts
           model="text-embedding-3-small"
       )
   ```

---

## 9. Interview Discussion Points

### "Why multi-agent over single LLM?"

1. **Cost efficiency**: Route simple tasks to cheap models
2. **Reliability**: Specialized prompts for each task
3. **Testability**: Test each agent independently
4. **Safety**: Dedicated safety agent catches issues first
5. **Maintainability**: Update one agent without affecting others

### "How does the future self persona work?"

1. User defines ideal identity ("CEO in 3 years")
2. System stores why, attributes, role models
3. Every LLM call includes persona: "You are the future version..."
4. References specific goals, patterns, wins
5. Creates emotional connection vs generic advice

### "Why Groq over just using Claude?"

1. **Cost**: 5-20x cheaper for same quality on routine tasks
2. **Latency**: Groq has fastest inference
3. **Availability**: Fallback chain prevents outages
4. **Quality**: Reserve Claude for complex reasoning only

### "How do you handle hallucinations?"

1. **RAG grounding**: Always retrieve relevant context first
2. **Safety agent**: Catches harmful content
3. **Scope boundaries**: Refuse health/finance/legal advice
4. **Confidence signals**: Pattern detection has thresholds
5. **Source attribution**: Show what memories were used

### "What would you do differently?"

1. **Start with tests**: Limited test coverage currently
2. **Streaming responses**: Users expect real-time tokens
3. **Better embeddings**: Fine-tune on personal journal data
4. **Proactive nudges**: Schedule push notifications

---

## 10. Summary

Gen-Friend v3 demonstrates production-grade AI application architecture:

**Multi-Agent System (7 agents)**
- Safety, Emotion, Memory, Planner, Insight, Academy, Orchestrator
- Each optimized for its task with appropriate model selection

**Personal RAG**
- Hybrid retrieval (vector + BM25)
- Sources: journals, goals, tasks, conversations, patterns
- Enables "I remember when you..." personalization

**Future Self Persona**
- User defines ideal identity
- AI speaks as that future version
- Creates emotional motivation vs generic advice

**Cost-Optimized Intelligence**
- Groq (80% of requests) + Claude (complex reasoning)
- ~$0.07/user/day at scale
- Three-provider fallback chain

**Pattern Detection**
- Automatic behavioral insights
- Productivity, emotional, goal progress patterns
- Confidence thresholds for reliability

**Technology Choices**
- FastAPI (async I/O for LLM concurrency)
- PostgreSQL + pgvector (single DB for relational + vectors)
- Next.js PWA (mobile-first, installable)
- Clerk (managed auth)

---

*Word Count: ~5,500 words*
*Last Updated: January 2026*
