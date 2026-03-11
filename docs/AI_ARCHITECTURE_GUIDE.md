# Gen-Friend V3: AI Architecture Guide
## For AI Architects & Technical Leads

**Document Version:** 1.0
**Last Updated:** December 2024
**Author:** AI Architecture Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [AI Technology Stack](#3-ai-technology-stack)
4. [LLM Integration Architecture](#4-llm-integration-architecture)
5. [RAG (Retrieval-Augmented Generation)](#5-rag-retrieval-augmented-generation)
6. [Agentic AI Architecture](#6-agentic-ai-architecture)
7. [Voice AI Pipeline](#7-voice-ai-pipeline)
8. [Mentor System (Personalization Engine)](#8-mentor-system-personalization-engine)
9. [Context Management Strategy](#9-context-management-strategy)
10. [Data Flow & Program Flow](#10-data-flow--program-flow)
11. [Database Architecture](#11-database-architecture)
12. [Cost Optimization Strategies](#12-cost-optimization-strategies)
13. [Security & Safety Architecture](#13-security--safety-architecture)
14. [Deployment Architecture](#14-deployment-architecture)
15. [Interview Discussion Points](#15-interview-discussion-points)

---

## 1. Executive Summary

### What is Gen-Friend?

Gen-Friend is an **AI-powered productivity companion** designed as the "opposite of Instagram" - instead of consuming attention, it builds users toward their ideal selves through personalized coaching, goal tracking, and behavioral pattern detection.

### Key AI Innovations

| Innovation | Description |
|------------|-------------|
| **Multi-Agent Orchestration** | 6 specialized AI agents coordinated by a central orchestrator |
| **Hybrid RAG** | Vector + BM25 retrieval with Reciprocal Rank Fusion |
| **Identity-Driven Personalization** | "Future Self" persona that coaches users toward their goals |
| **Proactive AI** | Scheduled check-ins and pattern-based interventions |
| **Voice-First Interface** | Whisper STT + GPT TTS for conversational interaction |

### Architecture Principles

1. **Safety First** - Crisis detection before any response
2. **Emotion-Aware** - Adapt tone based on user's emotional state
3. **Cost-Efficient** - Route to appropriate model based on task complexity
4. **Context-Rich** - Maintain conversation, identity, goals, and patterns
5. **Actionable** - Every response drives toward specific user actions

---

## 2. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Next.js   │  │   Voice     │  │   Mobile    │  │  WhatsApp   │        │
│  │   Web App   │  │   Input     │  │    PWA      │  │    Bot      │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER (FastAPI)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Auth     │  │    Chat     │  │   Audio     │  │   Goals     │        │
│  │   Router    │  │   Router    │  │   Router    │  │   Router    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    CONVERSATION ORCHESTRATOR                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │   │
│  │  │  Safety  │→ │ Emotion  │→ │  Intent  │→ │  Agent   │             │   │
│  │  │  Check   │  │ Detect   │  │ Classify │  │  Route   │             │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌─────────┬─────────┬─────────┬──┴──────┬─────────┬─────────┐             │
│  ▼         ▼         ▼         ▼         ▼         ▼         ▼             │
│ ┌───┐    ┌───┐    ┌───┐    ┌───┐    ┌───┐    ┌───┐    ┌───┐               │
│ │SAF│    │EMO│    │MEM│    │PLN│    │INS│    │ACA│    │CHT│               │
│ │ETY│    │TIO│    │ORY│    │NER│    │GHT│    │DMY│    │   │               │
│ └───┘    └───┘    └───┘    └───┘    └───┘    └───┘    └───┘               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI SERVICES LAYER                               │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   LLM ROUTER    │  │   RAG PIPELINE  │  │  MENTOR ENGINE  │             │
│  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐  │             │
│  │  │  Claude   │  │  │  │  Vector   │  │  │  │ Identity  │  │             │
│  │  │  Sonnet   │  │  │  │  Search   │  │  │  │  Builder  │  │             │
│  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │             │
│  │  │  Claude   │  │  │  │   BM25    │  │  │  │   Goal    │  │             │
│  │  │  Haiku    │  │  │  │  Search   │  │  │  │   Coach   │  │             │
│  │  ├───────────┤  │  │  ├───────────┤  │  │  ├───────────┤  │             │
│  │  │  GPT-4o   │  │  │  │   RRF     │  │  │  │  Pattern  │  │             │
│  │  │ (fallback)│  │  │  │  Fusion   │  │  │  │ Detector  │  │             │
│  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ PostgreSQL  │  │   Redis     │  │   Vector    │  │  Knowledge  │        │
│  │  (Primary)  │  │  (Cache)    │  │   Store     │  │    Base     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. AI Technology Stack

### Core Technologies

| Category | Technology | Purpose | Why Chosen |
|----------|------------|---------|------------|
| **Primary LLM** | Claude Sonnet 4 | Generation, Reasoning | Best balance of quality, speed, cost |
| **Fast LLM** | Claude Haiku 3.5 | Classification, Quick Tasks | 10x faster, 12x cheaper than Sonnet |
| **Fallback LLM** | GPT-4o | Reliability | Redundancy if Anthropic is down |
| **STT** | OpenAI Whisper | Speech-to-Text | Best accuracy across accents |
| **TTS** | OpenAI TTS | Text-to-Speech | Natural voice quality |
| **Embeddings** | text-embedding-3-small | Vector Search | Cost-effective, 1536 dimensions |
| **Framework** | FastAPI | API Server | Async support, auto-docs |
| **Database** | PostgreSQL + SQLAlchemy | Persistence | Robust, async ORM |

### Model Selection Matrix

```
┌────────────────────┬─────────────────┬──────────────┬───────────────┐
│      Task Type     │     Model       │  Latency     │   Cost/1M     │
├────────────────────┼─────────────────┼──────────────┼───────────────┤
│ Classification     │ Claude Haiku    │   ~200ms     │    $1.50      │
│ Intent Detection   │ Claude Haiku    │   ~200ms     │    $1.50      │
│ Emotion Detection  │ Claude Haiku    │   ~200ms     │    $1.50      │
│ Safety Check       │ Claude Haiku    │   ~200ms     │    $1.50      │
├────────────────────┼─────────────────┼──────────────┼───────────────┤
│ Content Generation │ Claude Sonnet   │   ~1-2s      │   $18.00      │
│ Complex Reasoning  │ Claude Sonnet   │   ~2-3s      │   $18.00      │
│ Coaching Responses │ Claude Sonnet   │   ~1-2s      │   $18.00      │
│ Pattern Analysis   │ Claude Sonnet   │   ~2-3s      │   $18.00      │
├────────────────────┼─────────────────┼──────────────┼───────────────┤
│ Embeddings         │ text-embed-3-sm │   ~100ms     │    $0.02      │
│ Speech-to-Text     │ Whisper         │   ~1-3s      │  $0.006/min   │
│ Text-to-Speech     │ TTS-1           │   ~500ms     │   $15/1M chr  │
└────────────────────┴─────────────────┴──────────────┴───────────────┘
```

---

## 4. LLM Integration Architecture

### Provider Pattern

**Why Use Provider Pattern?**
- **Vendor Independence**: Switch between Claude, GPT, or local models
- **Fallback Support**: Automatic failover if primary provider is down
- **Cost Optimization**: Route to cheaper models for simple tasks
- **A/B Testing**: Compare model performance easily

```python
# Architecture: Abstract Base + Concrete Providers

class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers"""

    @abstractmethod
    async def generate(self, messages, **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    async def stream(self, messages, **kwargs) -> AsyncGenerator:
        pass

class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude implementation"""
    def __init__(self):
        self.client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self.default_model = "claude-sonnet-4-20250514"

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT implementation"""
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.default_model = "gpt-4o"
```

### LLM Router (Task-Based Model Selection)

**Why Use Task-Based Routing?**
- **Cost Efficiency**: Save 90%+ on classification tasks using Haiku
- **Latency Optimization**: Faster models for real-time features
- **Quality Assurance**: Best models for user-facing content

```python
class TaskType(Enum):
    CLASSIFICATION = "classification"      # → Haiku (fast, cheap)
    GENERATION = "generation"              # → Sonnet (quality)
    COMPLEX_REASONING = "complex_reasoning" # → Sonnet (best)

class LLMRouter:
    """Intelligent model selection based on task type"""

    MODEL_MAPPING = {
        TaskType.CLASSIFICATION: "claude-3-5-haiku-20241022",
        TaskType.GENERATION: "claude-sonnet-4-20250514",
        TaskType.COMPLEX_REASONING: "claude-sonnet-4-20250514",
    }

    async def generate(self, prompt, task_type, user_id):
        model = self.MODEL_MAPPING[task_type]

        try:
            response = await self.claude.generate(prompt, model=model)
            await self._track_cost(user_id, model, response.tokens)
            return response
        except Exception:
            # Fallback to OpenAI
            return await self.openai.generate(prompt)
```

### Cost Tracking

```python
PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
    "gpt-4o": {"input": 2.5, "output": 10.0},
}

async def _track_cost(user_id, model, input_tokens, output_tokens):
    cost = (input_tokens * PRICING[model]["input"] +
            output_tokens * PRICING[model]["output"]) / 1_000_000
    await db.insert(CostLog(user_id=user_id, model=model, cost=cost))
```

---

## 5. RAG (Retrieval-Augmented Generation)

### What is RAG?

**RAG** combines retrieval systems with LLMs to provide contextually relevant, grounded responses based on user-specific or domain-specific data.

### Why RAG for Gen-Friend?

| Challenge | RAG Solution |
|-----------|--------------|
| LLM has no memory of past conversations | Retrieve relevant past entries |
| Generic advice isn't helpful | Ground responses in user's actual goals/wins |
| Hallucination risk | Provide evidence from user's own data |
| Context window limits | Selective retrieval of most relevant info |

### Hybrid RAG Architecture

**Why Hybrid (Vector + BM25)?**

| Method | Strengths | Weaknesses |
|--------|-----------|------------|
| **Vector Search** | Semantic understanding, finds related concepts | Misses exact keyword matches |
| **BM25 (Keyword)** | Exact matching, specific terms | No semantic understanding |
| **Hybrid + RRF** | Best of both worlds | Slightly more complex |

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG PIPELINE                                 │
│                                                                  │
│  User Query: "How am I doing on my fitness goal?"               │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   QUERY PROCESSING                        │   │
│  │   1. Generate embedding for query                         │   │
│  │   2. Extract keywords for BM25                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                       │
│            ┌─────────────┴─────────────┐                        │
│            ▼                           ▼                        │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │   VECTOR SEARCH     │    │    BM25 SEARCH      │            │
│  │                     │    │                     │            │
│  │ • Semantic matching │    │ • Keyword matching  │            │
│  │ • Cosine similarity │    │ • TF-IDF scoring    │            │
│  │ • Top 20 results    │    │ • Top 20 results    │            │
│  └──────────┬──────────┘    └──────────┬──────────┘            │
│             │                          │                        │
│             └────────────┬─────────────┘                        │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              RECIPROCAL RANK FUSION (RRF)                 │   │
│  │                                                           │   │
│  │   Score = Σ (1 / (k + rank_i + 1))   where k = 60        │   │
│  │                                                           │   │
│  │   • Combines rankings from both methods                   │   │
│  │   • Balances semantic and keyword relevance               │   │
│  │   • Returns Top 10 fused results                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 CONTEXT BUILDER                           │   │
│  │                                                           │   │
│  │   • Token budget: 4000 tokens max                         │   │
│  │   • Format: [SOURCE_TYPE] DATE\n Content                  │   │
│  │   • Priority: Higher RRF scores first                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  LLM GENERATION                           │   │
│  │                                                           │   │
│  │   System: "Answer based on user's data below..."          │   │
│  │   Context: [Retrieved entries, goals, wins]               │   │
│  │   Query: "How am I doing on my fitness goal?"             │   │
│  │                                                           │   │
│  │   → "You've logged 3 gym visits this week, up from 1      │   │
│  │      last week! Your goal was 4x/week. You're at 75%."    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### RRF (Reciprocal Rank Fusion) Explained

**Why RRF?**
- Simple yet effective fusion algorithm
- No need to normalize scores between methods
- Proven in information retrieval research

```python
def reciprocal_rank_fusion(vector_results, bm25_results, k=60):
    """
    Combine results from multiple retrieval methods.

    Formula: score(doc) = Σ (1 / (k + rank_i + 1))

    k=60 is the standard value from the original RRF paper.
    Higher k reduces the influence of high-ranked documents.
    """
    scores = defaultdict(float)

    for rank, doc in enumerate(vector_results):
        scores[doc.id] += 1 / (k + rank + 1)

    for rank, doc in enumerate(bm25_results):
        scores[doc.id] += 1 / (k + rank + 1)

    # Sort by combined score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

### Data Sources for RAG

| Source | Content | Use Case |
|--------|---------|----------|
| **Journal Entries** | Wins, moments, reflections | Recall past achievements |
| **Goals** | OKRs with key results | Track progress |
| **Tasks** | Daily tasks with outcomes | Behavioral patterns |
| **Conversations** | Past chat history | Contextual continuity |
| **Knowledge Base** | Domain expertise (CEO, Entrepreneur) | Role-specific advice |

---

## 6. Agentic AI Architecture

### What is Agentic AI?

**Agentic AI** refers to AI systems that can:
1. **Understand** - Interpret user intent and context
2. **Plan** - Break down complex tasks
3. **Execute** - Take actions or call other systems
4. **Reflect** - Evaluate results and adjust

### Why Multi-Agent Architecture?

| Approach | Pros | Cons |
|----------|------|------|
| **Single Monolithic Agent** | Simple | Hard to maintain, slow |
| **Multi-Agent Orchestration** | Specialized, parallel, modular | More complex routing |

Gen-Friend uses **Multi-Agent Orchestration** because:
- Different tasks need different expertise
- Parallel processing improves latency
- Easier to test and improve individual agents
- Clear separation of concerns

### Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONVERSATION ORCHESTRATOR                             │
│                                                                              │
│  User Message: "I'm feeling overwhelmed with my startup"                    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 1: SAFETY CHECK                                                   │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │  SafetyAgent.check()                                             │   │ │
│  │  │  • Scan for crisis keywords (suicide, self-harm)                 │   │ │
│  │  │  • If detected → Return helpline resources immediately           │   │ │
│  │  │  • Result: concern_level=0, is_safe=True                         │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 2: EMOTION DETECTION                                              │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │  EmotionAgent.detect()                                           │   │ │
│  │  │  • Analyze message + recent history                              │   │ │
│  │  │  • Result: emotion="overwhelmed", intensity=4/5                  │   │ │
│  │  │  • Tone guidance: "calm, supportive, shorter responses"          │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 3: INTENT CLASSIFICATION                                          │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │  IntentClassifier.classify()                                     │   │ │
│  │  │  • Intents: planning, memory, insight, academy, chat, goal...    │   │ │
│  │  │  • Result: intent="insight" (user needs pattern analysis)        │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 4: AGENT ROUTING                                                  │ │
│  │                                                                          │ │
│  │    intent="planning"  → PlannerAgent                                    │ │
│  │    intent="memory"    → MemoryAgent (RAG)                               │ │
│  │    intent="insight"   → InsightAgent  ← SELECTED                        │ │
│  │    intent="academy"   → AcademyAgent                                    │ │
│  │    intent="chat"      → MentorEngine (general)                          │ │
│  │                                                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 5: AGENT EXECUTION                                                │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │  InsightAgent.process()                                          │   │ │
│  │  │  • Load user's goals, tasks, patterns                            │   │ │
│  │  │  • Detect: "3 tasks rescheduled 4+ times = avoidance pattern"    │   │ │
│  │  │  • Generate insight with suggested action                        │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  STEP 6: PERSONA APPLICATION                                            │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │  MentorEngine.apply_persona()                                    │   │ │
│  │  │  • Wrap response in "future self" voice                          │   │ │
│  │  │  • Apply emotional tone guidance (calm, supportive)              │   │ │
│  │  │  • Add specific actions based on user's goals                    │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Final Response:                                                             │
│  "I hear you. Running a startup is intense. Looking at your patterns,       │
│   I notice you've rescheduled 'investor outreach' 4 times this week.        │
│   That avoidance might be fear of rejection - totally normal.               │
│   The CEO-you handles this by doing the scary thing FIRST each day.         │
│   Tomorrow, make one investor email your very first task. Just one."        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Six Agents

#### 1. Safety Agent
**Purpose**: Protect users in crisis

```python
class SafetyAgent(BaseAgent):
    """First line of defense for user safety"""

    CRISIS_KEYWORDS = [
        "suicide", "kill myself", "end my life", "self-harm",
        "don't want to live", "better off dead"
    ]

    HELPLINES = {
        "IN": "iCall: 9152987821",
        "US": "988 Suicide & Crisis Lifeline"
    }

    async def check(self, message: str) -> SafetyCheck:
        # Quick keyword scan first (fast)
        if any(kw in message.lower() for kw in self.CRISIS_KEYWORDS):
            return SafetyCheck(is_safe=False, intervention=self.HELPLINES)

        # LLM classification for subtle cases (thorough)
        concern_level = await self._classify_concern(message)
        return SafetyCheck(
            is_safe=concern_level < 0.7,
            concern_level=concern_level
        )
```

#### 2. Emotion Agent
**Purpose**: Adapt response tone to user's emotional state

```python
class EmotionAgent(BaseAgent):
    """Detect and respond to emotional states"""

    EMOTIONS = ["positive", "neutral", "stressed", "overwhelmed",
                "sad", "excited", "anxious", "frustrated"]

    TONE_GUIDANCE = {
        "stressed": "calm, supportive, shorter responses",
        "sad": "warm, empathetic, gentle encouragement",
        "frustrated": "understanding, solution-focused",
        "excited": "energetic, encouraging, match their energy"
    }

    async def detect(self, message: str, history: list) -> EmotionalState:
        result = await self.llm.generate(
            prompt=f"Classify emotion: {message}\nHistory: {history[-3:]}",
            task_type=TaskType.CLASSIFICATION  # Uses Haiku (fast)
        )
        return EmotionalState(
            primary=result.emotion,
            intensity=result.intensity,
            tone_guidance=self.TONE_GUIDANCE.get(result.emotion)
        )
```

#### 3. Memory Agent (RAG)
**Purpose**: Retrieve relevant personal history

```python
class MemoryAgent(BaseAgent):
    """Personal RAG for user's history"""

    async def retrieve_and_reflect(self, query: str, user_id: str):
        # Hybrid retrieval
        results = await self.rag_pipeline.query(
            query=query,
            user_id=user_id,
            sources=["entries", "goals", "tasks"]
        )

        # Generate reflection based on memories
        return await self.llm.generate(
            prompt=f"""Based on the user's memories:
            {results.context}

            Reflect on: {query}
            Reference specific memories to make it personal."""
        )
```

#### 4. Planner Agent
**Purpose**: Generate actionable daily/weekly plans

```python
class PlannerAgent(BaseAgent):
    """AI-powered planning assistant"""

    async def generate_daily_plan(self, user_id: str, goals: list):
        # Consider energy patterns
        plan = await self.llm.generate(
            prompt=f"""Create a daily plan for user with goals: {goals}

            Rules:
            - Morning: Most important/focused work
            - Afternoon: Collaborative tasks
            - Evening: Light tasks, reflection
            - Include breaks
            - Max 5 tasks

            Format: time_block|priority|title"""
        )
        return self._parse_plan(plan)
```

#### 5. Insight Agent
**Purpose**: Detect patterns and provide actionable insights

```python
class InsightAgent(BaseAgent):
    """Pattern detection and behavioral insights"""

    class InsightType(Enum):
        PRODUCTIVITY = "productivity"
        EMOTIONAL_TREND = "emotional_trend"
        GOAL_PROGRESS = "goal_progress"
        BLOCKERS = "blockers"

    async def analyze(self, user_id: str) -> list[Insight]:
        data = await self._gather_data(user_id)  # 90 days

        insights = []

        # Detect avoidance patterns
        rescheduled = [t for t in data.tasks if t.reschedule_count >= 3]
        if rescheduled:
            insights.append(Insight(
                type=InsightType.BLOCKERS,
                finding=f"Tasks avoided: {[t.title for t in rescheduled]}",
                action="Do the scariest task first tomorrow"
            ))

        return insights
```

#### 6. Academy Agent
**Purpose**: Teach AI concepts to users

```python
class AcademyAgent(BaseAgent):
    """AI education for students"""

    TOPICS = ["RAG", "agents", "embeddings", "LLM", "prompting",
              "memory", "fine-tuning"]

    async def explain(self, topic: str) -> str:
        return await self.llm.generate(
            prompt=f"""Explain {topic} to a college student in India.

            Rules:
            - Use simple analogies (relate to daily life)
            - Give one practical example
            - Max 150 words
            - End with an engaging question"""
        )
```

---

## 7. Voice AI Pipeline

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VOICE AI PIPELINE                                   │
│                                                                              │
│  ┌─────────────────┐                                                        │
│  │   User speaks   │                                                        │
│  │   into device   │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FRONTEND (Browser)                                                  │   │
│  │                                                                       │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │   │
│  │  │ MediaStream │ →  │   Audio     │ →  │   WebM/     │              │   │
│  │  │    API      │    │  Recorder   │    │   Opus      │              │   │
│  │  └─────────────┘    └─────────────┘    └─────────────┘              │   │
│  │                                                                       │   │
│  │  Two Modes:                                                           │   │
│  │  • Push-to-Talk: Tap to start, tap to stop                           │   │
│  │  • Continuous: VAD (Voice Activity Detection) auto-segments          │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │                                                                  │
│           │ FormData: audio blob + settings                                 │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  BACKEND API                                                          │   │
│  │                                                                       │   │
│  │  POST /audio/voice-chat-with-audio                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐     │   │
│  │  │                                                              │     │   │
│  │  │  1. TRANSCRIPTION (OpenAI Whisper)                          │     │   │
│  │  │     • Model: whisper-1                                       │     │   │
│  │  │     • Supports: webm, ogg, mp3, wav, m4a                    │     │   │
│  │  │     • Max size: 25MB                                         │     │   │
│  │  │     → Output: "I'm feeling overwhelmed with work"           │     │   │
│  │  │                                                              │     │   │
│  │  │  2. AI RESPONSE (Claude/Orchestrator)                       │     │   │
│  │  │     • Process through agent pipeline                         │     │   │
│  │  │     • Voice-optimized: SHORT responses (1-2 sentences)      │     │   │
│  │  │     • Conversational tone, no bullet lists                  │     │   │
│  │  │     → Output: "That's tough. What's the one thing..."       │     │   │
│  │  │                                                              │     │   │
│  │  │  3. SYNTHESIS (OpenAI TTS)                                  │     │   │
│  │  │     • Model: tts-1                                           │     │   │
│  │  │     • Voice: alloy (configurable)                           │     │   │
│  │  │     • Format: MP3 (base64 encoded)                          │     │   │
│  │  │     → Output: Base64 audio string                           │     │   │
│  │  │                                                              │     │   │
│  │  └─────────────────────────────────────────────────────────────┘     │   │
│  │                                                                       │   │
│  │  Response: {transcript, reply_text, audio, audio_format}             │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FRONTEND (Playback)                                                 │   │
│  │                                                                       │   │
│  │  • Decode base64 audio                                               │   │
│  │  • Play via Audio API                                                │   │
│  │  • Update chat UI with transcript + response                         │   │
│  │  • Allow interruption (tap while speaking)                           │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Voice Activity Detection (VAD)

```javascript
// Frontend VAD for Continuous Mode
function useVAD({ silenceThreshold = -45, silenceDuration = 1500 }) {
    // Analyze audio in real-time
    const checkAudio = () => {
        analyser.getByteFrequencyData(dataArray);

        // Calculate RMS (Root Mean Square) for volume
        const rms = Math.sqrt(sum / dataArray.length);
        const db = 20 * Math.log10(rms / 255);

        // If below threshold for silenceDuration → end of speech
        if (db < silenceThreshold) {
            startSilenceTimer();
        } else {
            clearSilenceTimer();
        }
    };
}
```

### Voice Prompt Optimization

```python
VOICE_SYSTEM_PROMPT = """You are Gen-Friend, a warm AI productivity companion.

VOICE INTERACTION RULES:
- Keep answers SHORT (1-2 sentences max)
- Sound friendly, direct, and natural
- Avoid bullet lists - speak conversationally
- If user needs detailed info, say "Would you like me to explain more?"
- Use simple language that sounds good when spoken aloud
- Be encouraging but concise
"""
```

---

## 8. Mentor System (Personalization Engine)

### The "Future Self" Concept

**Philosophy**: Instead of generic advice, Gen-Friend coaches users as their "future successful self" would - someone who has achieved their goals and is guiding them there.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MENTOR SYSTEM                                        │
│                                                                              │
│  User: "I want to become a successful CEO"                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      IDENTITY BUILDER                                   │ │
│  │                                                                          │ │
│  │  Extracts:                                                               │ │
│  │  • ideal_self: "CEO"                                                    │ │
│  │  • description: "Leading a tech company that makes impact"              │ │
│  │  • why: "To have autonomy and build something meaningful"               │ │
│  │  • role_models: ["Elon Musk", "Satya Nadella"]                         │ │
│  │  • attributes: ["decisive", "strategic", "resilient"]                  │ │
│  │  • target_timeline: "5 years"                                          │ │
│  │                                                                          │ │
│  │  Follow-up: "What specific aspect of being a CEO excites you most?"    │ │
│  │                                                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                        GOAL COACH                                       │ │
│  │                                                                          │ │
│  │  User: "I want to launch my product"                                    │ │
│  │                                                                          │ │
│  │  AI Response (OKR Format):                                              │ │
│  │  {                                                                       │ │
│  │    "title": "Launch MVP to first 100 users",                            │ │
│  │    "why": "This builds the decisive, action-taking CEO in you",         │ │
│  │    "category": "career",                                                │ │
│  │    "timeframe": "quarterly",                                            │ │
│  │    "suggested_key_results": [                                           │ │
│  │      {"title": "Ship v1.0", "target": 1, "unit": "release"},           │ │
│  │      {"title": "Onboard users", "target": 100, "unit": "users"},       │ │
│  │      {"title": "Gather feedback", "target": 20, "unit": "interviews"}  │ │
│  │    ]                                                                     │ │
│  │  }                                                                       │ │
│  │                                                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     PATTERN DETECTOR                                    │ │
│  │                                                                          │ │
│  │  Analyzes 90 days of:                                                   │ │
│  │  • Goals (completed vs abandoned)                                       │ │
│  │  • Tasks (completion rate, reschedule frequency)                        │ │
│  │  • Journal entries (mood, energy patterns)                              │ │
│  │                                                                          │ │
│  │  Detected Patterns:                                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │ │
│  │  │ AVOIDANCE PATTERN (confidence: 0.85)                             │   │ │
│  │  │ Evidence: "Investor outreach" rescheduled 6 times                │   │ │
│  │  │ Action: "Do the scary task first thing tomorrow"                 │   │ │
│  │  ├─────────────────────────────────────────────────────────────────┤   │ │
│  │  │ SUCCESS PATTERN (confidence: 0.72)                               │   │ │
│  │  │ Evidence: Tasks completed 3x more on days with morning exercise  │   │ │
│  │  │ Action: "Schedule exercise before work consistently"             │   │ │
│  │  └─────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      JOURNAL KEEPER                                     │ │
│  │                                                                          │ │
│  │  User logs win: "Got my first paying customer today!"                   │ │
│  │                                                                          │ │
│  │  AI Enrichment:                                                         │ │
│  │  "This shows you're developing the sales courage that defines great    │ │
│  │   CEOs. You put yourself out there even when it was uncomfortable.     │ │
│  │   CEO-you is proud of this moment."                                    │ │
│  │                                                                          │ │
│  │  Later, when struggling:                                                │ │
│  │  AI Recall: "Remember when you got your first paying customer? You     │ │
│  │   were terrified of rejection but did it anyway. That same courage     │ │
│  │   will help you with this investor pitch."                             │ │
│  │                                                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                      MENTOR ENGINE                                      │ │
│  │                                                                          │ │
│  │  Combines all context into "Future Self" persona:                       │ │
│  │                                                                          │ │
│  │  System Prompt:                                                         │ │
│  │  "You are the future version of this user who became a successful CEO. │ │
│  │   You know they have these attributes: decisive, strategic, resilient. │ │
│  │   They're working toward: Launch MVP to first 100 users.               │ │
│  │   You've noticed they tend to: avoid scary tasks like investor outreach│ │
│  │   Recent win: Got first paying customer.                               │ │
│  │                                                                          │ │
│  │   Speak as their future self giving warm, direct guidance."            │ │
│  │                                                                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Context Management Strategy

### The Challenge

LLMs have limited context windows and no persistent memory. How do we maintain continuity across:
- Multiple conversations
- Days/weeks/months of usage
- Different features (chat, goals, journal)

### Multi-Layer Context Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CONTEXT LAYERS                                          │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 1: IMMEDIATE CONTEXT (In-Memory)                                 │ │
│  │                                                                          │ │
│  │  • Current conversation history (last 10-20 messages)                   │ │
│  │  • Current emotional state                                              │ │
│  │  • Active intent/task                                                   │ │
│  │                                                                          │ │
│  │  Lifetime: Current session only                                         │ │
│  │  Size: ~2000 tokens                                                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 2: IDENTITY CONTEXT (Database)                                   │ │
│  │                                                                          │ │
│  │  • ideal_self, why, attributes (from Identity table)                   │ │
│  │  • Active goals and key results                                         │ │
│  │  • User preferences (timezone, communication style)                     │ │
│  │                                                                          │ │
│  │  Lifetime: Permanent (until updated)                                    │ │
│  │  Size: ~500 tokens                                                      │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 3: BEHAVIORAL CONTEXT (Database + Analytics)                     │ │
│  │                                                                          │ │
│  │  • Detected patterns (avoidance, success triggers)                      │ │
│  │  • Recent wins (last 5-10)                                              │ │
│  │  • Task completion rates                                                │ │
│  │  • Mood/energy trends                                                   │ │
│  │                                                                          │ │
│  │  Lifetime: Rolling 90 days                                              │ │
│  │  Size: ~1000 tokens (summarized)                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 4: RETRIEVED CONTEXT (RAG)                                       │ │
│  │                                                                          │ │
│  │  • Semantically relevant journal entries                                │ │
│  │  • Related past conversations                                           │ │
│  │  • Similar tasks/goals from history                                     │ │
│  │                                                                          │ │
│  │  Lifetime: Query-specific                                               │ │
│  │  Size: Up to 4000 tokens (budget)                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 5: KNOWLEDGE CONTEXT (Static Files)                              │ │
│  │                                                                          │ │
│  │  • Domain expertise (CEO skills, entrepreneur habits)                   │ │
│  │  • Best practices (goal-setting, productivity)                          │ │
│  │  • Decision frameworks                                                  │ │
│  │                                                                          │ │
│  │  Lifetime: Static (updated with app releases)                           │ │
│  │  Size: ~1000 tokens (selected based on user's ideal_self)              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Context Assembly for Each Request

```python
async def build_context(user_id: str, message: str) -> str:
    """Assemble all context layers for LLM request"""

    # Layer 1: Immediate (already in request)
    conversation_history = request.history[-10:]

    # Layer 2: Identity (always included)
    identity = await identity_builder.get_identity(user_id)
    goals = await goal_coach.get_active_goals(user_id)

    # Layer 3: Behavioral (summarized)
    patterns = await pattern_detector.get_patterns(user_id)
    recent_wins = await journal_keeper.get_recent_wins(user_id, limit=5)

    # Layer 4: Retrieved (query-specific)
    rag_results = await rag_pipeline.query(message, user_id)

    # Layer 5: Knowledge (based on ideal_self)
    domain_knowledge = await knowledge_loader.get_relevant(
        ideal_self=identity.ideal_self
    )

    # Assemble within token budget
    return f"""
    USER IDENTITY:
    {identity.ideal_self} - {identity.why}
    Attributes: {identity.attributes}

    ACTIVE GOALS:
    {[g.title for g in goals]}

    PATTERNS DETECTED:
    {[p.description for p in patterns]}

    RECENT WINS:
    {[w.content for w in recent_wins]}

    RELEVANT MEMORIES:
    {rag_results.context}

    DOMAIN KNOWLEDGE:
    {domain_knowledge}
    """
```

---

## 10. Data Flow & Program Flow

### Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE REQUEST FLOW                                     │
│                                                                              │
│  User: "I'm stuck on my product launch, feeling demotivated"                │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 1: API LAYER                                                          │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  POST /api/v1/chat                                                          │
│  {                                                                           │
│    "message": "I'm stuck on my product launch, feeling demotivated",        │
│    "conversation_id": "conv_123"                                            │
│  }                                                                           │
│                                                                              │
│  → Validate request                                                         │
│  → Get user_id from JWT                                                     │
│  → Load conversation history                                                │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 2: SAFETY CHECK (SafetyAgent)                                         │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  Input: "I'm stuck on my product launch, feeling demotivated"               │
│                                                                              │
│  → Keyword scan: No crisis keywords detected                                │
│  → LLM classification (Haiku): concern_level = 0.2                          │
│                                                                              │
│  Output: SafetyCheck(is_safe=True, concern_level=0.2)                       │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 3: EMOTION DETECTION (EmotionAgent)                                   │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  Input: message + last 3 conversation turns                                 │
│                                                                              │
│  → LLM classification (Haiku):                                              │
│    - Primary emotion: "frustrated"                                          │
│    - Intensity: 3/5                                                         │
│    - Secondary: "sad"                                                       │
│                                                                              │
│  Output: EmotionalState(                                                    │
│    primary="frustrated",                                                    │
│    intensity=3,                                                             │
│    tone_guidance="understanding, solution-focused, acknowledge feelings"   │
│  )                                                                           │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 4: INTENT CLASSIFICATION                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  Input: "I'm stuck on my product launch, feeling demotivated"               │
│                                                                              │
│  → LLM classification (Haiku):                                              │
│    Possible intents: planning, memory, insight, academy, goal, chat         │
│                                                                              │
│  Output: intent="insight" (user needs pattern analysis + encouragement)     │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 5: CONTEXT GATHERING (Parallel)                                       │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Get Identity   │  │   Get Goals     │  │  Get Patterns   │             │
│  │                 │  │                 │  │                 │             │
│  │ ideal_self:     │  │ "Launch MVP"    │  │ AVOIDANCE:      │             │
│  │ "CEO"           │  │ progress: 40%   │  │ "user testing"  │             │
│  │                 │  │                 │  │ rescheduled 5x  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                                   │
│  │  RAG Query      │  │  Get Wins       │                                   │
│  │                 │  │                 │                                   │
│  │ "product launch │  │ "First paying   │                                   │
│  │  motivation"    │  │  customer!"     │                                   │
│  │                 │  │ "Shipped v0.1"  │                                   │
│  │ Results: 3 past │  │                 │                                   │
│  │ journal entries │  │                 │                                   │
│  └─────────────────┘  └─────────────────┘                                   │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 6: AGENT EXECUTION (InsightAgent)                                     │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  Input: All gathered context                                                │
│                                                                              │
│  → Analyze patterns:                                                        │
│    - "user testing" task rescheduled 5 times                                │
│    - Possible fear of negative feedback                                     │
│                                                                              │
│  → Generate insight:                                                        │
│    "I notice you've rescheduled user testing 5 times.                      │
│     This might be fear of criticism - totally normal for creators.         │
│     The CEO-you knows that feedback is fuel, not failure."                 │
│                                                                              │
│  Output: InsightResponse(                                                   │
│    finding="Avoidance pattern on user testing",                            │
│    action="Schedule 1 user call for tomorrow, 15 mins max"                 │
│  )                                                                           │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 7: MENTOR ENGINE (Persona Application)                                │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  Input: InsightResponse + EmotionalState + Identity + Wins                  │
│                                                                              │
│  → Apply "Future Self" persona                                              │
│  → Apply emotional tone (understanding, solution-focused)                   │
│  → Reference specific wins for encouragement                                │
│  → Add concrete action                                                      │
│                                                                              │
│  Output (Sonnet):                                                           │
│  "I get it - launching is scary. Looking at your patterns, I notice        │
│   you've rescheduled user testing 5 times. That's usually fear of          │
│   criticism disguised as 'not ready yet.'                                  │
│                                                                              │
│   Remember when you got your first paying customer? You were terrified     │
│   they'd hate it, but they loved it. That same courage applies here.       │
│                                                                              │
│   The CEO-you doesn't wait for perfect - they ship and iterate.            │
│   Tomorrow: One 15-minute user call. Just one. Can you commit to that?"   │
│                                                                              │
│  ═══════════════════════════════════════════════════════════════════════    │
│  STEP 8: RESPONSE & STORAGE                                                 │
│  ═══════════════════════════════════════════════════════════════════════    │
│                                                                              │
│  → Store message in database:                                               │
│    - User message (role="user")                                             │
│    - Assistant response (role="assistant")                                  │
│    - Intent classification                                                  │
│    - Tokens used                                                            │
│    - Model used                                                             │
│                                                                              │
│  → Track costs                                                              │
│  → Return response to client                                                │
│                                                                              │
│  Response:                                                                  │
│  {                                                                           │
│    "success": true,                                                         │
│    "data": {                                                                │
│      "message": {                                                           │
│        "role": "assistant",                                                 │
│        "content": "I get it - launching is scary..."                       │
│      },                                                                     │
│      "conversation_id": "conv_123"                                         │
│    }                                                                        │
│  }                                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Sequence Diagram

```
User          Frontend       API          Orchestrator    Agents         LLM          Database
 │               │            │               │             │             │              │
 │──message────►│            │               │             │             │              │
 │               │──POST────►│               │             │             │              │
 │               │            │──process()──►│             │             │              │
 │               │            │               │             │             │              │
 │               │            │               │─safety()───►│             │              │
 │               │            │               │             │──classify──►│              │
 │               │            │               │             │◄──safe─────│              │
 │               │            │               │◄────────────│             │              │
 │               │            │               │             │             │              │
 │               │            │               │─emotion()──►│             │              │
 │               │            │               │             │──classify──►│              │
 │               │            │               │             │◄─frustrated─│              │
 │               │            │               │◄────────────│             │              │
 │               │            │               │             │             │              │
 │               │            │               │─intent()───►│             │              │
 │               │            │               │             │──classify──►│              │
 │               │            │               │             │◄──insight──│              │
 │               │            │               │◄────────────│             │              │
 │               │            │               │             │             │              │
 │               │            │               │─────────────────────────────────────────►│
 │               │            │               │         (parallel context load)          │
 │               │            │               │◄────────────────────────────────────────│
 │               │            │               │             │             │              │
 │               │            │               │─insight()──►│             │              │
 │               │            │               │             │──generate──►│              │
 │               │            │               │             │◄──response─│              │
 │               │            │               │◄────────────│             │              │
 │               │            │               │             │             │              │
 │               │            │               │─persona()──►│             │              │
 │               │            │               │             │──generate──►│              │
 │               │            │               │             │◄──final────│              │
 │               │            │               │◄────────────│             │              │
 │               │            │               │             │             │              │
 │               │            │               │─────────────────────────────────────────►│
 │               │            │               │              (store message)             │
 │               │            │               │◄────────────────────────────────────────│
 │               │            │               │             │             │              │
 │               │            │◄──────────────│             │             │              │
 │               │◄───────────│               │             │             │              │
 │◄──────────────│            │               │             │             │              │
 │               │            │               │             │             │              │
```

---

## 11. Database Architecture

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATABASE SCHEMA                                       │
│                                                                              │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐               │
│  │    USER     │       │  IDENTITY   │       │    GOAL     │               │
│  ├─────────────┤       ├─────────────┤       ├─────────────┤               │
│  │ id (PK)     │──1:1─►│ id (PK)     │       │ id (PK)     │               │
│  │ email       │       │ user_id(FK) │◄──────│ user_id(FK) │               │
│  │ password    │       │ ideal_self  │       │ identity_id │               │
│  │ name        │       │ description │       │ title       │               │
│  │ phone       │       │ why         │       │ description │               │
│  │ timezone    │       │ role_models │       │ why         │               │
│  │ created_at  │       │ attributes  │       │ category    │               │
│  │ updated_at  │       │ target_time │       │ timeframe   │               │
│  └─────────────┘       └─────────────┘       │ status      │               │
│        │                                      │ progress_%  │               │
│        │                                      │ start_date  │               │
│        │                                      │ end_date    │               │
│        │                                      └──────┬──────┘               │
│        │                                             │                      │
│        │       ┌─────────────┐       ┌─────────────┐│                      │
│        │       │ KEY_RESULT  │       │    TASK     ││                      │
│        │       ├─────────────┤       ├─────────────┤│                      │
│        │       │ id (PK)     │◄──────│ id (PK)     ││                      │
│        │       │ goal_id(FK) │       │ user_id(FK) ││                      │
│        │       │ title       │       │ goal_id(FK) │◄┘                      │
│        │       │ target_val  │       │ kr_id (FK)  │                       │
│        │       │ current_val │       │ title       │                       │
│        │       │ unit        │       │ description │                       │
│        │       │ progress_%  │       │ sched_date  │                       │
│        │       │ status      │       │ est_minutes │                       │
│        │       └─────────────┘       │ status      │                       │
│        │                             │ completed_at│                       │
│        │                             │ outcome     │                       │
│        │                             └─────────────┘                       │
│        │                                                                    │
│        │       ┌─────────────┐       ┌─────────────┐                       │
│        ├──1:N─►│CONVERSATION │──1:N─►│   MESSAGE   │                       │
│        │       ├─────────────┤       ├─────────────┤                       │
│        │       │ id (PK)     │       │ id (PK)     │                       │
│        │       │ user_id(FK) │       │ conv_id(FK) │                       │
│        │       │ title       │       │ role        │                       │
│        │       │ created_at  │       │ content     │                       │
│        │       └─────────────┘       │ intent      │                       │
│        │                             │ tokens_used │                       │
│        │                             │ model_used  │                       │
│        │                             │ created_at  │                       │
│        │                             └─────────────┘                       │
│        │                                                                    │
│        │       ┌─────────────┐       ┌─────────────┐                       │
│        ├──1:N─►│JOURNAL_ENTRY│       │   PATTERN   │◄──1:N─┤               │
│        │       ├─────────────┤       ├─────────────┤       │               │
│        │       │ id (PK)     │       │ id (PK)     │       │               │
│        │       │ user_id(FK) │       │ user_id(FK) │       │               │
│        │       │ entry_type  │       │ pattern_type│       │               │
│        │       │ content     │       │ description │       │               │
│        │       │ enrichment  │       │ evidence    │       │               │
│        │       │ goal_id(FK) │       │ confidence  │       │               │
│        │       │ mood        │       │ action      │       │               │
│        │       │ energy_lvl  │       │ expires_at  │       │               │
│        │       │ is_favorite │       └─────────────┘       │               │
│        │       │ created_at  │                             │               │
│        │       └─────────────┘                             │               │
│        │                                                    │               │
│        │       ┌─────────────┐       ┌─────────────┐       │               │
│        ├──1:N─►│  MOOD_LOG   │       │  EMBEDDING  │───────┘               │
│        │       ├─────────────┤       ├─────────────┤                       │
│        │       │ id (PK)     │       │ id (PK)     │                       │
│        │       │ user_id(FK) │       │ user_id(FK) │                       │
│        │       │ mood        │       │ content     │                       │
│        │       │ intensity   │       │ source_type │                       │
│        │       │ notes       │       │ source_id   │                       │
│        │       │ source      │       │ vector      │                       │
│        │       │ logged_at   │       │ created_at  │                       │
│        │       └─────────────┘       └─────────────┘                       │
│        │                                                                    │
│        │       ┌─────────────┐                                             │
│        └──1:N─►│  COST_LOG   │                                             │
│                ├─────────────┤                                             │
│                │ id (PK)     │                                             │
│                │ user_id(FK) │                                             │
│                │ model       │                                             │
│                │ input_tok   │                                             │
│                │ output_tok  │                                             │
│                │ cost        │                                             │
│                │ request_type│                                             │
│                │ created_at  │                                             │
│                └─────────────┘                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Cost Optimization Strategies

### Strategy Overview

| Strategy | Savings | Implementation |
|----------|---------|----------------|
| **Task-based model routing** | 60-80% | Haiku for classification, Sonnet for generation |
| **Token budgeting** | 30-40% | Max 4000 tokens for RAG context |
| **Caching** | 20-30% | Redis for repeated queries |
| **Batch embeddings** | 50%+ | Process multiple texts in one API call |
| **Prompt optimization** | 10-20% | Concise system prompts |

### Cost Breakdown Example

```
Monthly Active Users: 1,000
Avg. Messages/User/Day: 5
Monthly Messages: 150,000

WITHOUT OPTIMIZATION:
─────────────────────
All messages → Sonnet ($18/M tokens)
Avg. 1000 tokens/message
Monthly cost: 150M tokens × $18/M = $2,700

WITH OPTIMIZATION:
──────────────────
Classification (60%): 90K × Haiku ($1.50/M) × 200 tokens = $27
Generation (40%): 60K × Sonnet ($18/M) × 800 tokens = $864
Embeddings: 150K × text-embed ($0.02/M) × 100 tokens = $0.30

Monthly cost: ~$891 (67% savings)
```

---

## 13. Security & Safety Architecture

### Safety Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SAFETY ARCHITECTURE                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 1: INPUT VALIDATION                                              │ │
│  │  • Rate limiting (100 req/min per user)                                 │ │
│  │  • Input sanitization (no code injection)                               │ │
│  │  • Max message length (10,000 chars)                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 2: CRISIS DETECTION (SafetyAgent)                                │ │
│  │                                                                          │ │
│  │  Fast Path: Keyword matching                                            │ │
│  │  • "suicide", "kill myself", "end my life", etc.                        │ │
│  │  • Immediate intervention with helpline resources                       │ │
│  │                                                                          │ │
│  │  Slow Path: LLM classification (for subtle cases)                       │ │
│  │  • Concern level 0-1                                                    │ │
│  │  • Threshold: 0.7 triggers support response                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 3: TOPIC BOUNDARIES                                              │ │
│  │                                                                          │ │
│  │  ALLOWED (In Scope):                                                    │ │
│  │  ✓ Career planning, job search                                          │ │
│  │  ✓ Skill development, learning                                          │ │
│  │  ✓ Goal setting, productivity                                           │ │
│  │  ✓ Motivation, encouragement                                            │ │
│  │                                                                          │ │
│  │  NOT ALLOWED (Out of Scope):                                            │ │
│  │  ✗ Medical/health advice → Redirect to professionals                   │ │
│  │  ✗ Therapy/mental health → Provide resources                           │ │
│  │  ✗ Financial advice → General guidance only                            │ │
│  │  ✗ Legal advice → Suggest consulting lawyer                            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  LAYER 4: OUTPUT SAFETY                                                 │ │
│  │  • No PII in logs                                                       │ │
│  │  • No harmful content generation                                        │ │
│  │  • Appropriate for all ages                                             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Privacy

| Data Type | Storage | Encryption | Retention |
|-----------|---------|------------|-----------|
| Passwords | Hashed (bcrypt) | N/A | Permanent |
| Messages | Database | At-rest | 2 years |
| Embeddings | Vector Store | At-rest | Until deleted |
| Audio | Not stored | N/A | Processed & discarded |
| API Keys | Environment | In-transit (TLS) | N/A |

---

## 14. Deployment Architecture

### Production Setup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION DEPLOYMENT                                    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CLOUDFLARE                                   │   │
│  │                    (CDN + DDoS Protection)                          │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      LOAD BALANCER                                   │   │
│  │                    (AWS ALB / nginx)                                │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                    ┌──────────────┴──────────────┐                         │
│                    ▼                             ▼                         │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐         │
│  │       FRONTEND PODS        │  │       BACKEND PODS          │         │
│  │                             │  │                             │         │
│  │  ┌─────────┐ ┌─────────┐   │  │  ┌─────────┐ ┌─────────┐   │         │
│  │  │ Next.js │ │ Next.js │   │  │  │ FastAPI │ │ FastAPI │   │         │
│  │  │  Pod 1  │ │  Pod 2  │   │  │  │  Pod 1  │ │  Pod 2  │   │         │
│  │  └─────────┘ └─────────┘   │  │  └─────────┘ └─────────┘   │         │
│  │                             │  │                             │         │
│  │  Kubernetes / ECS          │  │  Kubernetes / ECS          │         │
│  │  Auto-scaling: 2-10 pods   │  │  Auto-scaling: 2-20 pods   │         │
│  └─────────────────────────────┘  └──────────────┬──────────────┘         │
│                                                   │                         │
│                    ┌──────────────────────────────┼──────────────┐         │
│                    ▼                              ▼              ▼         │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌───────────────────┐ │
│  │     PostgreSQL      │  │       Redis         │  │   Vector Store    │ │
│  │    (AWS RDS)        │  │   (ElastiCache)     │  │   (Pinecone)      │ │
│  │                     │  │                     │  │                   │ │
│  │  • Multi-AZ         │  │  • Session cache    │  │  • 1536 dims      │ │
│  │  • Read replicas    │  │  • Rate limiting    │  │  • Cosine metric  │ │
│  │  • Auto backup      │  │  • Query cache      │  │  • Namespaces     │ │
│  └─────────────────────┘  └─────────────────────┘  └───────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      EXTERNAL SERVICES                               │   │
│  │                                                                       │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │   │
│  │  │ Anthropic │  │  OpenAI   │  │  Sentry   │  │ DataDog   │        │   │
│  │  │  (Claude) │  │(Whisper/  │  │  (Errors) │  │(Metrics)  │        │   │
│  │  │           │  │   TTS)    │  │           │  │           │        │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15. Interview Discussion Points

### Common Questions & Answers

#### Q1: "Why did you choose Claude over GPT-4 as the primary model?"

**Answer:**
"We evaluated both models for our use case and chose Claude for several reasons:

1. **Instruction Following**: Claude is excellent at following complex persona instructions (our 'future self' coaching requires nuanced role-play)

2. **Safety**: Claude has strong built-in safety features, important for an app dealing with user emotions and goals

3. **Cost-Performance**: Claude Sonnet offers the best balance - $18/M tokens vs GPT-4's $30/M with comparable quality

4. **Haiku for Classification**: Claude's Haiku model is 10x cheaper and faster than GPT-3.5, perfect for our intent classification and emotion detection

We kept GPT-4 as a fallback for reliability - if Anthropic has downtime, we automatically switch."

---

#### Q2: "Why Hybrid RAG instead of just vector search?"

**Answer:**
"Pure vector search has a significant weakness - it can miss exact keyword matches. For example:

- User asks: 'How am I doing on my fitness goal?'
- Vector search might return semantically related entries about 'health' or 'exercise'
- But might miss an entry that explicitly mentions 'fitness goal' with different wording

BM25 (keyword search) catches exact matches, while vector search catches semantic similarity.

We use **Reciprocal Rank Fusion** to combine both:
- Each retriever returns top 20 results
- RRF combines rankings without needing to normalize scores
- Formula: score = Σ(1/(k+rank+1)) where k=60
- This gives us the best of both worlds with minimal latency overhead"

---

#### Q3: "How do you handle the context window limitation?"

**Answer:**
"We use a multi-layer context strategy:

1. **Immediate Context** (~2K tokens): Current conversation history
2. **Identity Context** (~500 tokens): User's goals, ideal_self - always included
3. **Behavioral Context** (~1K tokens): Summarized patterns from 90 days
4. **RAG Context** (up to 4K tokens): Dynamically retrieved based on query
5. **Knowledge Context** (~1K tokens): Domain expertise based on user's ideal_self

Total budget: ~8K tokens, well within Claude's 200K window.

The key insight is that we don't need all history - we need *relevant* history. RAG ensures we retrieve only what matters for the current query."

---

#### Q4: "How do you ensure safety with an AI companion?"

**Answer:**
"Safety is our first priority - literally. Every message goes through our Safety Agent before any other processing:

1. **Fast Path**: Keyword scan for crisis terms (suicide, self-harm) - instant detection
2. **Slow Path**: LLM classification for subtle cases - catches things like 'I don't see the point anymore'
3. **Intervention**: If detected, we immediately provide helpline resources (iCall for India, 988 for US) and shift to supportive mode

Beyond crisis detection:
- **Topic Boundaries**: We explicitly don't provide medical, legal, or financial advice
- **Emotional Awareness**: Our Emotion Agent detects distress and adjusts tone
- **No Data Storage for Audio**: Voice is transcribed and discarded, never stored

We've also defined clear escalation paths - some situations need human intervention, not AI."

---

#### Q5: "Walk me through what happens when a user sends a message"

**Answer:**
"Let me trace a real example: User says 'I'm stuck on my product launch'

1. **API Layer**: Validate request, extract user from JWT, load conversation history

2. **Safety Check** (50ms): Scan for crisis keywords → None found → Proceed

3. **Emotion Detection** (200ms): Analyze message + recent history → 'frustrated', intensity 3/5 → Tone guidance: 'understanding, solution-focused'

4. **Intent Classification** (200ms): Determine what user needs → 'insight' (not planning, not memory recall)

5. **Context Gathering** (parallel, 300ms):
   - Load identity: 'CEO' with attributes ['decisive', 'strategic']
   - Load goals: 'Launch MVP', 40% progress
   - Load patterns: Avoidance on 'user testing'
   - RAG query: Find related journal entries
   - Load recent wins: 'First paying customer'

6. **Agent Execution** (1s): InsightAgent analyzes patterns, finds avoidance, generates insight with action

7. **Persona Application** (500ms): Wrap in 'future self' voice, apply emotional tone, reference specific wins

8. **Storage**: Save both messages, track tokens, log costs

Total latency: ~2-3 seconds for a thoughtful, personalized, emotionally-aware response."

---

#### Q6: "What would you do differently if starting over?"

**Answer:**
"Three things I'd change:

1. **Event Sourcing for Context**: Currently we query multiple tables for context. Event sourcing would give us a cleaner audit trail and easier replay for debugging

2. **Streaming from Day 1**: We added streaming later, but designing for it upfront would have been cleaner. Users expect real-time responses

3. **More Aggressive Caching**: We cache at Redis level, but could cache at the semantic level - if user asks similar questions, we could serve cached responses with minor personalization"

---

#### Q7: "How do you measure success of the AI system?"

**Answer:**
"We track several metrics:

**Engagement Metrics:**
- Daily Active Users (DAU)
- Messages per session
- Retention (D1, D7, D30)

**AI Quality Metrics:**
- Intent classification accuracy (sampled and human-evaluated)
- User satisfaction (thumbs up/down on responses)
- Task completion rate (did users complete suggested actions?)

**Business Metrics:**
- Cost per user per month
- Conversion rate (free → paid)
- Goal completion rate (are users achieving their stated goals?)

The key insight: We don't just measure if the AI responded correctly, we measure if users are *actually becoming more productive*. That's the real success metric for a coaching product."

---

### Key Talking Points for Interviews

1. **Multi-Agent Architecture**: "We decomposed the problem into specialized agents rather than one monolithic prompt. This gives us better testability, maintainability, and the ability to improve components independently."

2. **Cost Optimization**: "By routing classification tasks to Haiku and generation to Sonnet, we reduced costs by 67% without sacrificing quality. Task-based routing is key."

3. **Hybrid RAG**: "Pure vector search isn't enough. We combine semantic and keyword search using Reciprocal Rank Fusion for more reliable retrieval."

4. **Context Management**: "LLMs have limited context, but users have unlimited history. We solve this with a 5-layer context strategy that prioritizes relevance over recency."

5. **Safety First**: "Every message passes through safety checks before processing. We have fast paths for crisis detection and clear escalation protocols."

6. **Personalization**: "The 'future self' persona isn't just a gimmick - it's grounded in user's stated goals, detected patterns, and actual wins. This makes advice feel personal, not generic."

---

## Appendix A: Technology Comparison Matrix

| Category | Our Choice | Alternatives Considered | Why We Chose |
|----------|------------|------------------------|--------------|
| Primary LLM | Claude Sonnet | GPT-4, Llama 3 | Best instruction following, cost-effective |
| Fast LLM | Claude Haiku | GPT-3.5-turbo | 10x cheaper, faster for classification |
| Embeddings | text-embedding-3-small | Cohere, Voyage | OpenAI ecosystem, good quality/cost ratio |
| Vector Store | In-DB (pgvector) | Pinecone, Weaviate | Simpler ops, good for <1M vectors |
| STT | Whisper | AssemblyAI, Deepgram | Best accuracy, especially for accents |
| TTS | OpenAI TTS | ElevenLabs, Play.ht | Natural voice, simple API |
| Framework | FastAPI | Django, Flask | Native async, auto-docs, Pydantic |
| Database | PostgreSQL | MongoDB, DynamoDB | Relational + pgvector, battle-tested |

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **RAG** | Retrieval-Augmented Generation - combining search with LLMs |
| **RRF** | Reciprocal Rank Fusion - algorithm to combine multiple ranking lists |
| **BM25** | Best Matching 25 - keyword-based ranking algorithm |
| **VAD** | Voice Activity Detection - detecting when speech starts/stops |
| **OKR** | Objectives and Key Results - goal-setting framework |
| **STT** | Speech-to-Text - converting audio to written text |
| **TTS** | Text-to-Speech - converting text to audio |
| **Haiku/Sonnet** | Claude model sizes (small/medium) |
| **pgvector** | PostgreSQL extension for vector similarity search |
| **JWT** | JSON Web Token - authentication token format |

---

*Document maintained by: AI Architecture Team*
*Last reviewed: December 2024*
