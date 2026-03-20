# Nigehbaan Infrastructure Reference

> Last updated: 2026-03-20

---

## 1. System Overview

```
                     +------------------+
                     |   Vercel (CDN)   |
                     |  Next.js 14 SSR  |
                     +--------+---------+
                              |
                     NEXT_PUBLIC_API_URL
                              |
                    +---------v----------+       +-------------------+
                    |   EC2 (Mumbai)     |       |   RDS (Mumbai)    |
                    |   Docker Compose   +-------> PostgreSQL 16.6   |
                    |                    |       |   PostGIS 3.4     |
                    |  - FastAPI (8000)  |       |   db.t3.micro     |
                    |  - Celery Worker   |       +-------------------+
                    |  - Celery Beat     |
                    |  - Redis 7         |       +-------------------+
                    |                    |       |   Neon (READ ONLY)|
                    |                    +-------> Court Judgments DB |
                    +--------------------+       +-------------------+
```

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | Next.js 14, Mapbox GL JS, next-intl | Map-based dashboard (English/Urdu) |
| Backend API | FastAPI, SQLAlchemy, asyncpg | REST API, data aggregation |
| Task Queue | Celery + Redis 7 | Scheduled scraping & processing |
| Primary DB | PostgreSQL 16.6 + PostGIS (RDS) | All platform data |
| Judgments DB | PostgreSQL (Neon) | Court judgments import (READ ONLY) |
| CI/CD | GitHub Actions | Lint, test, deploy to EC2 |
| Hosting | Vercel (frontend), AWS EC2 (backend) | Production hosting |

---

## 2. AWS Resources

### EC2 Instance

| Property | Value |
|----------|-------|
| Instance ID | `i-0ea8784163afa6f4e` |
| Type | `t3.medium` (2 vCPU, 4 GB RAM) |
| Region | `ap-south-1` (Mumbai) |
| VPC | `vpc-0452aff859766bf46` |
| Subnet | `subnet-0891bdca4ee7ff850` |
| Elastic IP | `13.205.224.14` (`eipalloc-04e9bdffb47aeabb9`) |
| Private IP | `172.31.3.108` |
| OS | Ubuntu (latest LTS) |
| Key Pair | `child-traffing.pem` |
| Deploy Path | `/home/ubuntu/nigehbaan/` |
| Swap | 2 GB (`/swapfile`) |

### RDS Instance

| Property | Value |
|----------|-------|
| Identifier | `nigehbaan-db` |
| Engine | PostgreSQL 16.6 |
| Class | `db.t3.micro` |
| Storage | 20 GB (encrypted) |
| Endpoint | `nigehbaan-db.c5i8iasqgtzx.ap-south-1.rds.amazonaws.com:5432` |
| Database | `nigehbaan` |
| User | `nigehbaan` |
| Subnet Group | `ict-lms-subnet-group` |
| Multi-AZ | No |
| VPC SG | `sg-0d9fbc36ed4e00a66` |

### Security Groups

**EC2 SG (`sg-09f66c521e6348ddd` / `launch-wizard-3`)**

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | `117.102.54.212/32` | SSH (restricted) |
| 8000 | TCP | `0.0.0.0/0` | FastAPI |

**RDS SG (`sg-0d9fbc36ed4e00a66`)**

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 5432 | TCP | EC2 SG / VPC CIDR | PostgreSQL |

### Elastic IP

| Property | Value |
|----------|-------|
| Allocation ID | `eipalloc-04e9bdffb47aeabb9` |
| Association ID | `eipassoc-097668d49c8461ac8` |
| Public IP | `13.205.224.14` |

---

## 3. Access

### SSH

```bash
ssh -i child-traffing.pem ubuntu@13.205.224.14
```

### Database (via EC2 or psql)

