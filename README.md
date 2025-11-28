# Kalag - Internal RAG Tool for Businesses

An internal Retrieval-Augmented Generation (RAG) tool that enables multi-modal search across business documents with visual citations.

## 🎯 Core Features

- **Multi-Modal Search**: Upload PDFs, search across text AND images (charts/diagrams)
- **Visual Citations**: Get answers with page numbers and cropped relevant sections
- **Mobile-First PWA**: React-based Progressive Web App
- **Security Hardened**: Protected against XSS, CSRF, Prompt Injection

## 🏗️ Tech Stack

| Layer | Technology | Hosting |
|-------|------------|---------|
| Frontend | React (Vite) + Tailwind + ShadCN UI | Vercel Free Tier |
| Backend | Python FastAPI | Render Free Tier |
| Vector DB | Qdrant Cloud | Free Tier (1GB) |
| Relational DB | Supabase PostgreSQL | Free Tier |
| LLM/Vision | Google Gemini Flash API | Free Tier |
| PDF Parsing | LlamaParse | Free Tier |

## 📁 Project Structure

```
kalag/
├── frontend/                    # React PWA (Vite)
│   ├── public/
│   │   ├── manifest.json       # PWA manifest
│   │   └── sw.js               # Service worker
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/             # ShadCN components
│   │   │   ├── auth/           # Login, Register forms
│   │   │   ├── documents/      # Upload, List, Viewer
│   │   │   ├── search/         # Search bar, Results
│   │   │   └── layout/         # Header, Sidebar, Mobile nav
│   │   ├── hooks/
│   │   │   ├── useAuth.ts      # Auth state & token refresh
│   │   │   └── useApi.ts       # API calls with auth
│   │   ├── lib/
│   │   │   ├── api.ts          # Axios instance with interceptors
│   │   │   └── utils.ts        # Utilities
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Search.tsx
│   │   │   └── Documents.tsx
│   │   ├── store/
│   │   │   └── authStore.ts    # Zustand for auth state
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── package.json
│
├── backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app entry
│   │   ├── config.py           # Environment config
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py         # Dependency injections
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py     # Login, Register, Refresh
│   │   │       ├── documents.py # Upload, List, Delete
│   │   │       └── search.py   # RAG search endpoint
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── jwt.py          # JWT token utilities
│   │   │   ├── security.py     # Password hashing, validation
│   │   │   └── dependencies.py # Auth middleware
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py     # SQLAlchemy setup
│   │   │   ├── models.py       # ORM models
│   │   │   └── schemas.py      # Pydantic schemas
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py       # LlamaParse integration
│   │   │   ├── vision.py       # Gemini vision pipeline
│   │   │   └── chunker.py      # Text chunking logic
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py   # Embedding generation
│   │   │   ├── vectorstore.py  # Qdrant operations
│   │   │   ├── retriever.py    # Retrieval logic
│   │   │   └── generator.py    # Gemini response generation
│   │   ├── security/
│   │   │   ├── __init__.py
│   │   │   ├── headers.py      # Security headers middleware
│   │   │   ├── sanitizer.py    # Input sanitization
│   │   │   └── rate_limit.py   # Rate limiting config
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── storage.py      # File storage utilities
│   ├── requirements.txt
│   ├── Dockerfile
│   └── render.yaml             # Render deployment config
│
├── docker-compose.yml          # Local development
├── .env.example
└── .gitignore
```

## 🔐 Auth Flow

1. User logs in → Backend returns `access_token` (short-lived) + `refresh_token` (HttpOnly cookie)
2. Frontend stores `access_token` in memory (Zustand store)
3. `refresh_token` is stored in HttpOnly, Secure cookie (XSS protected)
4. Background refresh happens before token expiry
5. On page reload, silent refresh via cookie restores session

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- Qdrant Cloud account
- Supabase account
- Google AI Studio API key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env with your credentials
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 📄 License

MIT License - Internal Use
