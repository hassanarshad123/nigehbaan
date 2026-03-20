# System Architecture

## Nigehbaan — Technical Architecture Document

**Version:** 1.0
**Date:** March 19, 2026

---

## 1. System Topology

### Full Stack Overview

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
```

### Data Pipeline

```
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

### Deployment Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Vercel     │────>│   EC2 (FastAPI)  │────>│  Neon DB      │
│  (Next.js)   │     │  t3.large        │     │  (PostgreSQL  │
│  Free -> Pro │     │  Ubuntu 22.04    │     │   + PostGIS)  │
└──────────────┘     │                  │     │  Free -> Pro  │
                     │  FastAPI (8000)  │     └───────────────┘
                     │  Celery Worker   │
                     │  Celery Beat     │     ┌───────────────┐
                     │  Redis           │     │  S3 Bucket    │
                     │                  │────>│  (Raw PDFs,   │
                     └──────────────────┘     │   photos)     │
                                              └───────────────┘
```

---

## 2. Tech Stack

### Frontend

| Technology | Version | Purpose | Rationale |
|-----------|---------|---------|-----------|
| Next.js | 14+ | Application framework | App Router with Server Components, ISR for district profiles, native Vercel deployment |
| Mapbox GL JS | Latest | Map rendering | Supports 11K+ point rendering, custom dark styles, vector tiles, free tier (50K loads/mo) |
| Deck.gl | Latest | Advanced map layers | PathLayer for route animation, HeatmapLayer for incident density, ScatterplotLayer for kilns |
| react-map-gl | Latest | React wrapper for Mapbox | Declarative map components, controlled state, event handling |
| Recharts | Latest | Dashboard charts | Composable chart components, responsive, good React integration |
| Tailwind CSS | 3.x | Styling | Utility-first, dark mode support, small bundle size |
| shadcn/ui | Latest | UI component library | Accessible, customizable, built on Radix primitives |
| Zustand | Latest | State management | Lightweight, no boilerplate, ideal for map state (layers, filters, viewport) |
| NextAuth.js | Latest | Authentication | Admin/government portal login, multiple providers |
| next-intl | Latest | Internationalization | English + Urdu (RTL) + Sindhi, message-based translations |
| next-pwa | Latest | Progressive Web App | Offline cached district profiles, helpline numbers, install prompt |

### Backend

| Technology | Version | Purpose | Rationale |
|-----------|---------|---------|-----------|
| FastAPI | 0.109+ | API framework | Async support, auto-generated OpenAPI docs, Python ecosystem for NLP/geo |
| SQLAlchemy | 2.0+ | ORM | Async support with asyncpg, PostGIS via GeoAlchemy2 |
| GeoAlchemy2 | 0.14+ | Spatial ORM | PostGIS column types, spatial queries in Python |
| asyncpg | 0.29+ | Async PostgreSQL driver | High-performance async database access for FastAPI |
| Alembic | 1.13+ | Database migrations | Version-controlled schema changes |
| Celery | 5.3+ | Task queue | Scheduled scraping, PDF processing, geocoding background tasks |
| Redis | 5.0+ | Message broker + cache | Celery broker, API response caching |
| spaCy | 3.7+ | NLP | Named Entity Recognition for news/court text processing |
| Scrapy | 2.11+ | Web scraping | Standard website crawling (news RSS, government pages) |
| Playwright | 1.40+ | Browser automation | JavaScript-heavy sites (Geo News, Balochistan HC portal) |
| pdfplumber | 0.10+ | PDF table extraction | Sahil Cruel Numbers tables, FIA reports, court judgments |
| tabula-py | 2.9+ | PDF table extraction (backup) | Fallback for tables pdfplumber handles poorly |
| GeoPandas | 0.14+ | Geospatial data processing | Shapefile/GeoJSON loading, spatial joins, transformations |
| Pydantic | 2.5+ | Data validation | Request/response schemas, settings management |
| uvicorn | 0.27+ | ASGI server | Production-grade async server for FastAPI |

### Database

| Technology | Version | Purpose | Rationale |
|-----------|---------|---------|-----------|
| PostgreSQL | 16+ | Relational database | Robust, mature, excellent geospatial support via PostGIS |
| PostGIS | 3.4+ | Spatial extension | Spatial indexing, geographic queries, geometry types |
| Neon | Managed | Hosting | Serverless scaling, free tier for development, branching for CI/CD |

### Infrastructure

| Technology | Purpose | Rationale |
|-----------|---------|-----------|
| Vercel | Frontend hosting | Free tier, edge CDN, native Next.js support, preview deployments |
| AWS EC2 (t3.large) | Backend hosting | 2 vCPU, 8 GB RAM for FastAPI + Celery + spaCy NLP model |
| AWS S3 | Object storage | Raw PDFs, scraped HTML, processed CSVs, photo uploads |
| Let's Encrypt | SSL certificates | Free HTTPS for backend API |
| Nginx | Reverse proxy | SSL termination, request routing, static file serving |

---

## 3. Data Flow Diagrams

### 3.1 Scraping Pipeline Flow

```
   Schedule triggers (Celery Beat)
              │
              ▼
   ┌─────────────────────┐
   │   Source Selection   │
   │  (RSS/HTML/PDF/API)  │
   └──────────┬──────────┘
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
 ┌──────┐ ┌──────┐ ┌──────┐
 │Scrapy│ │Playw.│ │ API  │
 │spider│ │fetch │ │client│
 └──┬───┘ └──┬───┘ └──┬───┘
    │        │        │
    └────────┼────────┘
             ▼
   ┌──────────────────┐
   │  S3 Raw Storage   │
   │  (audit trail)    │
   └────────┬─────────┘
            │
   ┌────────┼────────────┐
   ▼        ▼            ▼
