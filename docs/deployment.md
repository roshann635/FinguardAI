# Deployment Guide

This guide covers local development setup, environment configuration, and cloud deployment for FinGuard AI.

---

## 1. Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL 14+** (local) or a cloud PostgreSQL provider
- **Google Gemini API key** — get one free at [aistudio.google.com](https://aistudio.google.com/app/apikey)
- **Git**

---

## 2. Local Development — Step by Step

```bash
# 1. Clone the repository
git clone https://github.com/your-org/finguard-ai.git
cd finguard-ai

# 2. Copy and configure environment variables
cp .env.example backend/.env
# Edit backend/.env with your actual values (see §3)

# 3. Create and activate a Python virtual environment
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. Install backend dependencies
pip install -r requirements.txt

# 5. Create the PostgreSQL database (see §4)

# 6. Run database migrations and seed
python -c "
from app.database.connection import Base, engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('Tables created.')
"
# Seed synthetic data (adjust path if needed)
python -m data.seed

# 7. Start the backend
uvicorn main:app --reload --port 8000

# 8. In a new terminal — start the frontend
cd ../frontend
npm install
npm run dev
```

The application will be available at:
- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000/api/v1`
- **Swagger UI:** `http://localhost:8000/docs`

---

## 3. Environment Variables

All variables are loaded from `backend/.env` (or the system environment in production). The full set of variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string, e.g. `postgresql://user:pass@localhost:5432/finguard` |
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API key from [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| `FRONTEND_URL` | ❌ | `http://localhost:5173` | Allowed CORS origin for the frontend |
| `BACKEND_URL` | ❌ | `http://localhost:8000` | Backend URL (used for internal references) |
| `ENVIRONMENT` | ❌ | `development` | Runtime environment: `development`, `staging`, or `production` |
| `DEBUG` | ❌ | `false` | Set to `true` for verbose debug logging. **Never enable in production.** |

### `.env.example`

```dotenv
# PostgreSQL connection string
DATABASE_URL=postgresql://user:password@localhost:5432/finguard

# Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here

# CORS allowed origin
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

# Runtime environment: development | staging | production
ENVIRONMENT=development
```

> **Security:** Never commit `.env` to source control. It is listed in `.gitignore`.

---

## 4. Database Setup

### Create the database locally

```bash
# Using psql
psql -U postgres
CREATE DATABASE finguard;
\q

# Or in one command
psql -U postgres -c "CREATE DATABASE finguard;"
```

### Run migrations

```bash
cd finguard-ai/backend
# (virtual environment must be active)
python -c "
from app.database.connection import Base, engine
from app.models import *  # noqa — registers all model metadata
Base.metadata.create_all(bind=engine)
print('All tables created successfully.')
"
```

### Seed synthetic data

```bash
python -m data.seed
# Expected output: "Seeded X categories, Y customers, Z transactions ..."
```

---

## 5. Running the Backend

```bash
cd finguard-ai/backend

# Development (auto-reload on file changes)
uvicorn main:app --reload --port 8000

# Production (multiple workers, no reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be live at `http://localhost:8000`. Swagger docs at `/docs`.

---

## 6. Running the Frontend

```bash
cd finguard-ai/frontend

# Install dependencies (first time only)
npm install

# Development server with hot-reload
npm run dev

# Production build
npm run build
# Output in frontend/dist/ — serve with any static host
```

The development server runs at `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

### Frontend environment variable

Create `frontend/.env.local` for local overrides:

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

---

## 7. Docker Compose

A `docker-compose.yml` at the project root brings up PostgreSQL, the backend, and the frontend together.

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove volumes (wipes database)
docker-compose down -v
```

Services exposed:
- **Frontend:** `http://localhost:5173`
- **Backend:** `http://localhost:8000`
- **PostgreSQL:** `localhost:5432` (internal only; exposed on host for debugging)

---

## 8. Cloud Deployment

### 8.1 Database — Neon (Recommended Free Option)

[Neon](https://neon.tech) provides serverless PostgreSQL with a generous free tier.

1. Sign up at [neon.tech](https://neon.tech) and create a new project
2. Copy the connection string from the dashboard — format: `postgresql://user:pass@ep-xxx.neon.tech/finguard?sslmode=require`
3. Set `DATABASE_URL` on your backend host to this connection string
4. Run migrations remotely:
   ```bash
   DATABASE_URL="postgresql://..." python -c "
   from app.database.connection import Base, engine
   from app.models import *
   Base.metadata.create_all(bind=engine)
   "
   ```
5. Seed data:
   ```bash
   DATABASE_URL="postgresql://..." python -m data.seed
   ```

**Alternatives:**
- **Supabase** — [supabase.com](https://supabase.com): Free tier, has dashboard UI, connection string under Project Settings → Database
- **Railway** — [railway.app](https://railway.app): Provision PostgreSQL as an add-on, copy `DATABASE_URL` from Variables tab

---

### 8.2 Backend — Render (Free Tier)

[Render](https://render.com) provides free web service hosting for Python apps.

1. Push your code to GitHub
2. Sign up at [render.com](https://render.com) and click **New Web Service**
3. Connect your GitHub repository
4. Configure the service:
   - **Root Directory:** `finguard-ai/backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables in Render dashboard (see §8.4):
   - `DATABASE_URL` — your cloud PostgreSQL URL
   - `GEMINI_API_KEY`
   - `FRONTEND_URL` — your Vercel frontend URL (e.g. `https://finguard.vercel.app`)
   - `ENVIRONMENT` — `production`
6. Deploy — Render will build and start the service automatically

The backend will be accessible at `https://your-app-name.onrender.com`.

> **Note:** Render free tier spins down after 15 minutes of inactivity. The first request after sleep may take 30–60 seconds to respond.

---

### 8.3 Frontend — Vercel

[Vercel](https://vercel.com) is the simplest way to deploy a Vite/React app.

1. Push your code to GitHub
2. Sign up at [vercel.com](https://vercel.com) and click **Add New Project**
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset:** Vite
   - **Root Directory:** `finguard-ai/frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Set environment variable:
   - `VITE_API_URL` — your Render backend URL + `/api/v1`, e.g. `https://finguard-backend.onrender.com/api/v1`
6. Click **Deploy**

Vercel auto-deploys on every push to the main branch.

---

## 9. Environment Variables per Platform

| Variable | Local `.env` | Render | Vercel |
|----------|-------------|--------|--------|
| `DATABASE_URL` | ✅ | ✅ | ❌ |
| `GEMINI_API_KEY` | ✅ | ✅ | ❌ |
| `FRONTEND_URL` | ✅ | ✅ | ❌ |
| `BACKEND_URL` | ✅ | ✅ | ❌ |
| `ENVIRONMENT` | ✅ | ✅ | ❌ |
| `VITE_API_URL` | ✅ (`frontend/.env.local`) | ❌ | ✅ |

> On Render and Vercel, set these through each platform's environment variables UI — **never** commit secret values to source control.

---

## 10. Health Check

The backend exposes a lightweight liveness probe:

```
GET /health
```

**Response:**
```json
{"status": "ok", "version": "1.0.0"}
```

Use this endpoint for:
- Uptime monitoring (UptimeRobot, Better Uptime, etc.)
- Load balancer health checks
- Docker `HEALTHCHECK` directive

**Example Docker health check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

---

## 11. Production Checklist

Before deploying to production, verify each item:

### Security
- [ ] `DEBUG=false` — verbose logging and stack traces must be disabled
- [ ] `ENVIRONMENT=production` — ensures production-mode behaviour
- [ ] `GEMINI_API_KEY` is set via environment variable, never hardcoded
- [ ] `DATABASE_URL` includes `sslmode=require` for cloud PostgreSQL
- [ ] `.env` is listed in `.gitignore` and has never been committed

### CORS
- [ ] `FRONTEND_URL` is set to the exact production frontend origin (e.g. `https://finguard.vercel.app`)
- [ ] Wildcard CORS (`allow_origins=["*"]`) is **not** used in production
- [ ] The `allow_origins` list in [`main.py`](../backend/main.py) does not contain `http://localhost:*` in production

### Performance
- [ ] Backend is started with multiple workers: `uvicorn main:app --workers 4`
- [ ] Database connection pool is sized appropriately for expected load
- [ ] Render (or equivalent) plan supports the expected concurrent request volume

### Authentication
- [ ] If the app is publicly accessible, add JWT authentication before exposing it (see [API docs §5](./api.md#5-authentication))
- [ ] Admin/internal endpoints are not publicly reachable without authentication

### Data
- [ ] Production database migrations have been run
- [ ] ML model artifact (`ml/artifacts/risk_classifier.pkl`) has been trained and is available on the server, or the rule-based fallback is explicitly accepted
- [ ] Seed data is NOT loaded into production — only real financial data should be present

### Monitoring
- [ ] `/health` endpoint is monitored by an uptime checker
- [ ] Application logs are collected (Render Logs, Datadog, etc.)
- [ ] Gemini API quota usage is monitored in Google AI Studio
