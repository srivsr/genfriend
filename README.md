# Gen-Friend v3

AI-powered productivity companion — the opposite of Instagram.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  Next.js PWA (Mobile-first) → Future: Android, iOS, WhatsApp    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                         │
│  Auth │ Rate Limiting │ Request Router │ Session Manager        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 CORE INTELLIGENCE & AGENTS                       │
│  Orchestrator │ Memory │ Planner │ Insight │ Emotion │ Safety   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI / LLM & RAG ENGINE                         │
│  LLM Router │ Query Rewriter │ Retriever │ Reranker │ Generator │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATA & INFRASTRUCTURE                          │
│  PostgreSQL+pgvector │ Redis │ S3 │ Metrics/Logs                │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, PWA
- **Backend**: FastAPI, Python 3.11+, async-first
- **Database**: PostgreSQL 16 + pgvector
- **Cache**: Redis
- **AI**: Claude API (primary), OpenAI (fallback)

## Quick Start

### Using Docker

```bash
cd docker
cp ../.env.example ../.env
# Edit .env with your API keys
docker-compose up -d
```

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Core Agents

1. **Conversation Orchestrator** - Routes queries to appropriate agents
2. **Memory Agent** - Personal RAG for user data
3. **Planner Agent** - Daily/weekly plan generation
4. **Insight Agent** - Pattern recognition and insights
5. **Emotional Engine** - Mood detection and tone adaptation
6. **Safety Engine** - Crisis detection and guardrails
7. **Academy Agent** - AI education and explanations

## API Endpoints

- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/chat` - Main chat endpoint
- `GET /api/v1/planning/today` - Get today's plan
- `POST /api/v1/planning/today` - Generate new plan
- `GET /api/v1/entries` - List journal entries
- `GET /api/v1/insights/weekly` - Weekly summary
- `GET /api/v1/academy/topics` - List AI topics

## Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/genfriend
REDIS_URL=redis://localhost:6379
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
JWT_SECRET=your-secret-key
```

## Project Structure

```
gen-friend-v3/
├── frontend/           # Next.js application
│   ├── app/           # App router pages
│   ├── components/    # React components
│   ├── lib/           # API client, utils
│   └── stores/        # Zustand state
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── agents/    # AI agents
│   │   ├── rag/       # RAG pipeline
│   │   ├── llm/       # LLM providers
│   │   ├── models/    # SQLAlchemy models
│   │   └── schemas/   # Pydantic schemas
│   └── tests/
├── docker/            # Docker configs
└── docs/              # Documentation
```