┌──────┐ ┌──────┐  ┌────────┐
│PDF   │ │HTML  │  │CSV/JSON│
│parser│ │parser│  │loader  │
└──┬───┘ └──┬───┘  └───┬────┘
   │        │          │
   └────────┼──────────┘
            ▼
   ┌──────────────────┐
   │  NER + Geocoder   │
   │  (spaCy + gazet)  │
   └────────┬─────────┘
            ▼
   ┌──────────────────┐
   │ PostgreSQL+PostGIS│
   │  (normalized)     │
   └──────────────────┘
```

### 3.2 User Request Flow

```
   User browser
        │
        ▼
   ┌──────────┐
   │  Vercel   │  (Next.js SSR/ISR)
   │  CDN Edge │
   └────┬─────┘
        │ API call
        ▼
   ┌──────────┐
   │  Nginx    │  (SSL termination, rate limiting)
   │  proxy    │
   └────┬─────┘
        │
        ▼
   ┌──────────┐
   │  FastAPI  │  (request validation, auth check)
   │  uvicorn  │
   └────┬─────┘
        │
        ▼
   ┌──────────┐
   │  Neon     │  (PostGIS spatial query)
   │  PostgreSQL│
   └────┬─────┘
        │
        ▼
   JSON/GeoJSON response
   (through same chain back to user)
```

### 3.3 Report Submission Flow

```
   Citizen opens /report
        │
        ▼
   Multi-step form
   (category -> location -> date -> details -> contact)
        │
        ▼
   POST /api/v1/reports
        │
        ▼
   ┌──────────────────┐
   │  Input Validation  │
   │  + EXIF stripping  │
   │  + rate limit check│
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Auto-geocode to  │
   │  district P-code   │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Store in DB       │
   │  (public_reports)  │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Return reference  │
   │  number + helplines│
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Admin review queue│
   │  (manual moderation│
   │   before display)  │
   └────────┬─────────┘
            │
            ▼
   Referred to appropriate agency
   (ZARRA, police, labour dept, CPB)
