# NomosFlow — AI-Powered Dunning & Churn Prevention Engine

> Full-stack internal ops dashboard for white-label energy retailers. Powered by Gemini AI.

## Stack
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Gemini 1.5 Flash
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + TypeScript

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL running locally

### 2. Backend Setup

```bash
cd backend

# Copy and fill in env
cp .env.example .env
# Edit .env: set DATABASE_URL and GEMINI_API_KEY

# Install dependencies
pip install -r requirements.txt

# Create the database
createdb nomosflow

# Run migrations
alembic upgrade head

# Seed with demo data (3 partners, 25 customers, payments)
python -m app.seed.seed

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 3. Frontend Setup

```bash
cd frontend

# Copy env
cp .env.local.example .env.local

# Install dependencies
npm install

# Start dev server
npm run dev
```

App available at: http://localhost:3000

---

## Features

| Feature | Description |
|---|---|
| **Dashboard** | KPI cards, critical risk alerts, recent payments |
| **Customers** | Filterable table, slide-out drawer with full profile + dunning timeline |
| **Dunning Queue** | Failed/retrying payments; one-click AI cycle trigger |
| **AI Retention** | Gemini-generated personalised retention emails per at-risk customer |
| **Partners** | White-label OEM partner overview with brand preview |

## Environment Variables

### Backend (`.env`)
| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google Gemini API key |

### Frontend (`.env.local`)
| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (default: `http://localhost:8000`) |
