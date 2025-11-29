# Kalag Production Deployment Guide

This guide covers everything you need to deploy Kalag to production.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Production Requirements](#production-requirements)
3. [Database Setup (PostgreSQL)](#database-setup-postgresql)
4. [Backend Deployment (Render)](#backend-deployment-render)
5. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
6. [Vector Database (Qdrant Cloud)](#vector-database-qdrant-cloud)
7. [Environment Variables](#environment-variables)
8. [Database Schema & Viewing](#database-schema--viewing)
9. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│   PostgreSQL    │
│    (Vercel)     │     │    (Render)     │     │    (Render)     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
            ┌──────────┐  ┌──────────┐  ┌──────────┐
            │  Qdrant  │  │  Gemini  │  │  LLama   │
            │  Cloud   │  │   API    │  │  Parse   │
            └──────────┘  └──────────┘  └──────────┘
```

---

## Production Requirements

### Backend Services (All Free Tier Available)

| Service | Purpose | Free Tier | Paid Recommendation |
|---------|---------|-----------|---------------------|
| **Render** | Backend hosting + PostgreSQL | ✅ 750 hrs/mo + 1GB DB | Starter $7/mo |
| **Vercel** | Frontend hosting | ✅ 100GB bandwidth | Pro $20/mo |
| **Qdrant Cloud** | Vector database | ✅ 1GB free cluster | Starter $25/mo |
| **Google AI** | Gemini API | ✅ 1M tokens/day | Pay-as-you-go |
| **LlamaParse** | PDF parsing | ✅ 1000 pages/day | $50/mo |

### API Keys Needed

1. **Google AI API Key** - [Get it here](https://aistudio.google.com/app/apikey)
2. **Qdrant Cloud API Key** - [Get it here](https://cloud.qdrant.io/)
3. **LlamaParse API Key** (optional) - [Get it here](https://cloud.llamaindex.ai/)

---

## Database Setup (PostgreSQL)

### Why PostgreSQL Over SQLite for Production?

| Feature | SQLite (Current) | PostgreSQL (Production) |
|---------|-----------------|-------------------------|
| Concurrent connections | Single writer | Unlimited |
| Data size | <1GB recommended | Terabytes |
| Backups | Manual | Automated |
| Scaling | Cannot | Horizontal & Vertical |
| ACID compliance | Limited | Full |

**Your local SQLite database will NOT work in production.** Here's how to set up PostgreSQL:

### Option 1: Render PostgreSQL (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `kalag-db`
   - **Region**: Oregon (same as backend)
   - **Plan**: Free (1GB) or Starter ($7/mo for 5GB)
4. Copy the **Internal Database URL** (starts with `postgresql://`)

### Option 2: Supabase PostgreSQL (Alternative)

1. Go to [Supabase](https://supabase.com/)
2. Create new project
3. Go to **Settings** → **Database** → **Connection string**
4. Copy the URI (use "Session pooler" for serverless)

### Option 3: Neon PostgreSQL (Another Alternative)

1. Go to [Neon](https://neon.tech/)
2. Create new project
3. Copy the connection string

---

## Backend Deployment (Render)

### Step 1: Prepare Your Repository

Make sure your `render.yaml` is updated:

```yaml
# render.yaml (already in your repo)
services:
  - type: web
    name: kalag-api
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: kalag-db
          property: connectionString
      - key: QDRANT_URL
        sync: false
      - key: QDRANT_API_KEY
        sync: false
      - key: GOOGLE_API_KEY
        sync: false
      - key: LLAMA_CLOUD_API_KEY
        sync: false
      - key: CORS_ORIGINS
        value: https://kalag.vercel.app
      - key: COOKIE_SECURE
        value: "true"
      - key: COOKIE_DOMAIN
        value: kalag.vercel.app
      - key: DEBUG
        value: "false"

databases:
  - name: kalag-db
    plan: free
    region: oregon
    postgresMajorVersion: 15
```

### Step 2: Deploy to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New** → **Blueprint**
3. Connect your GitHub repo (`Mitakashim3/Kalag`)
4. Select the `backend` folder as root directory
5. Render will detect `render.yaml` and create services automatically
6. Add your secret environment variables manually:
   - `GOOGLE_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   - `LLAMA_CLOUD_API_KEY`

### Step 3: Verify Deployment

Once deployed, visit:
```
https://kalag-api.onrender.com/api/health
```

You should see:
```json
{"status": "healthy", "database": "connected"}
```

---

## Frontend Deployment (Vercel)

### Step 1: Update API URL

Create/update `frontend/.env.production`:

```env
VITE_API_URL=https://kalag-api.onrender.com
```

### Step 2: Deploy to Vercel

1. Go to [Vercel](https://vercel.com/)
2. Click **Add New** → **Project**
3. Import your GitHub repo
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variable:
   - `VITE_API_URL` = `https://kalag-api.onrender.com`
6. Click **Deploy**

### Step 3: Update CORS on Backend

After getting your Vercel URL (e.g., `https://kalag.vercel.app`), update the `CORS_ORIGINS` environment variable on Render.

---

## Vector Database (Qdrant Cloud)

### Step 1: Create Qdrant Cluster

1. Go to [Qdrant Cloud](https://cloud.qdrant.io/)
2. Sign up/Login
3. Click **Create Cluster**
4. Configure:
   - **Name**: `kalag-vectors`
   - **Cloud**: AWS
   - **Region**: us-east-1 (or closest to your backend)
   - **Plan**: Free (1GB)
5. Wait for cluster to be ready (~2 minutes)

### Step 2: Get Credentials

1. Click on your cluster
2. Copy the **Cluster URL** (e.g., `https://xxx-xxx.aws.cloud.qdrant.io`)
3. Go to **API Keys** → **Create API Key**
4. Copy the API key

### Step 3: Add to Render Environment

On Render dashboard, add:
- `QDRANT_URL` = `https://xxx-xxx.aws.cloud.qdrant.io`
- `QDRANT_API_KEY` = `your-api-key`

---

## Environment Variables

### Complete Production Environment Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `SECRET_KEY` | JWT signing key | Auto-generated by Render |
| `DATABASE_URL` | PostgreSQL connection | Render PostgreSQL |
| `QDRANT_URL` | Vector DB URL | Qdrant Cloud |
| `QDRANT_API_KEY` | Vector DB key | Qdrant Cloud |
| `GOOGLE_API_KEY` | Gemini AI | Google AI Studio |
| `LLAMA_CLOUD_API_KEY` | PDF parsing | LlamaIndex Cloud |
| `CORS_ORIGINS` | Frontend URL | Your Vercel URL |
| `COOKIE_SECURE` | `true` | Set this |
| `COOKIE_DOMAIN` | Your domain | Your Vercel domain |
| `DEBUG` | `false` | Set this |

---

## Database Schema & Viewing

### Your Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                          USERS                                  │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)          │ VARCHAR(36)  │ UUID                          │
│ email            │ VARCHAR(255) │ UNIQUE, NOT NULL              │
│ hashed_password  │ VARCHAR(255) │ bcrypt hash                   │
│ full_name        │ VARCHAR(255) │ nullable                      │
│ is_active        │ BOOLEAN      │ default: true                 │
│ is_superuser     │ BOOLEAN      │ default: false                │
│ created_at       │ DATETIME     │ auto                          │
│ updated_at       │ DATETIME     │ auto                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ 1:N
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       REFRESH_TOKENS                            │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)          │ VARCHAR(36)  │ UUID                          │
│ user_id (FK)     │ VARCHAR(36)  │ → users.id                    │
│ token_hash       │ VARCHAR(255) │ indexed                       │
│ expires_at       │ DATETIME     │ NOT NULL                      │
│ revoked          │ BOOLEAN      │ default: false                │
│ user_agent       │ VARCHAR(512) │ device tracking               │
│ ip_address       │ VARCHAR(45)  │ IPv6 compatible               │
│ created_at       │ DATETIME     │ auto                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        DOCUMENTS                                │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)           │ VARCHAR(36)  │ UUID                         │
│ owner_id (FK)     │ VARCHAR(36)  │ → users.id                   │
│ original_filename │ VARCHAR(255) │ user's filename              │
│ stored_filename   │ VARCHAR(255) │ UUID-based secure name       │
│ file_path         │ VARCHAR(512) │ relative path                │
│ file_size_bytes   │ INTEGER      │ NOT NULL                     │
│ mime_type         │ VARCHAR(100) │ e.g., application/pdf        │
│ status            │ VARCHAR(50)  │ pending/processing/completed │
│ total_pages       │ INTEGER      │ nullable                     │
│ processing_error  │ TEXT         │ error message if failed      │
│ created_at        │ DATETIME     │ auto                         │
│ processed_at      │ DATETIME     │ nullable                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │ 1:N                           │ 1:N
                ▼                               ▼
┌───────────────────────────────┐  ┌───────────────────────────────┐
│       DOCUMENT_PAGES          │  │      DOCUMENT_CHUNKS          │
├───────────────────────────────┤  ├───────────────────────────────┤
│ id (PK)                       │  │ id (PK)                       │
│ document_id (FK)              │  │ document_id (FK)              │
│ page_number                   │  │ content (TEXT)                │
│ image_path                    │  │ chunk_index                   │
│ width, height                 │  │ page_numbers                  │
│ vision_description            │  │ vector_id (→ Qdrant)          │
│ has_charts/tables/images      │  │ chunk_type                    │
│ created_at                    │  │ token_count                   │
└───────────────────────────────┘  └───────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      SEARCH_HISTORY                             │
├─────────────────────────────────────────────────────────────────┤
│ id (PK)          │ VARCHAR(36)  │ UUID                          │
│ user_id (FK)     │ VARCHAR(36)  │ → users.id                    │
│ query            │ TEXT         │ user's search query           │
│ response         │ TEXT         │ AI response                   │
│ chunks_retrieved │ INTEGER      │ metrics                       │
│ response_time_ms │ INTEGER      │ metrics                       │
│ was_helpful      │ BOOLEAN      │ user feedback                 │
│ created_at       │ DATETIME     │ auto                          │
└─────────────────────────────────────────────────────────────────┘
```

### How to View Database in Production

#### Option 1: Render PostgreSQL Dashboard (Easiest)

1. Go to Render Dashboard → Your PostgreSQL instance
2. Click **Connect** → **PSQL Command**
3. You can run SQL directly in browser

#### Option 2: pgAdmin (GUI Tool)

1. Download [pgAdmin](https://www.pgadmin.org/download/)
2. Create new server connection:
   - **Host**: Your Render DB external hostname
   - **Port**: 5432
   - **Database**: Your database name
   - **Username**: Your username
   - **Password**: Your password
3. Browse tables under **Schemas** → **public** → **Tables**

#### Option 3: DBeaver (Alternative GUI)

1. Download [DBeaver](https://dbeaver.io/download/)
2. Create new PostgreSQL connection
3. Enter your Render external database URL credentials

#### Option 4: Command Line (psql)

```bash
# Connect using the external URL from Render
psql "postgresql://user:password@hostname:5432/database?sslmode=require"

# List all tables
\dt

# View table schema
\d users
\d documents
\d document_chunks

# Sample queries
SELECT * FROM users;
SELECT COUNT(*) FROM documents WHERE status = 'completed';
```

#### Option 5: Create an Admin API Endpoint (Recommended)

Add this to your backend for secure schema viewing:

```python
# In app/api/routes/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.api.deps import get_current_superuser
from app.db.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/schema")
async def get_schema(
    db = Depends(get_db),
    user = Depends(get_current_superuser)  # Only superusers
):
    """Get database schema information"""
    result = await db.execute(text("""
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """))
    
    schema = {}
    for row in result:
        table = row[0]
        if table not in schema:
            schema[table] = []
        schema[table].append({
            "column": row[1],
            "type": row[2],
            "nullable": row[3]
        })
    
    return schema

@router.get("/stats")
async def get_stats(
    db = Depends(get_db),
    user = Depends(get_current_superuser)
):
    """Get database statistics"""
    users = await db.execute(text("SELECT COUNT(*) FROM users"))
    docs = await db.execute(text("SELECT COUNT(*) FROM documents"))
    chunks = await db.execute(text("SELECT COUNT(*) FROM document_chunks"))
    
    return {
        "users": users.scalar(),
        "documents": docs.scalar(),
        "chunks": chunks.scalar()
    }
```

---

## Post-Deployment Checklist

### ✅ Security Checklist

- [ ] `SECRET_KEY` is randomly generated (not default)
- [ ] `DEBUG` is set to `false`
- [ ] `COOKIE_SECURE` is `true`
- [ ] HTTPS is enabled (automatic on Render/Vercel)
- [ ] CORS is restricted to your frontend domain only
- [ ] Rate limiting is configured
- [ ] Database uses SSL connection

### ✅ Functionality Checklist

- [ ] Health endpoint responds: `/api/health`
- [ ] User registration works
- [ ] User login works
- [ ] File upload works
- [ ] Document processing completes
- [ ] Search returns results
- [ ] Visual citations display correctly

### ✅ Monitoring Setup

1. **Render Dashboard**: View logs, metrics, and alerts
2. **Vercel Analytics**: Frontend performance
3. **Optional**: Add Sentry for error tracking

---

## Quick Start Commands

### Deploy Everything (After Setup)

```bash
# Push to GitHub - Render and Vercel auto-deploy
git add .
git commit -m "Production deployment"
git push origin main
```

### View Render Logs

```bash
# In Render Dashboard → Your Service → Logs
# Or use Render CLI
render logs kalag-api
```

### Database Migration (If Schema Changes)

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

---

## Estimated Monthly Costs

### Free Tier (Getting Started)

| Service | Cost |
|---------|------|
| Render Backend | $0 |
| Render PostgreSQL | $0 |
| Vercel Frontend | $0 |
| Qdrant Cloud | $0 |
| Google Gemini API | $0 (1M tokens/day) |
| **Total** | **$0/month** |

### Production Scale (~100 users)

| Service | Cost |
|---------|------|
| Render Backend | $7/mo |
| Render PostgreSQL | $7/mo |
| Vercel Pro | $20/mo |
| Qdrant Starter | $25/mo |
| Google Gemini API | ~$10/mo |
| **Total** | **~$69/month** |

---

## Need Help?

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Qdrant Docs**: https://qdrant.tech/documentation/

Good luck with your deployment! 🚀