```

---

## 4. Backend Directory Structure

```
/backend
  /app
    /main.py                   -- FastAPI app initialization, CORS, middleware
    /config.py                 -- Environment variables, database connection settings
    /models/                   -- SQLAlchemy ORM models
      /boundaries.py           -- Administrative boundaries (admin 0-3)
      /incidents.py            -- Master incidents table
      /brick_kilns.py          -- Brick kiln point data
      /court_judgments.py       -- Court case records
      /vulnerability.py        -- District vulnerability indicators
      /public_reports.py       -- Citizen-submitted reports
      /news_articles.py        -- Scraped news with NER extraction
    /schemas/                  -- Pydantic request/response schemas
      /incidents.py
      /reports.py
      /dashboard.py
      /map.py
    /api/
      /v1/
        /map.py                -- Map data endpoints (boundaries, kilns, routes, heatmap)
        /dashboard.py          -- Dashboard aggregation endpoints
        /districts.py          -- District profiles and details
        /reports.py            -- Public report submission and status
        /legal.py              -- Court judgment search and statistics
        /search.py             -- Full-text search across all data
        /export.py             -- CSV and GeoJSON export
    /services/
      /geocoder.py             -- Pakistan-specific geocoding (gazetteer lookup)
      /nlp_pipeline.py         -- spaCy NER for news/court text extraction
      /risk_scorer.py          -- Composite vulnerability score calculator
      /spatial_analysis.py     -- PostGIS query builders for spatial operations
    /scrapers/                 -- Celery task definitions for data ingestion
      /sahil_scraper.py        -- Sahil PDF download and extraction
      /tip_report_scraper.py   -- US State Dept TIP Report HTML scraper
      /news_scraper.py         -- RSS and full-text news article scraper
      /court_scrapers/         -- One module per court system
        /scp.py                -- Supreme Court (CommonLII bulk)
        /lhc.py                -- Lahore High Court
        /shc.py                -- Sindh High Court (5 benches)
        /phc.py                -- Peshawar High Court (4 benches)
        /bhc.py                -- Balochistan High Court (Playwright)
        /ihc.py                -- Islamabad High Court (ASP.NET)
      /police_scrapers/        -- Provincial police data
        /punjab.py
        /sindh.py
    /tasks/
      /celery_app.py           -- Celery configuration and broker settings
      /schedule.py             -- Celery Beat periodic task schedule
    /utils/
      /gazetteer.py            -- Pakistan gazetteer loader (3000+ locations)
      /pdf_extractor.py        -- pdfplumber/tabula wrapper with fallback logic
      /name_normalizer.py      -- District name fuzzy matching via crosswalk table
```

---

## 5. Frontend Directory Structure

```
/frontend
  /app
    /page.tsx                    -- Landing page (hero, counters, CTAs)
    /layout.tsx                  -- Root layout (dark theme, fonts, providers)
    /map
      /page.tsx                  -- Full-screen interactive map
      /components
        /MapContainer.tsx        -- Mapbox GL wrapper with viewport state
        /LayerControls.tsx       -- Toggle panel for map layers
        /DistrictPopup.tsx       -- Click-on-district info card
        /IncidentTimeline.tsx    -- Time slider for temporal filtering
        /SearchBar.tsx           -- Location + incident search
    /dashboard
      /page.tsx                  -- Trend analysis dashboard
      /components
        /TrendCharts.tsx         -- Recharts 15-year time series
        /ProvinceComparison.tsx  -- Province grouped bar charts
        /CaseTypeBreakdown.tsx   -- Donut/pie charts by incident type
        /ConvictionRates.tsx     -- Prosecution vs. conviction trend
        /SummaryCounters.tsx     -- Animated top-level statistics
    /report
      /page.tsx                  -- Multi-step incident reporting form
      /success/page.tsx          -- Submission confirmation with reference number
    /district/[pcode]
      /page.tsx                  -- "Know Your District" profile
    /legal
      /page.tsx                  -- Court judgment search and analytics
    /resources
      /page.tsx                  -- Helplines, legal aid, shelters directory
    /about
      /page.tsx                  -- Project mission and methodology
    /api                         -- Next.js API routes (proxy to FastAPI)
  /components                   -- Shared UI components
    /ui/                         -- shadcn/ui primitives
    /layout/                     -- Header, footer, sidebar, navigation
  /lib                           -- Utilities, API client, hooks
  /public                        -- Static assets (icons, images)
  /messages                      -- i18n translation files (en.json, ur.json)
