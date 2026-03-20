# Nigehbaan Data Pipeline

## Architecture

```
Scheduler (APScheduler / cron)
    |
    v
Scrapers / Downloaders
    |
    v
Raw Storage (S3 / local: data/raw/)
    |
    v
Parsers (PDF extraction, HTML parsing)
    |
    v
NER + Geocoder (spaCy, Pakistan gazetteer)
    |
    v
Database (PostgreSQL + PostGIS)
```

## Pipeline Flow

1. **Scheduler** triggers scrapers/downloaders on their defined schedule (see `config/sources.yaml`).
2. **Scrapers** fetch data from live sources (news sites, court portals, government pages, international APIs).
3. **Downloaders** pull one-time or infrequent bulk datasets (GeoJSON boundaries, CSV datasets, PDF reports).
4. **Raw data** is stored in S3 (or local `data/raw/`) with timestamped keys for full audit trail.
5. **Parsers** extract structured data from PDFs, HTML, and CSV files.
6. **NER pipeline** identifies geographic entities, victim demographics, and crime types from unstructured text.
7. **Geocoder** resolves place names to coordinates using the Pakistan district gazetteer (`config/gazetteer/pakistan_districts.json`).
8. **Database** loader inserts validated, geocoded records into PostgreSQL with PostGIS geometry columns.

## Running Scrapers Manually

```bash
# Run a single scraper
python -m data.scrapers.news.dawn_scraper

# Run all news scrapers
python -m data.scrapers.news

# Run a downloader
python -m data.downloaders.hdx_boundaries

# Run a parser on downloaded PDFs
python -m data.parsers.sahil_parser --year 2024
```

## Configuration

All data sources are registered in `data/config/sources.yaml`. Each entry includes:

- `name`: Human-readable source name
- `url`: Source URL
- `priority`: P0/P1/P2/P3 tier
- `type`: Category (geographic_foundation, crime_statistics, etc.)
- `format`: Data format (GeoJSON, CSV, PDF, HTML, API)
- `scraper`: Python module that handles this source
- `schedule`: Cron expression or null for one-time downloads
- `geographic_granularity`: Spatial resolution (national, province, district, point)
- `fields`: Key fields extracted

## Priority Tiers

| Tier | Description | Action | Examples |
|------|-------------|--------|----------|
| **P0** | Foundation data required before anything else | Download immediately | HDX admin boundaries, census population |
| **P1** | Core crime/trafficking data for MVP | Implement scrapers first | Sahil reports, court judgments, TIP report |
| **P2** | Enrichment data that adds analytical depth | Implement after P1 | World Bank indicators, flood extent, brick kilns |
| **P3** | Nice-to-have or experimental sources | Backlog | Social media, dark web monitoring |

## Directory Structure

```
data/
  scrapers/
    base_scraper.py          # Abstract base class
    news/                    # Pakistani news outlet scrapers
    courts/                  # Court judgment scrapers (SCP, LHC, SHC, PHC, BHC, IHC)
    government/              # Government portal scrapers
    international/           # International org scrapers (TIP, DOL, UNODC, etc.)
  downloaders/               # One-time/bulk dataset downloaders
  parsers/                   # PDF and document parsers
  config/
    sources.yaml             # Master source registry
    gazetteer/               # Pakistan geographic name resolution
      pakistan_districts.json # District crosswalk with name variants
```