```bash
# From EC2 (inside Docker)
sudo docker exec -it nigehbaan-api python -c "import psycopg2; ..."

# Direct psql (from EC2)
psql -h nigehbaan-db.c5i8iasqgtzx.ap-south-1.rds.amazonaws.com -U nigehbaan -d nigehbaan
```

### API

```
Health:    http://13.205.224.14:8000/health
Dashboard: http://13.205.224.14:8000/api/v1/dashboard/summary
Scrapers:  http://13.205.224.14:8000/api/v1/scrapers/summary
Docs:      http://13.205.224.14:8000/docs
```

### Admin Panel

```
URL:      https://nigehbaan.vercel.app/admin
Default:  admin@nigehbaan.org / changeme  (CHANGE IMMEDIATELY)
```

---

## 4. GitHub

| Property | Value |
|----------|-------|
| Repository | `hassanarshad123/nigehbaan` |
| Branch | `master` |

### Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push/PR to master | Lint (ruff, ESLint), test (pytest), build (Next.js, Docker) |
| `deploy-backend.yml` | After CI passes on master | SSH to EC2, pull, write .env.production, rebuild Docker |
| `security-check.yml` | Weekly Mon 09:00 UTC | pip-audit + npm audit, creates issues |

### GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `DATABASE_URL` | RDS connection string (asyncpg) |
| `EC2_HOST` | `13.205.224.14` (Elastic IP) |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Private key for SSH deploy |
| `SECRET_KEY` | FastAPI session secret |
| `CORS_ORIGINS` | Allowed CORS origins |
| `OPENAI_API_KEY` | GPT-4o-mini for AI extraction |
| `EXTERNAL_JUDGMENTS_DB_URL` | Neon DB for court judgments import |

---

## 5. Vercel

| Property | Value |
|----------|-------|
| Project | `zensbots-project/nigehbaan` |
| URL | `https://nigehbaan.vercel.app` |
| Framework | Next.js 14 |

### Environment Variables

| Variable | Environment | Purpose |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Production | `http://13.205.224.14:8000` |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | All | Mapbox GL JS map rendering |
| `NEXTAUTH_URL` | All | NextAuth.js base URL |
| `NEXTAUTH_SECRET` | All | NextAuth.js session encryption |

---

## 6. Database Schema

**Alembic Version:** `003`

| Table | Rows | Purpose |
|-------|------|---------|
| `boundaries` | 745 | Admin boundaries (PostGIS MULTIPOLYGON) |
| `brick_kilns` | 11,272 | Brick kiln locations (Zenodo dataset) |
| `incidents` | 333 | Trafficking/exploitation incidents |
| `news_articles` | 476 | Scraped news articles |
| `data_sources` | 32 | Scraper registry and status |
| `vulnerability_indicators` | 121 | District vulnerability scores |
| `border_crossings` | 15 | Border crossing points |
| `trafficking_routes` | 8 | Known trafficking routes |
| `public_reports` | 1 | Public-submitted reports |
| `court_judgments` | 0 | Court judgment data (pending import) |
| `district_name_variants` | 0 | Name normalization lookup |
| `statistical_reports` | 0 | Statistical report data (new, migration 002) |
| `transparency_reports` | 0 | Transparency report data (new, migration 002) |
| `tip_report_annual` | 0 | TIP report annual data |

### Migrations

| Version | Description |
|---------|-------------|
| 001 | Initial schema (12 tables, PostGIS, indexes) |
| 002 | Add statistical_reports and transparency_reports tables |
| 003 | Add court_judgments unique constraint (source_url) + is_trafficking_related index |

---

## 7. Docker Services

All services defined in `docker-compose.prod.yml`, using `.env.production`.

| Container | Image | Port | Memory Limit | Purpose |
|-----------|-------|------|-------------|---------|
| `nigehbaan-redis` | `redis:7-alpine` | 6379 (internal only) | 256 MB | Task broker + result backend |
| `nigehbaan-api` | `nigehbaan-api` | `0.0.0.0:8000` | 512 MB | FastAPI (2 Uvicorn workers) |
| `nigehbaan-celery-worker` | `nigehbaan-api` | — | 768 MB | Celery worker (concurrency=2, queues: celery, scraping, processing) |
| `nigehbaan-celery-beat` | `nigehbaan-api` | — | 128 MB | Celery beat scheduler |