```

---

## 6. Database Architecture

### Extensions Required

```sql
CREATE EXTENSION postgis;           -- Spatial types and functions
CREATE EXTENSION pg_trgm;           -- Trigram similarity for fuzzy text search
CREATE EXTENSION unaccent;          -- Accent-insensitive search
```

### Core Tables

The database contains 12 primary tables organized into three tiers:

**Geographic Foundation:**
- `boundaries` — Administrative boundaries (levels 0-3) with PostGIS geometry, P-codes as universal join key
- `district_name_variants` — Crosswalk table for fuzzy district name matching
- `brick_kilns` — 11K+ geolocated brick kiln points from Zenodo
- `border_crossings` — International border crossing points with vulnerability scores

**Incident & Intelligence Data:**
- `incidents` — Master normalized table aggregating all sources (Sahil, SSDO, CTDC, news, courts)
- `court_judgments` — Structured court case records with NLP-extracted fields
- `news_articles` — Scraped news with NER-extracted entities and geographic references
- `tip_report_annual` — 24-year time series of TIP Report enforcement data
- `trafficking_routes` — Constructed route geometries with evidence sources
- `vulnerability_indicators` — Per-district, per-year composite vulnerability data

**User-Generated:**
- `public_reports` — Citizen-submitted incident reports with moderation workflow
- `data_sources` — Registry tracking freshness and health of all data sources

### Indexing Strategy

- **Spatial indexes** (GiST) on all geometry columns for fast geographic queries
- **B-tree indexes** on P-codes, years, incident types, and source types for filtered queries
- **GIN indexes** on JSONB columns and text arrays for full-text and array containment queries
- **Composite indexes** on (district_pcode, year) for time-series queries

Full schema definitions are in [DATA_DICTIONARY.md](DATA_DICTIONARY.md) and [MASTER.md](../MASTER.md) Section 7.

---

## 7. Security Architecture

### Transport Security

- **Frontend:** HTTPS via Vercel (automatic SSL)
- **Backend API:** HTTPS via Nginx + Let's Encrypt
- **Database:** SSL connections enforced by Neon (managed)
- **Internal:** All EC2 services communicate over localhost

### Application Security

| Threat | Mitigation |
|--------|------------|
| SQL Injection | SQLAlchemy parameterized queries; no raw SQL from user input |
| XSS (Cross-Site Scripting) | Next.js built-in output escaping; Content-Security-Policy headers |
| CSRF (Cross-Site Request Forgery) | SameSite cookies; CSRF token validation on state-changing requests |
| Rate Limiting | Nginx rate limiting (10 req/sec public); FastAPI middleware for fine-grained control |
| File Upload Attacks | File type validation (whitelist: JPEG, PNG); EXIF metadata stripping; max 5MB size limit |
| Data Exposure | No individual victim data displayed; minimum aggregation at district level |
| Reporter Identification | IP hashing (SHA-256, not stored raw); optional contact info encrypted (AES-256) |
| Dependency Vulnerabilities | Dependabot/Snyk automated scanning; monthly dependency audits |

### Server Hardening (EC2)

- UFW firewall: only ports 80, 443, 22 open
- fail2ban for SSH brute-force protection
- SSH key-only authentication (password disabled)
- Non-root application user with minimal permissions
- Automatic security updates enabled

### Data Ethics

- No data that could identify individual victims is displayed publicly
- All victim data aggregated to district level minimum
- Reporter contact information encrypted at rest (AES-256)
- Photo uploads stripped of EXIF metadata before storage
- Reports moderated before public display
- Full methodology documented and publicly available
- Confidence scores on all NLP-extracted data points

---

## 8. Deployment

### Environments

| Environment | Frontend | Backend | Database |
|-------------|----------|---------|----------|
| Development | `localhost:3000` | `localhost:8000` | Local PostgreSQL + PostGIS via Docker |
| Staging | Vercel Preview | EC2 staging instance | Neon branch |
| Production | Vercel Production | EC2 production | Neon main branch |

### Docker Compose (Development)

```yaml
services:
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: nigehbaan
      POSTGRES_USER: nigehbaan
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file: .env

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
    env_file: .env

volumes:
  pgdata:
```

### Production EC2 Process Management

- **uvicorn** (FastAPI) managed by systemd service
- **Celery worker** managed by systemd service (2 concurrent workers)
- **Celery Beat** managed by systemd service (scheduler)
- **Redis** managed by systemd (or ElastiCache for production scale)
- **Nginx** as reverse proxy with SSL termination

### Monitoring

| Concern | Tool | Tier |
|---------|------|------|
| Uptime | UptimeRobot | Free |
| Error tracking | Sentry | Free tier |
| Logs | CloudWatch | AWS included |
| Database | Neon dashboard | Built-in |
| Scraper health | Celery Flower | Self-hosted |
| Performance | Vercel Analytics | Free tier |

### Cost Estimate (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| Vercel | Free (hobby) to Pro ($20) | $0-20 |
| EC2 t3.large | On-demand | ~$60 |
| Neon PostgreSQL | Free (0.5 GB) to Launch ($19) | $0-19 |
| S3 (50 GB storage) | Standard | ~$1 |
| Mapbox | Free (50K map loads) | $0 |
| Domain (.pk) | Annual | ~$10/year |
| **Total MVP** | | **$60-100/month** |

---

*For the complete master blueprint, see [MASTER.md](../MASTER.md). For API endpoint details, see [API_SPEC.md](API_SPEC.md). For data source details, see [DATA_DICTIONARY.md](DATA_DICTIONARY.md).*
