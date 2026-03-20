# Nigehbaan (نگہبان) — Pakistan Child Trafficking Intelligence Platform

> **"The Guardian Who Watches Over"**

[![License: Private](https://img.shields.io/badge/License-Private-red.svg)]()
[![Status: Pre-Development](https://img.shields.io/badge/Status-Pre--Development-yellow.svg)]()
[![Platform: Pakistan](https://img.shields.io/badge/Platform-Pakistan-green.svg)]()

## Overview

Pakistan has an estimated **2.35 million people trapped in modern slavery** (Walk Free Foundation, 2023), ranking 4th globally in prevalence. Data on child trafficking exists across 90+ sources in 3 languages, locked in PDFs, scattered across federal agencies, provincial governments, and dozens of NGOs — not geocoded, not cross-referenced, not actionable.

**Nigehbaan** is a unified data intelligence platform that aggregates every publicly available data point on child trafficking in Pakistan into one normalized database, geo-maps every incident and vulnerability indicator onto an interactive map at district resolution (160 districts, 577 tehsils), and empowers government, NGOs, and citizens with the intelligence they need to protect Pakistan's children.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Vercel)                     │
│              Next.js 14+ (App Router)                   │
│   Mapbox GL JS / Deck.gl — Recharts — Tailwind CSS     │
│         shadcn/ui — Next-Auth — PWA Support             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / REST + WebSocket
┌──────────────────────┴──────────────────────────────────┐
│                   BACKEND (EC2)                          │
│                  FastAPI (Python)                        │
│   SQLAlchemy ORM — Celery (task queue) — Redis          │
│   spaCy NLP — scikit-learn — GeoPandas — pdfplumber     │
└──────────────────────┬──────────────────────────────────┘
                       │ SQL / Connection Pool
┌──────────────────────┴──────────────────────────────────┐
│                 DATABASE (Neon)                          │
│           PostgreSQL + PostGIS Extension                 │
│     Spatial indexing — JSONB for flexible schemas        │
│          Full-text search (tsvector/tsquery)             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  DATA PIPELINE (EC2)                     │
│   Scrapy spiders — Playwright (JS sites) — Celery Beat  │
│   pdfplumber/Tabula — spaCy NER — Geocoding pipeline    │
│              Schedule: daily/weekly/monthly              │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│                 OBJECT STORAGE (S3)                      │
│       Raw PDFs — Scraped HTML — Processed CSVs          │
│              Source archives for audit trail             │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Node.js | 20+ |
| Python | 3.11+ |
| pnpm | 9+ |
| Docker & Docker Compose | Latest |
| PostgreSQL + PostGIS | 16+ with PostGIS 3.4+ |

## Quickstart

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repo-url> nigehbaan
cd nigehbaan

# Copy environment template
cp .env.example .env
# Edit .env with your actual values (Mapbox token, database URL, etc.)

# Start all services
docker compose up -d

# Frontend available at http://localhost:3000
# Backend API at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Option 2: Manual Setup

**Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
# Open http://localhost:3000
```

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

**Database:**

```bash
# Ensure PostgreSQL is running with PostGIS extension
psql -U postgres -c "CREATE DATABASE nigehbaan;"
psql -U postgres -d nigehbaan -c "CREATE EXTENSION postgis;"

# Run migrations
cd backend
alembic upgrade head
```

## Monorepo Structure

| Directory | Purpose | Tech |
|-----------|---------|------|
| `frontend/` | Web application — map, dashboard, reporting portal | Next.js 14+, Mapbox GL JS, Tailwind CSS, shadcn/ui |
| `backend/` | REST API, task queue, NLP pipeline, scrapers | FastAPI, Celery, spaCy, SQLAlchemy |
| `data/` | Data ingestion scripts, raw downloads, processing | Python scripts, GeoPandas, pdfplumber |
| `shared/` | Shared types, constants, configuration | TypeScript types, Python schemas |
| `docs/` | Project documentation | Markdown |

## Key Documentation

| Document | Description |
|----------|-------------|
| [PRD](docs/PRD.md) | Product Requirements Document — problem statement, personas, features |
| [ROADMAP](docs/ROADMAP.md) | Phased development plan (4 phases, 24 weeks) |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | System architecture, tech stack rationale, deployment |
| [DATA_DICTIONARY](docs/DATA_DICTIONARY.md) | All 90+ data sources with schemas, URLs, and priority tiers |
| [API_SPEC](docs/API_SPEC.md) | Complete API endpoint specification with request/response schemas |
| [DESIGN_SYSTEM](docs/DESIGN_SYSTEM.md) | Dark intelligence theme — colors, typography, components |
| [MASTER.md](MASTER.md) | Master blueprint — the single source of truth for the entire project |

## Core Capabilities

- **Interactive Geo-Intelligence Map** — Heat maps, 11K+ brick kiln markers, trafficking routes, border crossings, toggleable layers
- **Trend Analysis Dashboard** — 15-year longitudinal data, province comparisons, conviction rates
- **Pattern Detection Engine** — Spatial clustering, correlation analysis, vulnerability scoring
- **Public Reporting Portal** — Anonymous incident reporting with GPS, photo upload, and referral system
- **Legal Intelligence Module** — Court judgment search, conviction rate mapping, sentencing analysis

## License

Private. All rights reserved.

## Built By

**Hassan Arshad** / [Zensbot](https://zensbot.com)

*For Pakistan's children.*