### Commands

```bash
# SSH to EC2
ssh -i child-traffing.pem ubuntu@13.205.224.14

# View running containers
sudo docker ps

# View logs
sudo docker logs nigehbaan-api --tail=50 -f
sudo docker logs nigehbaan-celery-worker --tail=50 -f

# Restart all
cd /home/ubuntu/nigehbaan
sudo docker compose -f docker-compose.prod.yml down
sudo docker compose -f docker-compose.prod.yml up -d

# Rebuild after code change
sudo docker compose -f docker-compose.prod.yml build
sudo docker compose -f docker-compose.prod.yml up -d

# Run Alembic migration
sudo docker exec -w /app/backend nigehbaan-api alembic upgrade head

# Health check
curl -sf http://localhost:8000/health
```

---

## 8. Scrapers

32 active data sources organized by category:

### News (7 scrapers, every 6h)

| Scraper | Schedule | Records |
|---------|----------|---------|
| `rss_monitor` (Google News RSS) | Every 6h (xx:00) | 1,600 |
| `dawn` | Every 6h (xx:15) | 10 |
| `tribune` (Express Tribune) | Every 6h (xx:30) | 115 |
| `the_news` | Every 6h (xx:45) | 20 |
| `ary_news` | 4x/day (01,07,13,19:00) | 2 |
| `geo_news` | 4x/day (01,07,13,19:15) | 13 |
| `news_js` (Jang/Samaa) | Daily 02:30 | — |

### Urdu News (4 scrapers, 4x/day)

| Scraper | Schedule | Records |
|---------|----------|---------|
| `jang_urdu` | 4x/day (02,08,14,20:00) | — |
| `express_urdu` | 4x/day (02,08,14,20:15) | — |
| `bbc_urdu` | 4x/day (02,08,14,20:30) | — |
| `geo_urdu` | 4x/day (02,08,14,20:45) | — |

### Courts (6 scrapers, weekly Sunday)

| Scraper | Schedule | Records |
|---------|----------|---------|
| `court_scp` | Sun 01:00 | 0 |
| `court_lhc` | Sun 01:15 | — |
| `court_shc` | Sun 01:30 | 0 |
| `court_phc` | Sun 01:45 | 0 |
| `court_bhc` | Sun 02:00 | 0 |
| `court_ihc` | Sun 02:15 | 0 |

### Government/Police (5 scrapers)

| Scraper | Schedule | Records |
|---------|----------|---------|
| `police_punjab` | Monthly 15th | 0 |
| `police_sindh` | Monthly 15th | 0 |
| `police_kp` | Monthly 15th | — |
| `police_balochistan` | Monthly 15th | — |
| `stateofchildren` (NCRC) | Monthly 1st | 66 |

### International APIs (2 scrapers, quarterly)

| Scraper | Schedule | Records |
|---------|----------|---------|
| `worldbank_api` | Quarterly (Jan,Apr,Jul,Oct) | 1,002 |
| `unhcr_api` | Quarterly | 166 |

### CSA & Child Protection (6 scrapers)

| Scraper | Schedule |
|---------|----------|
| `sahil` | Annually (Jan) |
| `ecpat` | Annually (Jan) |
| `pahchaan` | Quarterly |
| `unicef_pakistan` | Quarterly |
| `ncrc` | Annually |
| `cpwb_punjab` | Quarterly |

### Online Exploitation (7 scrapers)

| Scraper | Schedule |
|---------|----------|
| `ncmec` | Annually (Jan) |
| `iwf_reports` | Annually (Jan) |
| `meta_transparency` | Semi-annual (Jan, Jul) |
| `google_transparency` | Semi-annual (Jan, Jul) |
| `drf_newsletters` | Monthly |
| `weprotect_gta` | Annually |
| `bytes_for_all` | Annually |

