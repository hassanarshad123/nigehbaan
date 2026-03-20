# Nigehbaan Data Sources & Scraper Specification

**Version**: 1.0
**Purpose**: Authoritative reference for building every scraper, parser, and data loader in the Nigehbaan pipeline. Contains URLs, selectors, field mappings, libraries, schedules, challenges, and target database tables — enough detail for Claude Code to implement each scraper without further research.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [P0 Downloaders — Foundation Data](#2-p0-downloaders--foundation-data)
3. [P1 PDF Parsers — Civil Society & Government Reports](#3-p1-pdf-parsers--civil-society--government-reports)
4. [News Scrapers](#4-news-scrapers)
5. [Court Scrapers](#5-court-scrapers)
6. [Government & Police Scrapers](#6-government--police-scrapers)
7. [International API Scrapers](#7-international-api-scrapers)
8. [NEW Sources Found Via Research](#8-new-sources-found-via-research)
9. [NLP & Geocoding Pipeline](#9-nlp--geocoding-pipeline)
10. [Celery Schedule Reference](#10-celery-schedule-reference)
11. [Database Target Reference](#11-database-target-reference)
12. [Implementation Sequence](#12-implementation-sequence)

---

## 1. Architecture Overview

### Three-Tier Pipeline

```
FETCHERS (Tier 1)          PARSERS (Tier 2)           STORAGE (Tier 3)
─────────────────          ────────────────           ─────────────────
Downloaders (one-time) ──► CSV/JSON Loaders    ──┐
Scrapers (recurring)   ──► PDF Parsers (plumber) │──► NER/Geocoder ──► Neon PostGIS
API Clients (REST)     ──► HTML Parsers (BS4)  ──┘
```

All raw data is saved to S3 (`raw/{scraper_name}/{run_id}.{format}`) before parsing, creating an immutable audit trail.

### BaseScraper Contract

**File**: `data/scrapers/base_scraper.py`

All scrapers inherit `BaseScraper` and implement:

| Method | Signature | Description |
|--------|-----------|-------------|
| `scrape()` | `async -> list[dict]` | Execute scraping logic, return raw records |
| `validate()` | `(record: dict) -> bool` | Validate a single record |
| `save_raw()` | `async (data, format) -> str` | Save to S3, return S3 key |
| `log_run()` | `async (count, status, error) -> None` | Log run to `data_sources` table |
| `run()` | `async -> None` | Full pipeline: scrape → validate → save → log |

Class attributes: `name`, `source_url`, `schedule` (cron), `priority` (P0-P3).

### BaseCourtScraper Extension

**File**: `data/scrapers/courts/base_court_scraper.py`

Extends `BaseScraper` with court-specific methods:

| Method | Description |
|--------|-------------|
| `search_cases(year, case_type)` | Search court portal |
| `download_judgment(case_ref)` | Download judgment PDF |
| `extract_metadata(case_ref)` | Extract structured metadata |
| `filter_relevant_cases(cases)` | Filter by PPC sections of interest |

PPC sections of interest: `366-A`, `366-B`, `369`, `370`, `371-A`, `371-B`, `377`, `292-A`, `292-B`, `292-C`

### Shared Utilities

| Utility | File | Role |
|---------|------|------|
| `PakistanGeocoder` | `backend/app/services/geocoder.py` | Gazetteer lookup + Nominatim fallback |
| `TraffickingNLPPipeline` | `backend/app/services/nlp_pipeline.py` | 20 keywords, keyword density classification, spaCy NER |
| `SahilParser` | `data/parsers/sahil_parser.py` | 21 crime categories, per-year extraction, pdfplumber + tabula |
| `CourtJudgmentParser` | `data/parsers/court_judgment_parser.py` | PPC regex, case header, victim demographics |
| `NewsArticleParser` | `data/parsers/news_article_parser.py` | 11 crime types, spaCy NER, gazetteer geocoding |

---

## 2. P0 Downloaders — Foundation Data

These are one-time downloads (annual refresh at most). No recurring scraping needed.

### 2.1 HDX Administrative Boundaries (COD-AB)

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/hdx_boundaries.py` |
| **URL** | `https://data.humdata.org/dataset/cod-ab-pak` |
| **Format** | GeoJSON / Shapefile |
| **Download steps** | 1. Navigate to dataset page 2. Download GeoJSON for admin levels 0-3 3. Load into PostGIS with GeoPandas |
| **Library** | `geopandas`, `requests` |
| **Target table** | `boundaries` |
| **Field mapping** | `ADM0_EN` → `name_en`, `ADM0_PCODE` → `pcode`, `geometry` → `geometry` (MULTIPOLYGON, SRID 4326). Repeat for ADM1-ADM3. Set `admin_level` = 1-4 based on file. |
| **Spatial ops** | Create GIST index on geometry. Build `district_name_variants` crosswalk from name fields. |
| **Validation** | Expect 7 provinces, ~44 divisions, ~160 districts, ~577 tehsils. Every polygon must have a valid P-code. |
| **Schedule** | One-time. Annual re-download when OCHA updates. |

### 2.2 Pakistan Census 2017 (CERP)

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/census_2017.py` |
| **URL** | `https://github.com/cerp-analytics/pbs2017` |
| **Format** | CSV (GitHub repo) |
| **Download steps** | 1. `git clone https://github.com/cerp-analytics/pbs2017` 2. Read CSVs with pandas 3. Join to `boundaries` using district names via `district_name_variants` crosswalk |
| **Library** | `pandas`, `subprocess` (for git clone) |
| **Target table** | `boundaries` (population columns) |
| **Field mapping** | `population_total` → `population_total`, `population_male` → `population_male`, `population_female` → `population_female`, `urban` → `population_urban`, `rural` → `population_rural` |
| **Validation** | National total should approximate 207.68M. Every district must match a boundary P-code. |
| **Schedule** | One-time. |

### 2.3 HDX Population Statistics (COD-PS)

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/hdx_population.py` |
| **URL** | `https://data.humdata.org/dataset/cod-ps-pak` |
| **Format** | CSV / XLSX |
| **Download steps** | 1. Download from HDX 2. Parse with pandas 3. Join to `boundaries` via P-code (pre-matched) |
| **Library** | `pandas`, `openpyxl`, `requests` |
| **Target table** | `boundaries` (population columns) |
| **Field mapping** | `ADM_PCODE` → join key to `boundaries.pcode`, `T_TL` → `population_total`, `T_MA` → `population_male`, `T_FE` → `population_female` |
| **Validation** | P-codes must exist in `boundaries`. Population figures > 0. |
| **Schedule** | One-time. Annual refresh. |

### 2.4 Zenodo Brick Kilns

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/zenodo_kilns.py` |
| **URL** | `https://zenodo.org/records/14038648` |
| **Format** | GeoJSON (~11.8 MB) |
| **Download steps** | 1. Find GeoJSON download link on Zenodo record page 2. Download with requests 3. Load with GeoPandas 4. Spatial join with `boundaries` (admin level 4 / district) to assign `district_pcode` |
| **Library** | `geopandas`, `requests` |
| **Target table** | `brick_kilns` |
| **Field mapping** | `latitude/longitude` → `geometry` (POINT, SRID 4326), `kiln_type` → `kiln_type`, `nearest_school_dist_m` → `nearest_school_m`, `nearest_hospital_dist_m` → `nearest_hospital_m`, `population_1km` → `population_1km` |
| **Spatial ops** | Spatial join: `ST_Within(kiln.geometry, boundary.geometry)` to assign `district_pcode`. Calculate `brick_kiln_count` and `brick_kiln_density_per_sqkm` per district for `vulnerability_indicators`. |
| **Validation** | Expect ~11,000 points. All points within Pakistan bounding box (24-37°N, 61-77°E). |
| **Schedule** | One-time. |

### 2.5 CTDC Victims Dataset

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/ctdc_victims.py` |
| **URL** | `https://www.ctdatacollaborative.org/page/global-synthetic-dataset` |
| **GitHub** | `https://github.com/UNMigration/HTCDS` |
| **Format** | CSV |
| **Download steps** | 1. Download CSV from CTDC or clone GitHub repo 2. Filter: `country_of_exploitation == 'Pakistan' OR victim_citizenship == 'Pakistan'` 3. Map to incidents table |
| **Library** | `pandas`, `requests` |
| **Target table** | `incidents` |
| **Field mapping** | `victim_gender` → `victim_gender`, `victim_age` → `victim_age_min`/`victim_age_max`, `exploitation_type` → `incident_type`, `means_of_control` → `sub_type`, `route_origin` → used for `trafficking_routes` |
| **Validation** | Expect ~48,800 observations globally; Pakistan subset ~500-2000 rows. Each record must have exploitation_type. |
| **Schedule** | One-time + quarterly refresh. Celery: `ctdc_updater`. |

### 2.6 Walk Free Global Slavery Index

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/walkfree_gsi.py` |
| **URL** | `https://www.walkfree.org/global-slavery-index/downloads/` |
| **Country PDF** | `https://cdn.walkfree.org/content/uploads/2023/09/27164917/GSI-Snapshot-Pakistan.pdf` |
| **Format** | CSV/Excel + PDF |
| **Download steps** | 1. Download country-level dataset (CSV/Excel) 2. Extract Pakistan row 3. Download Pakistan snapshot PDF, parse 23 vulnerability indicators |
| **Library** | `pandas`, `pdfplumber`, `requests` |
| **Target table** | `vulnerability_indicators` |
| **Field mapping** | `gsi_score` → context data, `estimated_prevalence` → context data. 23 vulnerability indicators map to various `vulnerability_indicators` columns. |
| **Validation** | Pakistan should show ~2.35M estimated in modern slavery. |
| **Schedule** | One-time. Check biennially for updates. |

### 2.7 UNOSAT 2022 Flood Extent

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/flood_extent.py` |
| **URL** | `https://data.humdata.org/dataset/satellite-detected-water-extents-between-01-and-29-august-2022-over-pakistan` |
| **Format** | Shapefile |
| **Download steps** | 1. Download shapefile from HDX 2. Load with GeoPandas 3. Spatial intersection with `boundaries` to calculate `flood_affected_pct` per district |
| **Library** | `geopandas`, `requests` |
| **Target table** | `vulnerability_indicators` → `flood_affected_pct` |
| **Spatial ops** | `ST_Intersection(flood_polygon, district_polygon)` → area ratio = `flood_affected_pct` |
| **Validation** | Flood polygons should cover primarily Sindh and southern Punjab. |
| **Schedule** | One-time. |

### 2.8 OSM Border Crossings (Geofabrik)

| Field | Value |
|-------|-------|
| **File** | `data/downloaders/osm_borders.py` |
| **URL** | `https://download.geofabrik.de/asia/pakistan.html` |
| **Format** | Shapefile (330 MB for full extract) |
| **Download steps** | 1. Download Pakistan Shapefile from Geofabrik 2. Filter for `barrier=border_control` points 3. Load into PostGIS |
| **Library** | `geopandas`, `requests` |
| **Target table** | `border_crossings` |
| **Field mapping** | `name` → `name`, `lat/lon` → `geometry` (POINT), infer `border_country` from proximity to AF/IR/IN/CN boundaries |
| **Spatial ops** | Calculate `distance_to_border_km` for each district for `vulnerability_indicators`. |
| **Validation** | Expect ~13 official crossings (8 Afghanistan, 4 Iran, 1 India). |
| **Schedule** | One-time + optional monthly refresh. |

### 2.9 GADM Boundaries (Backup)

| Field | Value |
|-------|-------|
| **URL** | `https://gadm.org/download_country.html` (select Pakistan) |
| **Format** | GeoPackage / Shapefile |
| **Purpose** | Backup/validation for HDX boundaries. Up to 5 admin levels. |
| **Target table** | Not directly loaded; used for QA cross-reference. |
| **License** | Non-commercial free. |
| **Schedule** | One-time. |

### 2.10 UNICEF Child Marriage Data

| Field | Value |
|-------|-------|
| **URL** | `https://childmarriagedata.org/country-profiles/pakistan/` |
| **Format** | Interactive dashboard (scrape or find download) |
| **Key data** | 18% married before 18 nationally; Balochistan 49.1%, Punjab 29.8% |
| **Library** | `requests`, `beautifulsoup4` (or download underlying data) |
| **Target table** | `vulnerability_indicators` → `child_marriage_rate` |
| **Field mapping** | Provincial child marriage rates → `child_marriage_rate` per province/district |
| **Schedule** | One-time. |

### 2.11 World Bank API (Foundation Indicators)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/international/worldbank_api.py` |
| **API** | `https://api.worldbank.org/v2/country/PAK/indicator/{code}?format=json&per_page=100` |
| **Format** | JSON REST API |
| **14 Indicator codes** | `NY.GDP.PCAP.CD` (GDP/capita), `SI.POV.NAHC` (poverty national), `SI.POV.DDAY` (poverty $2.15/day), `SE.PRM.ENRR` (primary enrollment), `SE.SEC.ENRR` (secondary enrollment), `SE.PRM.CMPT.ZS` (primary completion), `SE.ADT.LITR.ZS` (literacy total), `SE.ADT.LITR.FE.ZS` (literacy female), `SP.POP.TOTL` (population), `SP.POP.0014.TO.ZS` (population 0-14%), `SL.TLF.0714.WK.ZS` (child employment 7-14%), `SP.DYN.IMRT.IN` (infant mortality), `SH.STA.BRTC.ZS` (skilled birth attendance), `SP.URB.TOTL.IN.ZS` (urban %) |
| **Library** | `httpx` (async), `requests` |
| **Target table** | `vulnerability_indicators` |
| **Field mapping** | Each indicator maps to a specific column: `SE.PRM.ENRR` → `school_enrollment_rate`, `SI.POV.NAHC` → `poverty_headcount_ratio`, `SE.ADT.LITR.ZS` → `literacy_rate`, `SL.TLF.0714.WK.ZS` → `child_labor_rate`, `SP.URB.TOTL.IN.ZS` → context data |
| **Validation** | API returns `[metadata, [datapoints]]`. Check `metadata.total` > 0. Years should span 1960-present. |
| **Schedule** | Quarterly. Celery: `worldbank_api`. |

---

## 3. P1 PDF Parsers — Civil Society & Government Reports

### 3.1 Sahil "Cruel Numbers" Reports (2010-2024)

**Parser file**: `data/parsers/sahil_parser.py`
**Priority**: P1 — Highest priority PDF extraction

#### All 16 Download URLs

| Year | URL |
|------|-----|
| 2024 | `https://drive.google.com/file/d/1hwjN8dKRfy6ZIqsL240sScCfNUlCLX-m/view` |
| 2023 | `https://sahil.org/wp-content/uploads/2024/03/Curel-Numbers-2023-Finalll.pdf` |
| 2022 | `https://sahil.org/wp-content/uploads/2023/05/Cruel-Numbers-2022-Email.pdf` |
| 2021 | `https://drive.google.com/file/d/1UVATKnqmgpX9K2W5p76o2AiRGsz4fg3n/view` |
| 2020 | `https://drive.google.com/file/d/1TKxMWYc2w_iwtWMpGDt4UYDvCTtEPA0n/view` |
| 2019 | `https://sahil.org/wp-content/uploads/2020/03/Cruel-Numbers-2019-final.pdf` |
| 2018 | `https://drive.google.com/file/d/1EmISbZNQ7v6bRVUc4VwsoThbXPUzs7Xd/view` |
| 2017 | `https://sahil.org/wp-content/uploads/2018/04/Cruel-Numbers-Report-2017-1.pdf` |
| 2016 | `https://sahil.org/wp-content/uploads/2017/03/Cruel-numbers-Report-2016-Autosaved1-edited111.pdf` |
| 2015 | `https://sahil.org/wp-content/uploads/2016/04/Final-Cruel-Numbers-2015-16-03-16.pdf` |
| 2014 | `https://sahil.org/wp-content/uploads/2015/04/Cruel-Numbers-2014.pdf` |
| 2013 | `https://sahil.org/wp-content/uploads/2014/06/Cruel-Number-2013.pdf` |
| 2012 | `https://sahil.org/wp-content/uploads/2014/09/Cruel-Number-2012.pdf` |
| 2011 | `https://sahil.org/wp-content/uploads/2015/11/Creul-Number-2011.pdf` |
| 2010 | `https://sahil.org/wp-content/uploads/2015/11/cruel-numbers-2010.pdf` |
| 5-Year (2007-2011) | `https://sahil.org/wp-content/uploads/2014/09/FIVE-YEAR-ANALYSIS-200-2011.pdf` |

**Note**: Google Drive URLs require conversion: replace `/view` with export format or use `gdown` library.

#### Three Format Eras

| Era | Years | Layout characteristics |
|-----|-------|-----------------------|
| Era 1 | 2010-2014 | Simple tables, fewer categories, basic layout |
| Era 2 | 2015-2019 | More crime categories, urban/rural split added, improved formatting |
| Era 3 | 2020-2024 | Modern layout, comprehensive breakdown, age brackets refined |

#### 21 Standardized Crime Categories

```python
CRIME_CATEGORIES = [
    "abduction", "kidnapping", "missing_children", "child_sexual_abuse",
    "sodomy", "gang_sodomy", "rape", "gang_rape", "attempt_sexual_abuse",
    "child_pornography", "child_marriage", "child_labour",
    "child_domestic_labour", "child_trafficking", "physical_abuse",
    "murder", "attempt_murder", "acid_attack", "honor_killing",
    "medical_negligence", "abandonment",
]
```

#### Data Structure Per Report

Each report contains 10-15 key tables:
- **Total cases by crime category** (21 categories)
- **Province-wise breakdown**: Punjab, Sindh, KP, Balochistan, ICT, AJK, GB
- **Urban vs. rural split**
- **Victim gender**: male / female
- **Victim age brackets**: 0-5, 6-10, 11-15, 16-18
- **Abuser profile**: acquaintance, stranger, family member, service provider, neighbor, teacher
- **Police registration rates** (FIR filed vs. not)
- **Location type** where abuse occurred

#### Volume Trajectory (for validation)

| Year | Total cases |
|------|-------------|
| 2010 | 2,388 |
| 2013 | 3,002 |
| 2016 | 4,139 |
| 2018 | 3,832 |
| 2022 | 4,253 |
| 2023 | 4,213 |
| 2024 | 7,608 (SSDO figure) |

#### Extraction Settings

```python
# pdfplumber settings for Sahil reports
TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "join_tolerance": 3,
    "edge_min_length": 3,
    "min_words_vertical": 1,
    "min_words_horizontal": 1,
}
# Fallback: tabula-py with lattice=True first, then stream=True
```

#### Output Schema

```python
{
    "year": int,
    "province": str,           # normalized to constants.json provinces
    "crime_category": str,     # from CRIME_CATEGORIES
    "victim_gender": str,      # "male" | "female" | "unknown"
    "victim_age_bracket": str,  # "0-5" | "6-10" | "11-15" | "16-18"
    "urban_rural": str,         # "urban" | "rural" | "unknown"
    "case_count": int,
    "fir_registered_count": int | None,
}
```

#### Target Table

**`incidents`** with `source_type = "sahil"`, `incident_type` mapped from `crime_category`.

#### Normalization Rules

- Province: "KP" / "KPK" / "Khyber Pakhtunkhwa" / "NWFP" → "Khyber Pakhtunkhwa" (PK02)
- Province: "AJK" / "Azad Kashmir" / "Azad Jammu & Kashmir" → PK07
- Categories: Map Urdu category names to English standardized names
- Validate extracted totals against published annual totals (±5% tolerance)

### 3.2 SSDO (Sustainable Social Development Organization) Reports

| Field | Value |
|-------|-------|
| **Parser file** | `data/parsers/ssdo_parser.py` (to create) |
| **URL** | `https://www.ssdo.org.pk/` |
| **Checker** | `data/scrapers/government/ssdo_checker.py` |
| **Format** | PDF reports + press releases |
| **Key 2024 data** | Total: 7,608. Sexual abuse (2,954), Kidnapping (2,437), Child labour (895), Physical abuse (683), Child trafficking (586), Child marriage (53) |
| **Provincial breakdown** | Punjab (6,083), KP (1,102), Sindh (354), ICT (138), Balochistan (69) |
| **Unique value** | Official police-sourced data with conviction rates (mostly under 1%) |
| **Extraction** | pdfplumber for tables. Check `/media/` and `/reports/` paths for new PDFs. |
| **Target table** | `incidents` with `source_type = "ssdo"` |
| **Schedule** | Monthly check: `0 3 20 * *` |

### 3.3 ZARRA Missing Children Reports

| Field | Value |
|-------|-------|
| **Parser file** | `data/parsers/zarra_parser.py` (to create) |
| **PDF URL** | `https://mohr.gov.pk/SiteImage/Misc/files/ZARRA%20Data%20Analysis%20Report%20Oct,%202021%20-%20June,%202022.pdf` |
| **URL pattern** | `mohr.gov.pk/SiteImage/Misc/files/ZARRA*` |
| **Key data** | 3,639 total cases; 2,130 closures; 592 open. District-level with geo-tags |
| **Provincial distribution** | Punjab ~72%, Sindh ~11%, KP ~3%, Balochistan ~2%, ICT ~6% |
| **Extraction** | pdfplumber. Extract district-level case counts. |
| **Target table** | `incidents` with `source_type = "zarra"` |
| **Checker** | `data/scrapers/government/mohr_checker.py` |
| **Schedule** | Monthly: `0 3 25 * *` |

### 3.4 US TIP Report (24+ Years)

| Field | Value |
|-------|-------|
| **Scraper file** | `data/scrapers/international/tip_report.py` |
| **URL pattern (post-2017)** | `https://www.state.gov/reports/{YEAR}-trafficking-in-persons-report/pakistan/` |
| **URL pattern (pre-2017)** | `https://2009-2017.state.gov/j/tip/rls/tiprpt/countries/...` |
| **Format** | Clean HTML country pages + full PDF reports |
| **Data per year** | Tier ranking, investigations, prosecutions, convictions (PTPA vs PPC), victims identified, budget |
| **2025 data** | 1,607 PTPA investigations (523 sex, 915 forced labor, 169 unspecified); 495 convictions; 23,629 PPC investigations; 19,954 victims identified |
| **Library** | `requests`, `beautifulsoup4` |
| **Selectors** | Country pages are clean HTML with standard paragraph/heading structure. Parse `<h3>` sections for Prosecution, Protection, Prevention. Extract numeric data via regex patterns. |
| **Target table** | `tip_report_annual` |
| **Field mapping** | `tier_ranking`, `ptpa_investigations`, `ptpa_prosecutions`, `ptpa_convictions`, `ptpa_sex_trafficking_inv`, `ptpa_forced_labor_inv`, `ppc_investigations`, `ppc_prosecutions`, `ppc_convictions`, `victims_identified`, `victims_referred`, `budget_allocated_pkr`, `key_findings`, `named_hotspots` |
| **Validation** | Should get 24+ rows (2001-2025). Each row must have year and tier_ranking. |
| **Schedule** | Annually in July: `0 4 1 7 *` |

### 3.5 US DOL Child Labor Report

| Field | Value |
|-------|-------|
| **Scraper file** | `data/scrapers/international/dol_child_labor.py` |
| **URL** | `https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan` |
| **PDF pattern** | `https://www.dol.gov/sites/dolgov/files/ILAB/child_labor_reports/tda{YEAR}/Pakistan.pdf` |
| **Key data** | Working children ages 10-14: 9.8% (2,261,704). Agriculture 69.4%, Services 19.7%, Industry 10.9% |
| **Library** | `requests`, `pdfplumber` |
| **Target table** | `vulnerability_indicators` (child labor indicators) |
| **Schedule** | Annually Q4: `0 3 15 10 *` |

### 3.6 NCSW/UNICEF Violence Against Children Mapping Study (2024)

| Field | Value |
|-------|-------|
| **URL** | `https://ngdp-ncsw.org.pk/storage/6865729cf1528.pdf` |
| **Key data** | District-level violence rates: 121 trafficking cases, 53 child marriage cases across 4 provinces |
| **Why critical** | Rare DISTRICT-LEVEL trafficking case data |
| **Library** | `pdfplumber` |
| **Target table** | `incidents` with `source_type = "ncsw_vac"` |
| **Schedule** | One-time download. |

### 3.7 FIA Annual Reports

| Field | Value |
|-------|-------|
| **URL** | `https://www.fia.gov.pk/` |
| **PDF paths** | `/files/publications/686234992.pdf` (2024), `/files/publications/1069384536.pdf` (2019), `/files/immigration/1815351109.pdf` (NAP) |
| **Data** | Case counts by year, deportee statistics, trafficking routes, AHTC personnel (781 staff) |
| **Challenge** | Server unstable (ConnectTimeout frequent). Implement retry with exponential backoff. |
| **Library** | `requests` (with retry), `pdfplumber` |
| **Target table** | `incidents` (case stats), `trafficking_routes` (route data) |
| **Schedule** | One-time download with retries. |

### 3.8 NCRC Annual Report

| Field | Value |
|-------|-------|
| **URL** | `https://ncrc.gov.pk/wp-content/uploads/2025/07/Annual-Report-24-25.pdf` |
| **Data** | First comprehensive State of Children report covering health, education, protection |
| **Library** | `pdfplumber` |
| **Target table** | `vulnerability_indicators`, `incidents` |
| **Schedule** | One-time + annual check. |

### 3.9 UK DFID Modern Slavery Report (2019)

| Field | Value |
|-------|-------|
| **URL** | `https://assets.publishing.service.gov.uk/media/5e56a35a86650c53b6909337/DFID_Modern_Slavery_in_Pakistan_.pdf` |
| **Data** | Sector-specific data (brick kilns, agriculture, domestic work), geographic hotspots |
| **Library** | `pdfplumber` |
| **Target table** | `vulnerability_indicators` (context data) |
| **Schedule** | One-time. |

### 3.10 Academic PDFs

| Source | URL | Key content |
|--------|-----|-------------|
| Aurat Foundation | `https://af.org.pk/gep/images/Research%20Studies%20(Gender%20Based%20Violence)/study%20on%20trafficking%20final.pdf` | Internal trafficking routes, victim profiles, district-level field data |
| SDPI Child Trafficking | `https://sdpi.org/sdpiweb/publications/files/2004-05.pdf` | Swat Valley community-level surveys |
| ECPAT Pakistan | `https://ecpat.org/wp-content/uploads/2022/03/Gobal-Boys-Initiative_Pakistan-Report_FINAL.pdf` | Hotspot identification (hotels, truck stops, shrines, mining) |
| ECPAT Supplementary | `https://pahchaan.info/wp-content/uploads/2025/05/Supplementary-report-on-Sexual-Exploitation-of-Children-in-Pakistan.pdf` | Prosecution data, legal framework |
| HRW 1995 Bonded Labor | `https://www.hrw.org/legacy/reports/1995/Pakistan.htm` | Named brick kiln sites (HTML, historical baseline) |
| HRCP Modern Slavery | `https://hrcp-web.org/hrcpweb/wp-content/uploads/2020/09/2022-Modern-slavery-1.pdf` | Province-by-province trafficking analysis |

**Library**: `requests`, `pdfplumber` for PDFs, `beautifulsoup4` for HRW HTML.
**Target table**: `incidents` (quantitative data), context/notes for qualitative data.

---

## 4. News Scrapers

All news scrapers inherit `BaseScraper`. They share a common keyword list for relevance filtering.

### Common Keyword List

```python
TRAFFICKING_KEYWORDS = [
    "child trafficking", "child abuse", "missing child", "kidnap", "abduct",
    "sexual abuse", "child labour", "child labor", "bonded labour", "brick kiln",
    "zina", "366-A", "370", "371", "FIA", "human trafficking", "child marriage", "minor",
]
```

### 4.1 Dawn Newspaper

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/dawn_scraper.py` |
| **Class** | `DawnScraper` |
| **RSS URL** | `https://dawn.com/feeds/home` |
| **Article body selector** | `<div class="story__content">` |
| **Author selector** | `<span class="story__byline">` |
| **Library** | `feedparser`, `aiohttp`, `beautifulsoup4` (Scrapy-compatible) |
| **Schedule** | Every 6 hours: `0 */6 * * *` |
| **Target table** | `news_articles` |
| **Notes** | Pakistan's oldest English newspaper. Clean, well-structured HTML. Most reliable source. |

### 4.2 Express Tribune

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/tribune_scraper.py` |
| **Class** | `TribuneScraper` |
| **RSS URL** | `https://tribune.com.pk/feed` |
| **Dedicated tag page** | `https://tribune.com.pk/child-trafficking/` |
| **Article body selector** | WordPress standard: `<div class="entry-content">` or `<div class="story-text">` |
| **Library** | `feedparser`, `requests`, `beautifulsoup4` |
| **Schedule** | Every 6 hours: `0 */6 * * *` |
| **Target table** | `news_articles` |
| **Notes** | WordPress-based. Has dedicated `/child-trafficking/` tag — crawl this for targeted historical articles. |

### 4.3 The News International

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/the_news_scraper.py` |
| **Class** | `TheNewsScraper` |
| **RSS URL** | `https://www.thenews.com.pk/rss` |
| **Article body selector** | `<div class="detail-content">` or similar Jang Group layout |
| **Library** | `feedparser`, `requests`, `beautifulsoup4` |
| **Schedule** | Every 6 hours: `0 */6 * * *` |
| **Target table** | `news_articles` |
| **Notes** | Part of Jang Group. Standard HTML, no JS rendering needed. |

### 4.4 ARY News

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/ary_scraper.py` |
| **Class** | `ARYScraper` |
| **RSS URL** | `https://arynews.tv/feed/` |
| **WP REST API** | `https://arynews.tv/wp-json/wp/v2/posts?search=child+trafficking` (fallback) |
| **Article body selector** | WordPress: `<div class="entry-content">` |
| **Library** | `feedparser`, `requests`, `beautifulsoup4` |
| **Schedule** | Every 6 hours: `0 */6 * * *` |
| **Target table** | `news_articles` |
| **Notes** | WordPress-based. Try WP REST API v2 for structured data with pagination. |

### 4.5 Geo News (Playwright Required)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/geo_scraper.py` |
| **Class** | `GeoScraper` |
| **Base URL** | `https://www.geo.tv` |
| **Search URL** | `https://www.geo.tv/search/{query}` |
| **Search queries** | `child trafficking`, `child abuse`, `missing children`, `kidnapping`, `bonded labour`, `human trafficking` |
| **Article body selector** | Extract from rendered DOM (JS-heavy, structure varies) |
| **Library** | `playwright` (headless Chromium) |
| **Schedule** | Daily: `0 2 * * *` (less frequent due to browser overhead) |
| **Target table** | `news_articles` |
| **Challenges** | Heavy JS rendering. No RSS feed. Requires Playwright. ~2-5s per page load. Block ads/trackers via request interception. |

### 4.6 Samaa TV (Playwright Required)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/samaa_scraper.py` (to create) |
| **Base URL** | `https://www.samaa.tv` |
| **Library** | `playwright` |
| **Schedule** | Daily: `0 2 * * *` (grouped with Geo News in `news_js` task) |
| **Target table** | `news_articles` |
| **Challenges** | Heavy JS rendering like Geo News. Grouped into `scrape_news_js` Celery task. |

### 4.7 Pakistan Today

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/pakistan_today_scraper.py` (to create) |
| **Base URL** | `https://www.pakistantoday.com.pk` |
| **RSS URL** | Likely WordPress: `https://www.pakistantoday.com.pk/feed/` |
| **Library** | `feedparser`, `requests`, `beautifulsoup4` |
| **Schedule** | Every 6 hours (group with other RSS scrapers) |
| **Target table** | `news_articles` |
| **Notes** | WordPress-based. Standard RSS approach. |

### 4.8 RSS Monitor (Google News + Multi-Feed Aggregator)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/news/rss_monitor.py` |
| **Class** | `RSSMonitor` |
| **Feeds monitored** | `google_news_trafficking`: Google News RSS (child+trafficking+Pakistan), `google_news_child_abuse`: Google News RSS (child+abuse+Pakistan), `google_news_missing_children`: Google News RSS (missing+children+Pakistan), plus Dawn, Tribune, The News, ARY feeds |
| **Library** | `feedparser`, `aiohttp` (concurrent feed fetching) |
| **Schedule** | Every 4 hours: `0 */4 * * *` |
| **Target table** | `news_articles` |
| **Deduplication** | Normalize URLs (strip UTM, resolve Google News redirects). Track `seen_urls` in Redis set for cross-process dedup. |
| **Notes** | Google News RSS aggregator is critical — captures articles from Urdu-language outlets and regional papers we don't have dedicated scrapers for. |

### News Scraper Output Schema

All news scrapers produce records conforming to:

```python
{
    "url": str,                  # → news_articles.url (UNIQUE)
    "title": str,                # → news_articles.title
    "source_name": str,          # → news_articles.source_name ("dawn", "tribune", etc.)
    "author": str | None,
    "published_date": date,      # → news_articles.published_date
    "full_text": str,            # → news_articles.full_text
    "tags": list[str] | None,
    "category": str | None,
}
```

After scraping, articles are queued for NLP processing via `run_nlp_pipeline` task, which populates `extracted_incidents`, `extracted_locations`, `extracted_entities`, `is_trafficking_relevant`, and `relevance_score`.

---

## 5. Court Scrapers

All court scrapers inherit `BaseCourtScraper`. **Critical limitation**: No Pakistani court allows searching by criminal offense. Strategy: search by case type (Criminal Appeal, Criminal Petition, etc.) then keyword-filter judgment text for relevant PPC sections.

### Relevant PPC Sections

| Section | Description |
|---------|-------------|
| 366-A | Kidnapping woman to compel marriage |
| 366-B | Importation of girl from foreign country |
| 369 | Kidnapping child under 10 |
| 370 | Buying/selling person for slavery |
| 371-A | Selling person for prostitution |
| 371-B | Buying person for prostitution |
| 377 | Unnatural offences |
| 292-A/B/C | Child pornography (PECA 2016) |

### Relevant Statutes

- Prevention of Trafficking in Persons Act 2018 (PTPA)
- Zainab Alert, Response and Recovery Act 2020
- Punjab Destitute and Neglected Children Act 2004
- Bonded Labour System (Abolition) Act 1992
- Prevention of Smuggling of Migrants Act 2018

### 5.1 Supreme Court of Pakistan (SCP)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/courts/scp.py` |
| **Class** | `SCPScraper` |
| **Portal URL** | `https://supremecourt.nadra.gov.pk/judgement-search/` |
| **Tech stack** | Standard HTML forms, NADRA infrastructure |
| **Search strategy** | POST form with parameters: year, case_type ("Criminal Appeal", "Criminal Petition", "Human Rights Case") |
| **Result parsing** | HTML `<table>` rows. Columns: case number, date, parties, result. Use BeautifulSoup. |
| **PDF download** | Direct download links from search results table |
| **Rate limiting** | 2-second delay between requests. Max 100 requests/session. |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `court_judgments` |
| **Schedule** | Weekly Sunday: `0 1 * * 0` |

### 5.2 Lahore High Court (LHC)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/courts/lhc.py` |
| **Portal URL** | `https://data.lhc.gov.pk/reported_judgments/` |
| **Tech stack** | Standard HTML, `data.lhc.gov.pk` subdomain |
| **Search strategy** | Browse by year, case type. Keyword filter in case title. |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `court_judgments` |
| **Schedule** | Weekly Sunday: `0 1 * * 0` (15 min offset) |
| **Notes** | Punjab's high court. Highest case volume of all courts. |

### 5.3 Sindh High Court (SHC)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/courts/shc.py` |
| **Portal URL** | `https://cases.shc.gov.pk` |
| **5 Benches** | Karachi (`/khi`), Sukkur (`/suk`), Hyderabad (`/hyd`), Larkana (`/lar`), Mirpurkhas (`/mpkhas`) |
| **Search strategy** | Must iterate ALL 5 benches separately. Same form structure per bench. |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `court_judgments` (with `court_bench` populated) |
| **Schedule** | Weekly Sunday: `0 1 * * 0` (30 min offset) |

### 5.4 Peshawar High Court (PHC)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/courts/phc.py` |
| **Portal URL** | `https://peshawarhighcourt.gov.pk/app/site/15/p/Search_For_Case.html` |
| **4 Benches** | Peshawar, Abbottabad, Mingora, D.I. Khan |
| **Search strategy** | Iterate all 4 benches. HTML form submission. |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `court_judgments` |
| **Schedule** | Weekly Sunday: `0 1 * * 0` (45 min offset) |

### 5.5 Balochistan High Court (BHC)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/courts/bhc.py` |
| **Portal URL** | `https://portal.bhc.gov.pk/case-status/` |
| **Tech stack** | SPA (Single Page Application) — **requires Playwright** |
| **Search strategy** | Playwright browser automation to interact with SPA. Fill form fields, click search, wait for results to render. |
| **Library** | `playwright` |
| **Target table** | `court_judgments` |
| **Schedule** | Weekly Sunday: `0 2 * * 0` |
| **Challenges** | SPA requires full browser rendering. JS-generated content. May have CAPTCHA. |

### 5.6 Islamabad High Court (IHC)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/courts/ihc.py` |
| **Portal URL** | `https://mis.ihc.gov.pk/frmCseSrch` |
| **Tech stack** | ASP.NET with ViewState |
| **Search strategy** | Must handle ASP.NET ViewState/EventValidation hidden fields. Extract `__VIEWSTATE`, `__VIEWSTATEGENERATOR`, `__EVENTVALIDATION` from form, submit POST with these fields + search params. |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `court_judgments` |
| **Schedule** | Weekly Sunday: `0 2 * * 0` (15 min offset) |
| **Challenges** | ASP.NET ViewState can be large (>100KB). Must maintain session cookies. |

### 5.7 CommonLII (Historical Archive)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/courts/commonlii.py` |
| **Portal URL** | `https://www.commonlii.org/resources/245.html` |
| **Tech stack** | Static HTML, no JS, no auth |
| **Search strategy** | Bulk crawl. Use Scrapy for efficient crawling of all Pakistan court decisions. Keyword search for trafficking terms. |
| **Library** | `scrapy` (bulk crawl) |
| **Target table** | `court_judgments` |
| **Schedule** | Monthly: `0 3 1 * *` |
| **Notes** | FREE. Historical judgments not on individual court portals. Start here for Phase 1. |

### 5.8 District Courts (Punjab & Sindh)

| Court | URL | Notes |
|-------|-----|-------|
| Punjab District Courts | `https://dsj.punjab.gov.pk/` | Partial auth required. Mixed JS. |
| Sindh District Courts | `https://cases.districtcourtssindh.gos.pk/` | No auth. Standard HTML. Requests + BS4. |

**Priority**: P2. Build after High Court scrapers are working.
**Library**: `requests`, `beautifulsoup4` (Sindh), `playwright` (Punjab if needed)
**Target table**: `court_judgments`

### Court Scraper Output Schema

```python
{
    "court_name": str,           # → court_judgments.court_name
    "court_bench": str | None,   # → court_judgments.court_bench
    "case_number": str,          # → court_judgments.case_number
    "judgment_date": date | None,# → court_judgments.judgment_date
    "judge_names": list[str],    # → court_judgments.judge_names (ARRAY)
    "appellant": str,            # → court_judgments.appellant
    "respondent": str,           # → court_judgments.respondent
    "ppc_sections": list[str],   # → court_judgments.ppc_sections (ARRAY)
    "statutes": list[str],       # → court_judgments.statutes (ARRAY)
    "verdict": str | None,       # → court_judgments.verdict
    "sentence": str | None,      # → court_judgments.sentence
    "pdf_url": str | None,       # → court_judgments.pdf_url
    "source_url": str,           # → court_judgments.source_url
}
```

After scraping, judgments are queued for NLP processing via `CourtJudgmentParser` to extract `incident_district_pcode`, `trafficking_type`, `sentence_years`, and `nlp_confidence`.

---

## 6. Government & Police Scrapers

### 6.1 StateOfChildren.com (NCRC Portal)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/government/stateofchildren.py` |
| **URL** | `https://stateofchildren.com/children-dataset/` |
| **Also scrape** | `/helplines/`, related child protection pages |
| **Format** | Clean HTML tables — **EASIEST government source** |
| **Library** | `requests`, `beautifulsoup4` |
| **Selectors** | Standard `<table>` elements. Use `pd.read_html()` for quick extraction. |
| **Target table** | `vulnerability_indicators`, `incidents` |
| **Schedule** | Monthly: `0 6 1 * *` |
| **Notes** | Quick win. No authentication, no JS, clean data. |

### 6.2 Punjab Police

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/government/punjab_police.py` |
| **Missing persons URL** | `https://punjabpolice.gov.pk/missing-persons` |
| **Crime stats URL** | `https://punjabpolice.gov.pk/crimestatistics` |
| **Format** | HTML pages + quarterly PDF lists |
| **Library** | `requests`, `beautifulsoup4`, `pdfplumber` |
| **Target table** | `incidents` (missing persons, crime stats) |
| **Schedule** | Monthly (15th): `0 4 15 * *` |
| **Notes** | Quarterly missing persons lists published as HTML/PDF. Crime stats are annual pages. e-FIR system (878K+ FIRs) is behind police auth — not accessible. |

### 6.3 Sindh Police

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/government/sindh_police.py` |
| **Crime stats URL** | `https://sindhpolice.gov.pk/annoucements/crime_stat_all_cities.html` |
| **Missing persons URL** | `https://sindhpolice.gov.pk/missing_person.html` (currently 403) |
| **Format** | HTML tables |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `incidents` |
| **Schedule** | Monthly (15th): `0 4 15 * *` (30 min offset) |
| **Data granularity** | Range-level: Karachi, Hyderabad, Sukkur, Larkana |
| **Challenges** | Missing persons page returns 403. Monitor periodically for access restoration. |

### 6.4 KP Child Protection & Welfare Commission (CPWC)

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/government/kpcpwc.py` |
| **URL** | `https://kpcpwc.gov.pk/factsandfigure.html` |
| **Format** | HTML |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `vulnerability_indicators`, `incidents` |
| **Schedule** | Monthly (15th): `0 5 15 * *` |
| **Notes** | KP Police has no public crime stats (403 on data pages). CPWC facts page is the primary KP source. |

### 6.5 MoHR ZARRA Checker

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/government/mohr_checker.py` |
| **URL pattern** | `https://mohr.gov.pk/SiteImage/Misc/files/ZARRA*` |
| **Purpose** | Monitor for new ZARRA PDF publications |
| **Library** | `requests` |
| **Schedule** | Monthly: `0 3 25 * *` |
| **Notes** | Checks for new PDF URLs matching the ZARRA pattern. Downloads new PDFs and queues for parsing. |

### 6.6 SSDO Checker

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/government/ssdo_checker.py` |
| **URL** | `https://www.ssdo.org.pk/` (check `/media/`, `/reports/`) |
| **Purpose** | Monitor for new SSDO report publications |
| **Library** | `requests`, `beautifulsoup4` |
| **Schedule** | Monthly: `0 3 20 * *` |
| **Notes** | Scans SSDO website for new report PDFs. Downloads and queues for parsing. |

---

## 7. International API Scrapers

### 7.1 World Bank API

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/international/worldbank_api.py` |
| **Class** | `WorldBankAPIScraper` |
| **API base** | `https://api.worldbank.org/v2/country/PAK/indicator/{code}?format=json&per_page=100` |
| **14 indicators** | See Section 2.11 for full list |
| **Response format** | `[metadata, [datapoints]]` where each datapoint has `date` (year), `value`, `indicator.id` |
| **Library** | `httpx` (async) or `requests` |
| **Target table** | `vulnerability_indicators` |
| **Schedule** | Quarterly: `0 7 1 1,4,7,10 *` |
| **Rate limit** | None required. Public API with generous limits. |

### 7.2 UNHCR Refugee Data Finder API

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/international/unhcr_api.py` |
| **API base** | `https://api.unhcr.org/population/v1/` |
| **Query params** | `?limit=100&dataset=population&displayType=totals&yearFrom=2000&yearTo=2025&coo_all=true&coa=PAK` |
| **Key data** | 1.4M+ registered Afghans, 500K+ undocumented. Settlement locations. |
| **Library** | `httpx` (async) or `requests` |
| **Target table** | `vulnerability_indicators` → `refugee_population` |
| **Schedule** | Quarterly: `0 7 1 1,4,7,10 *` (30 min offset) |

### 7.3 UNODC Data Portal

| Field | Value |
|-------|-------|
| **File** | `data/scrapers/international/unodc.py` |
| **Data portal** | `https://dataunodc.un.org/dp-trafficking-persons` |
| **GLO.ACT reports** | `https://www.unodc.org/documents/human-trafficking/GLO-ACTII/` (multiple PDFs) |
| **Global reports** | `https://www.unodc.org/unodc/data-and-analysis/glotip.html` (biennial 2009-2024) |
| **Format** | CSV download from portal + PDF reports |
| **Library** | `requests`, `pandas`, `pdfplumber` |
| **Target table** | `incidents` (victim counts), `vulnerability_indicators` |
| **Schedule** | Quarterly: `0 3 1 1,4,7,10 *` |
| **Notes** | Portal allows CSV download filtered by country. Pakistan-specific: 800+ sex trafficking cases, 11,803 victims referred by provincial police. |

### 7.4 ACLED (Political Violence Events)

| Field | Value |
|-------|-------|
| **URL** | `https://acleddata.com/data-export-tool/` |
| **API** | `https://api.acleddata.com/acled/read?iso=586&limit=0` (ISO 586 = Pakistan) |
| **Auth** | Requires free API key (register at acleddata.com) |
| **Data** | Political violence events with geocoded locations, event types, fatalities |
| **Format** | JSON API / CSV export |
| **Library** | `requests` |
| **Target table** | `vulnerability_indicators` (conflict indicator) |
| **Schedule** | Monthly or quarterly |
| **Notes** | NEW source — not in original documentation. Provides conflict/instability context for vulnerability modeling. |

---

## 8. NEW Sources Found Via Research

These sources were NOT in the original project documentation and add significant analytical value.

### 8.1 ACLED Pakistan (Armed Conflict Location & Event Data)

| Field | Value |
|-------|-------|
| **URL** | `https://acleddata.com/` |
| **API** | `https://api.acleddata.com/acled/read?iso=586` |
| **What it adds** | Geocoded political violence and protest events. Conflict zones correlate with trafficking vulnerability (displacement, breakdown of law enforcement). |
| **Format** | JSON API with auth key |
| **Fields** | `event_date`, `event_type`, `sub_event_type`, `admin1`, `admin2`, `latitude`, `longitude`, `fatalities` |
| **Target table** | `vulnerability_indicators` (aggregate conflict scores per district) |
| **Implementation** | Register for free API key. Fetch Pakistan events. Spatial join to districts. Calculate violence density per district. |

### 8.2 Organized Crime Index (OC Index)

| Field | Value |
|-------|-------|
| **URL** | `https://ocindex.net/country/pakistan` |
| **What it adds** | Structured crime assessment scores: criminality score, criminal markets (human trafficking, arms, drugs), criminal actors, resilience scores |
| **Format** | Web page (likely has underlying API or downloadable dataset) |
| **Target table** | `vulnerability_indicators` (national-level context) |
| **Implementation** | Scrape country page or find data download. Extract trafficking market score, resilience score. |

### 8.3 NASA FIRMS (Fire Information for Resource Management System)

| Field | Value |
|-------|-------|
| **URL** | `https://firms.modaps.eosdis.nasa.gov/` |
| **API** | `https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/PAK/1` |
| **What it adds** | Thermal anomaly data. Brick kilns produce distinct heat signatures. Can validate/supplement Zenodo kiln dataset with near-real-time satellite detection. |
| **Format** | CSV via REST API |
| **Fields** | `latitude`, `longitude`, `brightness`, `confidence`, `acq_date`, `acq_time` |
| **Target table** | `brick_kilns` (validation layer) |
| **Implementation** | Register for free MAP_KEY. Download Pakistan thermal anomalies. Filter for persistent hotspots (daily recurrence = likely kiln). Cross-reference with Zenodo kiln locations. |

### 8.4 Meta Relative Wealth Index (RWI)

| Field | Value |
|-------|-------|
| **URL** | `https://data.humdata.org/dataset/relative-wealth-index` |
| **What it adds** | 2.4km grid poverty mapping using Facebook connectivity data + satellite imagery. Much higher resolution than national surveys. |
| **Format** | CSV (lat/lon grid cells with RWI scores) |
| **Target table** | `vulnerability_indicators` → `poverty_headcount_ratio` (district average of grid cells) |
| **Implementation** | Download Pakistan RWI CSV. Spatial join grid cells to districts. Calculate mean RWI per district as poverty proxy. |

### 8.5 Additional News Sources

| Source | URL | RSS | Library | Notes |
|--------|-----|-----|---------|-------|
| Pakistan Today | `https://www.pakistantoday.com.pk` | WordPress `/feed/` | feedparser, requests, BS4 | Standard WP scraping |
| Dunya News | `https://dunyanews.tv` | Check for RSS | feedparser/playwright | May need JS rendering |
| Daily Times | `https://dailytimes.com.pk` | WordPress `/feed/` | feedparser, requests, BS4 | Standard WP |
| BBC Urdu | `https://www.bbc.com/urdu` | BBC RSS available | feedparser, requests | Urdu-language, reliable |

**Implementation**: Add to `RSSMonitor.DEFAULT_FEEDS` dict. Those requiring Playwright go in `scrape_news_js` task.

### 8.6 Balochistan Police Crime Statistics

| Field | Value |
|-------|-------|
| **URL** | `https://balochistanpolice.gov.pk/crime_statistics` |
| **Subsections** | All Crime, Major Crime Heads, Terrorism |
| **Library** | `requests`, `beautifulsoup4` |
| **Target table** | `incidents` |
| **Notes** | Separate from existing Sindh/Punjab police scrapers. Add to `scrape_police_data` Celery task with `province="balochistan"`. |

### 8.7 District Courts

| Court | URL | Tech | Notes |
|-------|-----|------|-------|
| Punjab District Courts | `https://dsj.punjab.gov.pk/` | Mixed JS | Partial auth. P2 priority. |
| Sindh District Courts | `https://cases.districtcourtssindh.gos.pk/` | Standard HTML | No auth. Requests + BS4. P2. |

### 8.8 DHS 2017-18 Pakistan

| Field | Value |
|-------|-------|
| **URL** | `https://dhsprogram.com/` |
| **API** | `https://api.dhsprogram.com/` |
| **What it adds** | Health/demographic survey with GPS cluster coordinates. 8 regions. Spatial join to districts. |
| **Format** | API (JSON) + downloadable microdata (registration required) |
| **Target table** | `vulnerability_indicators` (birth registration, health indicators) |

### 8.9 UNICEF MICS Punjab 2017-18

| Field | Value |
|-------|-------|
| **URL** | `https://mics.unicef.org/` (Tabulator), `https://microdata.worldbank.org/` (microdata) |
| **What it adds** | District-representative survey for Punjab. 120+ indicators including child labor, child marriage, birth registration. |
| **Format** | SPSS/CSV microdata (registration required) |
| **Target table** | `vulnerability_indicators` |
| **Notes** | Richest district-level dataset for Punjab. Registration required for microdata access. |

### 8.10 PBS PSLM SDGs Dashboard

| Field | Value |
|-------|-------|
| **URL** | `https://pslm-sdgs.data.gov.pk/` |
| **What it adds** | Interactive data portal with district-level SDG indicators. May have API endpoints. |
| **Format** | Interactive dashboard (check for API/CSV export) |
| **Target table** | `vulnerability_indicators` (education, health, WASH, food insecurity) |

### 8.11 ILO SIMPOC Child Labour Surveys

| Field | Value |
|-------|-------|
| **URL** | `https://www.ilo.org/` |
| **What it adds** | Sector-level child labor data: agriculture, manufacturing, services, domestic work |
| **Format** | PDF/Excel |
| **Target table** | `vulnerability_indicators` → `child_labor_rate` |

### 8.12 SPARC State of Pakistan's Children

| Field | Value |
|-------|-------|
| **URL** | `https://sparcpk.org/` |
| **What it adds** | Annual child rights monitoring. Province-level indicator tracking. |
| **Format** | PDF annual reports |
| **Target table** | `vulnerability_indicators`, `incidents` |

### 8.13 IOM Migration Data Portal

| Field | Value |
|-------|-------|
| **URL** | `https://www.migrationdataportal.org/themes/human-trafficking` |
| **Pakistan Snapshot PDF** | `https://dtm.iom.int/sites/g/files/tmzbdl1461/files/reports/Pakistan%20Migration%20Snapshot%20Final.pdf` |
| **What it adds** | Migration flow data relevant to trafficking routes |
| **Format** | Web portal + PDF |
| **Target table** | `trafficking_routes`, `incidents` |

### 8.14 PBS Labour Force Survey

| Field | Value |
|-------|-------|
| **URL** | `https://www.pbs.gov.pk/labour-force-statistics/` |
| **Key Findings PDF** | `https://www.pbs.gov.pk/sites/default/files/labour_force/publications/lfs2020_21/Key_Findings_of_Labour_Force_Survey_2020-21.pdf` |
| **What it adds** | Employment by province/district/sex/age, child labor indicators (10-14 age), NEET data |
| **Target table** | `vulnerability_indicators` → `child_labor_rate`, `unemployment_rate` |

---

## 9. NLP & Geocoding Pipeline

### 9.1 TraffickingNLPPipeline

**File**: `backend/app/services/nlp_pipeline.py`

#### 20 Trafficking Keywords

```python
_TRAFFICKING_KEYWORDS = [
    "trafficking", "trafficked", "bonded", "forced labor", "forced labour",
    "child labor", "child labour", "brick kiln", "bhatta", "smuggling",
    "kidnap", "abduct", "sexual abuse", "exploitation", "modern slavery",
    "debt bondage", "child marriage", "missing child", "begging ring",
    "organ trafficking", "camel jockey",
]
```

#### Classification Logic

- `classify_relevance(text)` → `(is_relevant: bool, confidence: float)`
- Heuristic: keyword count / word count = keyword_density
- Threshold: at least 1 keyword hit AND density > 0.5%
- Confidence: `min(keyword_density * 100, 1.0)` when relevant

#### Entity Extraction

- `extract_entities(text)` → `{locations: [], dates: [], victims: [], perpetrators: []}`
- Uses spaCy `en_core_web_sm` model
- Entity labels: `GPE`/`LOC`/`FAC` → locations, `DATE`/`TIME` → dates, `PERSON` → victims/perpetrators
- Perpetrator classification: if context contains "accused", "suspect", "perpetrator", "arrested" within 60 chars

### 9.2 NewsArticleParser

**File**: `data/parsers/news_article_parser.py`

#### 11 Crime Types

```python
CRIME_TYPES = [
    "child_trafficking", "child_sexual_abuse", "kidnapping", "abduction",
    "bonded_labor", "child_marriage", "missing_child", "child_labor",
    "physical_abuse", "child_pornography", "other",
]
```

#### Pipeline Stages

1. **NER** (spaCy): Extract GPE, LOC, PERSON, DATE, ORG, CARDINAL entities
2. **Crime classification**: Keyword matching + ML classifier
3. **Victim extraction**: Age patterns ("12-year-old", "minor"), gender from pronouns
4. **Perpetrator extraction**: Arrest/accused references, relationship to victim
5. **Geocoding**: Gazetteer lookup → district P-code + lat/lon
6. **Confidence scoring**: Aggregate extraction quality

### 9.3 CourtJudgmentParser

**File**: `data/parsers/court_judgment_parser.py`

#### Key Regex Patterns

```python
# PPC section extraction
PPC_PATTERN = r"(?:section|s\.|u/s|under section)\s*(\d{2,3}(?:-[A-Z])?)"

# Case number extraction
CASE_NUMBER_PATTERN = r"(?:Cr\.?\s*(?:A|P|M|R)\.?\s*No\.?\s*(\d+)\s*/\s*(\d{4}))"

# Age extraction
AGE_PATTERN = r"aged?\s*(\d{1,2})\s*years?"

# Sentence extraction
SENTENCE_PATTERN = r"(?:sentenced?\s+to\s+|rigorous imprisonment\s+(?:for\s+)?|imprisonment\s+(?:for\s+)?)(\d+)\s*years?"
```

#### Extraction Flow

1. Extract text from PDF (pdfplumber, layout-aware)
2. Extract case header: case number, date, court, bench, judge
3. Extract parties: petitioner vs respondent (look for "versus"/"v/s")
4. Extract PPC sections: regex on full text, deduplicate
5. Extract district: NER + "FIR registered at PS [station]" patterns
6. Extract victim demographics: age, gender, count
7. Extract sentence: "sentenced to"/"acquitted"/"appeal allowed"
8. Combine into structured record

### 9.4 PakistanGeocoder

**File**: `backend/app/services/geocoder.py`

#### Gazetteer Requirements

- **3,000+ entries** covering:
  - All 160+ district names with alternative spellings
  - All 577 tehsils
  - 500+ major cities/towns
  - Known trafficking-relevant locations: brick kiln areas, border towns, bus stations, truck stops, shrines
- **Format**: JSON at `data/config/gazetteer/pakistan_districts.json`
- **Entry structure**: `{"name": {"lat": float, "lon": float, "pcode": str}}`
- **Variant handling**: Each name lowercased and stripped. Substring matching fallback.

#### Geocoding Strategy

1. **Gazetteer lookup** (confidence = 1.0): Exact match on lowercased text
2. **Substring fallback** (confidence = 0.8): Partial match in gazetteer entries
3. **Nominatim API** (confidence = 0.7): OSM geocoder restricted to `countrycodes=PK`
   - User-Agent: `Nigehbaan/0.1 (child-trafficking-research)`
   - Rate limit: 1 request/second (Nominatim ToS)

---

## 10. Celery Schedule Reference

**File**: `backend/app/tasks/schedule.py`

| # | Task Key | Celery Task | Cron | Queue | Target |
|---|----------|-------------|------|-------|--------|
| 1 | `news_rss` | `scrape_news_rss` | `0 */6 * * *` | scraping | Dawn, Tribune, The News, ARY RSS |
| 2 | `news_js` | `scrape_news_js` | `30 2 * * *` | scraping | Geo News, Samaa TV (Playwright) |
| 3 | `sahil_checker` | `check_sahil_updates` | `0 3 1 * *` | scraping | sahil.org |
| 4 | `tip_report` | `scrape_tip_report` | `0 4 1 7 *` | scraping | state.gov TIP Report |
| 5 | `ctdc_updater` | `update_ctdc` | `0 5 1 1,4,7,10 *` | scraping | CTDC dataset |
| 6 | `court_scp` | `scrape_courts("scp")` | `0 1 * * 0` | scraping | Supreme Court |
| 7 | `court_lhc` | `scrape_courts("lhc")` | `15 1 * * 0` | scraping | Lahore HC |
| 8 | `court_shc` | `scrape_courts("shc")` | `30 1 * * 0` | scraping | Sindh HC (5 benches) |
| 9 | `court_phc` | `scrape_courts("phc")` | `45 1 * * 0` | scraping | Peshawar HC (4 benches) |
| 10 | `court_bhc` | `scrape_courts("bhc")` | `0 2 * * 0` | scraping | Balochistan HC (Playwright) |
| 11 | `court_ihc` | `scrape_courts("ihc")` | `15 2 * * 0` | scraping | Islamabad HC (ASP.NET) |
| 12 | `police_punjab` | `scrape_police_data("punjab")` | `0 4 15 * *` | scraping | Punjab Police |
| 13 | `police_sindh` | `scrape_police_data("sindh")` | `30 4 15 * *` | scraping | Sindh Police |
| 14 | `police_kp` | `scrape_police_data("kp")` | `0 5 15 * *` | scraping | KP CPWC |
| 15 | `police_balochistan` | `scrape_police_data("balochistan")` | `30 5 15 * *` | scraping | Balochistan Police |
| 16 | `stateofchildren` | `scrape_stateofchildren` | `0 6 1 * *` | scraping | StateOfChildren.com |
| 17 | `worldbank_api` | `scrape_worldbank_api` | `0 7 1 1,4,7,10 *` | scraping | World Bank API |
| 18 | `unhcr_api` | `scrape_unhcr_api` | `30 7 1 1,4,7,10 *` | scraping | UNHCR API |

**Processing tasks** (file: `backend/app/tasks/processing_tasks.py`):

| Task | Trigger | What it does |
|------|---------|--------------|
| `process_pdf` | After PDF download | pdfplumber extraction → NLP → store |
| `geocode_incidents` | After new incidents | Batch geocode: gazetteer → Nominatim |
| `calculate_risk_scores` | After vulnerability update | Composite risk score per district |
| `run_nlp_pipeline` | After news article scrape | classify + extract entities per article |
| `update_vulnerability_indicators` | After new data ingest | Aggregate kiln counts, border proximity, WB/UNHCR data |

---

## 11. Database Target Reference

### Source → Table Mapping

| Source | Target Table | `source_type` | Key Fields Populated |
|--------|-------------|---------------|---------------------|
| HDX Admin Boundaries | `boundaries` | — | `name_en`, `pcode`, `parent_pcode`, `geometry`, `admin_level` |
| Census 2017 | `boundaries` | — | `population_total`, `population_male`, `population_female`, `population_urban`, `population_rural` |
| HDX Population | `boundaries` | — | `population_total`, `population_male`, `population_female` |
| Zenodo Brick Kilns | `brick_kilns` | — | `geometry`, `kiln_type`, `nearest_school_m`, `nearest_hospital_m`, `population_1km`, `district_pcode` |
| OSM Border Crossings | `border_crossings` | — | `name`, `geometry`, `border_country`, `crossing_type` |
| CTDC Victims | `incidents` | `ctdc` | `incident_type`, `victim_gender`, `victim_age_min`, `victim_age_max`, `sub_type` |
| Sahil Reports | `incidents` | `sahil` | `year`, `province_pcode`, `incident_type`, `victim_gender`, `victim_age_bracket`, `case_count` |
| SSDO Reports | `incidents` | `ssdo` | `year`, `province_pcode`, `incident_type`, `case_count`, `conviction` |
| ZARRA Reports | `incidents` | `zarra` | `district_pcode`, `case_status`, `year` |
| NCSW/UNICEF VAC | `incidents` | `ncsw_vac` | `district_pcode`, `incident_type`, `case_count` |
| FIA Reports | `incidents` | `fia` | `year`, `incident_type`, `case_count` |
| FIA Reports | `trafficking_routes` | — | `origin_country`, `destination_country`, `trafficking_type`, `evidence_source` |
| News Articles | `news_articles` | — | `url`, `title`, `source_name`, `published_date`, `full_text`, `is_trafficking_relevant`, `extracted_*` |
| News NLP → | `incidents` | `news` | `incident_date`, `district_pcode`, `incident_type`, `victim_count`, `geometry` |
| Court Scraping | `court_judgments` | — | `court_name`, `case_number`, `judgment_date`, `ppc_sections`, `appellant`, `respondent`, `verdict` |
| Court NLP → | `court_judgments` | — | `incident_district_pcode`, `trafficking_type`, `sentence_years`, `nlp_confidence` |
| TIP Report | `tip_report_annual` | — | `year`, `tier_ranking`, `ptpa_investigations`, `ptpa_convictions`, `victims_identified`, `named_hotspots` |
| World Bank API | `vulnerability_indicators` | `worldbank` | `school_enrollment_rate`, `poverty_headcount_ratio`, `literacy_rate`, `child_labor_rate` |
| UNHCR API | `vulnerability_indicators` | `unhcr` | `refugee_population` |
| Walk Free GSI | `vulnerability_indicators` | `walkfree` | National-level context scores |
| UNICEF Child Marriage | `vulnerability_indicators` | `unicef` | `child_marriage_rate` |
| UNOSAT Flood | `vulnerability_indicators` | `unosat` | `flood_affected_pct` |
| DOL Child Labor | `vulnerability_indicators` | `dol` | `child_labor_rate` |
| Zenodo Kilns (agg) | `vulnerability_indicators` | `zenodo` | `brick_kiln_count`, `brick_kiln_density_per_sqkm` |
| OSM Borders (agg) | `vulnerability_indicators` | `osm` | `distance_to_border_km` |
| ACLED (new) | `vulnerability_indicators` | `acled` | Conflict density score (derived) |
| Meta RWI (new) | `vulnerability_indicators` | `meta_rwi` | `poverty_headcount_ratio` (high-res proxy) |
| Public Reports | `public_reports` | — | `report_type`, `description`, `geometry`, `district_pcode`, `status` |

### ORM Model → Column Coverage

Every column in every ORM model has at least one source mapping:

**`boundaries`** (11 columns): HDX Boundaries + Census 2017 + HDX Population
**`brick_kilns`** (7 columns): Zenodo dataset
**`border_crossings`** (8 columns): OSM Geofabrik
**`incidents`** (25 columns): Sahil, SSDO, ZARRA, CTDC, News NLP, Court NLP, FIA
**`court_judgments`** (19 columns): Court scrapers + CourtJudgmentParser NLP
**`news_articles`** (11 columns): News scrapers + TraffickingNLPPipeline
**`tip_report_annual`** (16 columns): TIP Report scraper
**`vulnerability_indicators`** (18 columns): World Bank, UNHCR, Walk Free, UNICEF, UNOSAT, DOL, Zenodo agg, OSM agg, ACLED, Meta RWI
**`trafficking_routes`** (11 columns): FIA reports, TIP Report qualitative data, CTDC route fields
**`public_reports`** (12 columns): User-submitted (no scraper — frontend form)
**`data_sources`** (10 columns): Auto-populated by `BaseScraper.log_run()`

---

## 12. Implementation Sequence

### Dependency Graph

```
boundaries (HDX) ─────────────────────┐
    ↑                                  │
census_2017 ──► boundaries.population  │
hdx_population ──► boundaries.pop     │
    │                                  │
    ├─── brick_kilns (Zenodo) ─► spatial join needs boundaries
    ├─── border_crossings (OSM) ─► spatial join needs boundaries
    ├─── flood_extent (UNOSAT) ─► spatial intersection needs boundaries
    │                                  │
    ├─── ctdc_victims ─► needs incident_type mapping
    ├─── sahil_parser ─► needs province_pcode from boundaries
    ├─── news_scrapers ─► needs geocoder (needs gazetteer from boundaries)
    ├─── court_scrapers ─► needs district_pcode from boundaries
    │                                  │
    └─── vulnerability_indicators ─► aggregates from all above
```

### 6-Phase Build Order

**Phase 1: Foundation (Week 1-2)**
1. Load HDX administrative boundaries → `boundaries`
2. Load Census 2017 population → `boundaries` population columns
3. Load HDX population stats → `boundaries`
4. Build `district_name_variants` crosswalk
5. Build `pakistan_districts.json` gazetteer (3000+ entries)

**Phase 2: Point Data (Week 2-3)**
6. Load Zenodo brick kilns → `brick_kilns` + spatial join
7. Load OSM border crossings → `border_crossings`
8. Load UNOSAT flood extent → `vulnerability_indicators.flood_affected_pct`
9. Load CTDC victims → `incidents`
10. Load Walk Free GSI → `vulnerability_indicators`

**Phase 3: PDF Parsers (Week 3-5)**
11. Build Sahil parser (16 PDFs, 3 format eras) → `incidents`
12. Build SSDO parser → `incidents`
13. Build TIP Report scraper (24 years HTML) → `tip_report_annual`
14. Build ZARRA parser → `incidents`
15. Build NCSW/UNICEF VAC parser → `incidents`
16. Build DOL Child Labor parser → `vulnerability_indicators`

**Phase 4: News Pipeline (Week 5-6)**
17. Build Dawn scraper (RSS + article fetch) → `news_articles`
18. Build Tribune scraper → `news_articles`
19. Build The News scraper → `news_articles`
20. Build ARY scraper → `news_articles`
21. Build RSS Monitor (Google News + multi-feed) → `news_articles`
22. Build Geo News scraper (Playwright) → `news_articles`
23. Wire NLP pipeline: `run_nlp_pipeline` → `news_articles` extracted columns
24. Wire geocoding: `geocode_incidents` → `incidents.geometry`

**Phase 5: Court & Government (Week 6-8)**
25. Build CommonLII bulk scraper → `court_judgments`
26. Build SCP scraper → `court_judgments`
27. Build LHC scraper → `court_judgments`
28. Build remaining HC scrapers (SHC, PHC, BHC, IHC) → `court_judgments`
29. Wire CourtJudgmentParser NLP → `court_judgments` extracted columns
30. Build StateOfChildren scraper → `vulnerability_indicators`
31. Build Punjab/Sindh Police scrapers → `incidents`
32. Build KP CPWC scraper → `vulnerability_indicators`

**Phase 6: APIs & Enrichment (Week 8-9)**
33. Build World Bank API scraper → `vulnerability_indicators`
34. Build UNHCR API scraper → `vulnerability_indicators`
35. Build UNODC data fetcher → `incidents`, `vulnerability_indicators`
36. Build FIA report parser → `incidents`, `trafficking_routes`
37. Wire `calculate_risk_scores` → `vulnerability_indicators.trafficking_risk_score`
38. Wire `update_vulnerability_indicators` → composite vulnerability
39. Add ACLED, Meta RWI, NASA FIRMS enrichment sources

---

## Verification Checklist

- [x] Every source in `data/config/sources.yaml` (37 entries) has a corresponding section in this spec
- [x] Every stub scraper/parser file has implementation details (URLs, selectors, field mappings)
- [x] Every Celery task in `schedule.py` (17 tasks + 5 processing) maps to a documented scraper
- [x] Every ORM model column has at least one source mapping
- [x] All 16 Sahil PDF URLs are included
- [x] 14 new sources discovered via research are documented in Section 8
- [x] Scraper output schemas match target table columns
- [x] NLP pipeline keywords, patterns, and classification logic documented
- [x] Geocoder strategy (gazetteer → Nominatim fallback) specified
- [x] Implementation dependency graph and build order defined