### Child Labor (5 scrapers)

| Scraper | Schedule |
|---------|----------|
| `ilostat_api` | Quarterly |
| `dol_annual_report` | Annually (Oct) |
| `dol_tvpra` | Annually (Oct) |
| `labour_surveys` | Annually |
| `zenodo_kilns` | Annually (one-time) |
| `bllf` | Annually |
| `brick_kiln_dashboard` | Quarterly |

### Cross-border (2 scrapers)

| Scraper | Schedule |
|---------|----------|
| `ctdc_dataset` | Quarterly |
| `brookings_bride` | Annually |

### Other Registered Sources (no scraper scheduled)

| Source | Type |
|--------|------|
| HDX Administrative Boundaries | Spatial |
| HDX Population Estimates | Demographic |
| Pakistan Census 2017 (CERP) | Demographic |
| Zenodo Brick Kiln Dataset | Geospatial |
| SSDO Child Protection Reports | Report |
| MoHR ZARRA Reports | Government |
| KP CPWC | Government |
| Lahore High Court (LHC) | Court |
| CommonLII Court Decisions | Court |
| US DOL ILAB | International |
| US State Dept TIP Report | International |
| UNODC Data Portal | International |
| OSM Border Crossings | Geospatial |
| UNOSAT Flood Extent | Geospatial |
| Walk Free GSI | International |

---

## 9. Data Pipeline

```
[Celery Beat] ──schedule──> [Celery Worker]
                                  |
                          ┌───────┴────────┐
                          v                v
                   [News Scrapers]   [API Scrapers]
                          |                |
                          v                v
                   news_articles      data_sources
                          |           (record_count++)
                          v
                   [AI Extractor]
                   (GPT-4o-mini)
                          |
                          v
                     incidents
                   (geocoded, typed)
                          |
                          v
                   [Risk Scorer]
                   vulnerability_indicators
```

1. **Scrape**: Celery Beat triggers scraping tasks on schedule
2. **Persist**: Raw data saved to `news_articles`, `data_sources` updated
3. **Extract**: AI extractor (GPT-4o-mini) processes articles into structured incidents
4. **Geocode**: Geocoding task resolves locations to district pcodes
5. **Score**: Risk scorer calculates district vulnerability indicators

---

## 10. Environment Variables

### Backend (.env.production)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | RDS PostgreSQL connection (asyncpg driver) |
| `REDIS_URL` | Redis connection (`redis://redis:6379/0` in Docker) |
| `SECRET_KEY` | FastAPI session/JWT secret |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `OPENAI_API_KEY` | OpenAI API key for AI extraction |
| `OPENAI_MODEL` | Model name (`gpt-4o-mini`) |
| `EXTERNAL_JUDGMENTS_DB_URL` | Neon DB for court judgments (READ ONLY) |
| `S3_BUCKET` | S3 bucket name (`nigehbaan-data`) |
| `AWS_ACCESS_KEY_ID` | AWS credentials for S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for S3 |
| `AWS_REGION` | AWS region (`ap-south-1`) |
| `MAPBOX_TOKEN` | Mapbox access token |

### Frontend (Vercel)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox GL JS token |
| `NEXTAUTH_URL` | NextAuth base URL |
| `NEXTAUTH_SECRET` | NextAuth session secret |

---

## 11. Monitoring & Recovery

### Health Checks

```bash
# API health
curl -sf http://13.205.224.14:8000/health

# Docker container status
ssh -i child-traffing.pem ubuntu@13.205.224.14 "sudo docker ps"

# Memory usage
ssh ... "free -h"

# Disk usage
ssh ... "df -h"

# Celery worker status
ssh ... "sudo docker exec nigehbaan-celery-worker celery -A app.tasks.celery_app inspect active"
```

### Log Access

```bash
# API logs
sudo docker logs nigehbaan-api --tail=100 -f

# Worker logs (scraper output)
sudo docker logs nigehbaan-celery-worker --tail=100 -f

# Beat logs (schedule)
sudo docker logs nigehbaan-celery-beat --tail=50 -f
```

### Restart Procedures

```bash
# Full restart
cd /home/ubuntu/nigehbaan
sudo docker compose -f docker-compose.prod.yml down
sudo docker compose -f docker-compose.prod.yml up -d

# Single service restart
sudo docker restart nigehbaan-api
sudo docker restart nigehbaan-celery-worker
```

### Rollback

The deploy workflow does not auto-rollback. Manual rollback:
```bash
cd /home/ubuntu/nigehbaan
git log --oneline -5           # find the good commit
git checkout <commit-hash>     # checkout it
sudo docker compose -f docker-compose.prod.yml build
sudo docker compose -f docker-compose.prod.yml up -d
```

---

## 12. Cost Breakdown (Monthly Estimate)

| Resource | Type | Estimated Cost |
|----------|------|---------------|
| EC2 | t3.medium (on-demand) | ~$30/mo |
| RDS | db.t3.micro (on-demand) | ~$15/mo |
| Elastic IP | Associated | $0 (free when associated) |
| EBS | 8 GB gp3 (EC2) | ~$1/mo |
| RDS Storage | 20 GB gp2 | ~$2/mo |
| Data Transfer | ~5 GB/mo est. | ~$1/mo |
| **Total** | | **~$49/mo** |

Vercel: Free tier (hobby plan).

---

## 13. Troubleshooting

### API returns 502/Connection Refused

1. Check if container is running: `sudo docker ps`
2. Check logs: `sudo docker logs nigehbaan-api --tail=50`
3. Verify port mapping: `sudo docker port nigehbaan-api`
4. Restart: `sudo docker restart nigehbaan-api`

### Scrapers Not Running

1. Check beat is running: `sudo docker ps | grep beat`
2. Check worker logs: `sudo docker logs nigehbaan-celery-worker --tail=50`
3. Verify Redis: `sudo docker exec nigehbaan-redis redis-cli ping`
4. Check schedule: Review `backend/app/tasks/schedule.py`

### Database Connection Failed

1. Verify RDS is running: `aws rds describe-db-instances --db-instance-identifier nigehbaan-db`
2. Check security group allows EC2 → RDS on port 5432
3. Test from EC2: `psql -h nigehbaan-db.c5i8iasqgtzx.ap-south-1.rds.amazonaws.com -U nigehbaan -d nigehbaan`
4. Check `.env.production` DATABASE_URL is correct

### CORS Errors on Frontend

1. Verify `CORS_ORIGINS` in EC2 `.env.production` includes the Vercel domain
2. Restart API after changing: `sudo docker restart nigehbaan-api`
3. Check browser console for the exact origin being blocked

### Out of Memory

1. Check: `free -h` (swap should show 2 GB)
2. Check container memory: `sudo docker stats --no-stream`
3. If swap missing: `sudo swapon /swapfile`
4. Consider upgrading to t3.large if persistent

### Frontend Shows No Data

1. Verify `NEXT_PUBLIC_API_URL` is set on Vercel: `vercel env ls`
2. Test API directly: `curl http://13.205.224.14:8000/api/v1/dashboard/summary`
3. Check browser Network tab for failed requests
4. Redeploy Vercel if env var was just added: `vercel --prod`

### CI/CD Deploy Fails

1. Check GitHub Actions run: `gh run list -R hassanarshad123/nigehbaan`
2. Verify secrets: `gh secret list -R hassanarshad123/nigehbaan`
3. Ensure `EC2_HOST` matches Elastic IP (`13.205.224.14`)
4. Ensure SSH key (`EC2_SSH_KEY`) matches the EC2 key pair
