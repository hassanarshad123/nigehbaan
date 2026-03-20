# NIGEHBAAN — Pakistan Child Trafficking Intelligence Platform

## نگہبان — "The Guardian Who Watches Over"

**Version**: 1.0 — Master Blueprint
**Last Updated**: March 19, 2026
**Created By**: Hassan Arshad (Zensbot) — in collaboration with Claude
**Status**: Pre-Development — Architecture & Data Source Documentation Complete

---

## TABLE OF CONTENTS

1. [Why This Exists](#1-why-this-exists)
2. [What Nigehbaan Does](#2-what-nigehbaan-does)
3. [Who This Is For](#3-who-this-is-for)
4. [System Architecture](#4-system-architecture)
5. [Complete Data Source Registry](#5-complete-data-source-registry)
6. [Scraper & Pipeline Specifications](#6-scraper--pipeline-specifications)
7. [Database Schema](#7-database-schema)
8. [Geo-Mapping Engine](#8-geo-mapping-engine)
9. [Frontend Application](#9-frontend-application)
10. [Backend API](#10-backend-api)
11. [AI/ML Intelligence Layer](#11-aiml-intelligence-layer)
12. [Public Reporting System](#12-public-reporting-system)
13. [Development Roadmap](#13-development-roadmap)
14. [Security & Ethics](#14-security--ethics)
15. [Deployment & Infrastructure](#15-deployment--infrastructure)

---

## 1. WHY THIS EXISTS

### The Problem

Pakistan has an estimated **2.35 million people trapped in modern slavery** (Walk Free Foundation, 2023), ranking 4th globally in prevalence. The US State Department's 2025 TIP Report documents **1,607 trafficking investigations under PTPA alone**, with only **495 convictions**. Sahil's "Cruel Numbers" reports track **7,608 incidents of child abuse in 2024**, including kidnapping, sexual exploitation, and trafficking — a number that represents only what newspapers report. The actual scale is far larger.

Yet the data that exists is:

- **Scattered** across 90+ sources in 3 languages (English, Urdu, Sindhi)
- **Siloed** between federal agencies, 4 provincial governments, dozens of NGOs, and international bodies
- **Locked in PDFs** — the most critical datasets (Sahil's 16 annual reports, FIA annual reports, court judgments, ZARRA analysis) exist as unstructured PDF documents
- **Not geo-coded** — no single map exists showing where trafficking happens, where children go missing, where they are recovered, and what routes connect origin to exploitation
- **Not connected** — nobody is cross-referencing brick kiln locations with missing children reports with poverty data with school dropout rates to see predictive patterns

**The result**: Law enforcement operates blind. NGOs duplicate effort. Policymakers legislate without evidence. Citizens have no way to report or understand the threat in their own communities.

### The Solution

Nigehbaan is a **unified data intelligence platform** that:

1. **Aggregates** every publicly available data point on child trafficking in Pakistan into one normalized database
2. **Geo-maps** every incident, hotspot, route, and vulnerability indicator onto an interactive map of Pakistan at district resolution (160 districts, 577 tehsils)
3. **Connects** data across sources to reveal patterns invisible in any single dataset — linking brick kiln locations to missing children reports to poverty indicators to court conviction rates
4. **Empowers** three audiences: government/law enforcement (with intelligence dashboards), NGOs (with evidence for advocacy), and citizens (with reporting tools and awareness)

### The Name

**Nigehbaan** (نگہبان) means "Guardian" or "Watchkeeper" in Urdu — someone who keeps vigil, who watches over those who cannot protect themselves. This platform is a digital nigehbaan for Pakistan's children.

---

## 2. WHAT NIGEHBAAN DOES

### Core Capabilities

**A. Interactive Geo-Intelligence Map**
- Heat maps of child trafficking incidents by district (sourced from Sahil, SSDO, ZARRA, news media)
- Point markers for 11,000+ brick kilns (Zenodo dataset) with bonded labor indicators
- Trafficking route visualization (origin → transit → exploitation) constructed from TIP Reports and FIA data
- Border crossing vulnerability overlay (8 Afghanistan crossings, 4 Iran crossings, 1 India crossing)
- Layer toggle for: poverty index, school dropout rates, flood-affected areas, police jurisdiction boundaries

**B. Trend Analysis Dashboard**
- 15-year longitudinal charts from Sahil Cruel Numbers (2010–2024)
- Province-wise comparison (Punjab, Sindh, KP, Balochistan, ICT, AJK, GB)
- Case type breakdown (kidnapping, sexual abuse, trafficking, child marriage, bonded labor, begging mafia)
- Prosecution vs. conviction rates over time (from TIP Reports — 24 years of data)
- Seasonal patterns and year-over-year change

**C. Pattern Detection Engine**
- Correlation analysis: poverty × trafficking incidents × school dropout × brick kiln density
- Hotspot identification using spatial clustering (DBSCAN on geocoded incidents)
- Network graph of repeat offenders, locations, and connections (from court judgment NLP)
- Early warning scores for vulnerable districts based on leading indicators

**D. Public Reporting Portal**
- Anonymous incident reporting with location pin, photo upload, and category selection
- Missing children alert feed (aggregated from ZARRA, Roshni Helpline, media)
- Community awareness: "Know Your District" risk profiles
- Resource directory: helplines (1099, 1098, Roshni 0800-22444), legal aid, shelter homes

**E. Legal Intelligence Module**
- Court judgment search filtered by trafficking-related PPC sections (366-A, 366-B, 369, 370, 371-A, 371-B)
- Conviction rate mapping by district and court
- Sentencing pattern analysis
- Legislative gap identification (which laws exist vs. which are enforced)

---

## 3. WHO THIS IS FOR

### Primary Audiences

**1. Federal Government & Law Enforcement**
- **FIA Anti-Human Trafficking Circles** (Lahore, Islamabad, Karachi, Peshawar, Quetta) — route intelligence, cross-border pattern analysis
- **ZARRA / Ministry of Human Rights** — missing children geo-tracking, district-level case analysis
- **NCRC (National Commission on Rights of the Child)** — evidence base for policy recommendations
- **Provincial Child Protection Bureaus** (Punjab CPWB, Sindh CPA, KP CPWC) — district-level hotspot data for resource allocation
- **District Administration & DPOs** — local intelligence for targeted operations

**2. NGOs & International Organizations**
- **Sahil, SPARC, Roshni Helpline, Madadgaar** — unified view of the data they each partially hold
- **UNICEF, ILO, IOM, UNODC** — Pakistan-specific analytics for their global programs
- **Walk Free, ECPAT, HRW** — evidence for international advocacy and reporting

**3. Common Citizens of Pakistan**
- Parents who want to understand the risk in their area
- Community members who want to report suspicious activity
- Journalists investigating trafficking stories
- Students and researchers studying the issue
- Anyone who wants to help but doesn't know how

### What Success Looks Like

- A DPO in Kasur opens Nigehbaan, sees a cluster of missing children reports near known brick kilns, and dispatches a targeted operation
- An NGO in Balochistan uses district-level vulnerability scores to decide where to open their next child protection center
- A citizen in Lahore sees a child begging at a traffic signal, opens Nigehbaan on their phone, and files an anonymous report with GPS location
- A parliamentarian uses Nigehbaan's conviction rate data to argue for judicial reform in trafficking cases
- A journalist uses the trend dashboard to write an evidence-backed story that changes public discourse

---

## 4. SYSTEM ARCHITECTURE

### Tech Stack

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

### Supporting Infrastructure

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

### Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend hosting | Vercel | Free tier, edge CDN, native Next.js support |
| Map library | Mapbox GL JS + Deck.gl | 11K+ point rendering (brick kilns), custom layers, free tier (50K loads/mo) |
| Backend framework | FastAPI | Async, auto-docs, Python ecosystem for NLP/geo |
| Database | Neon PostgreSQL + PostGIS | Serverless scaling, spatial queries, free tier |
| Task queue | Celery + Redis | Scheduled scraping, PDF processing, geocoding |
| NLP | spaCy + custom Pakistan gazetteer | Geographic entity extraction from Urdu/English news |
| PDF extraction | pdfplumber + Tabula | Sahil tables, court judgments, FIA reports |
| Scraping | Scrapy + Playwright | Scrapy for standard sites, Playwright for JS-heavy (Geo News, BHC portal) |

---

## 5. COMPLETE DATA SOURCE REGISTRY

### Priority Tier System

- **P0 — IMMEDIATE** (structured, downloadable, no scraping needed)
- **P1 — HIGH** (scrapable HTML or consistent PDFs, high value)
- **P2 — MEDIUM** (requires PDF parsing or complex scraping)
- **P3 — LONG-TERM** (requires institutional access, RTI requests, or NLP)

---

### 5.1 GEOGRAPHIC FOUNDATION LAYERS (P0)

These must be loaded FIRST — they are the base map onto which everything else is plotted.

#### 5.1.1 HDX Administrative Boundaries (OCHA COD-AB)
- **URL**: https://data.humdata.org/dataset/cod-ab-pak
- **What it contains**: Pakistan admin boundaries levels 0-3 (country → province → district → tehsil). 160 districts, 577 tehsils. Each polygon has OCHA P-codes (e.g., PK01 = Balochistan, PK0101 = Kech)
- **Format**: Shapefile, GeoJSON, Geoservice API
- **Schema**: `ADM0_EN`, `ADM0_PCODE`, `ADM1_EN`, `ADM1_PCODE`, `ADM2_EN`, `ADM2_PCODE`, `ADM3_EN`, `ADM3_PCODE`, `geometry`
- **License**: Open (humanitarian use)
- **Scraping**: NONE needed — direct download
- **Join key**: P-codes are the UNIVERSAL JOIN KEY for all geographic data in this platform. Every other dataset must be mapped to these codes.
- **Claude Code instruction**: Download GeoJSON files for admin levels 0-3. Load into PostGIS as `boundaries_adm0`, `boundaries_adm1`, `boundaries_adm2`, `boundaries_adm3` tables. Create spatial indexes. Build a crosswalk table `district_name_variants` mapping common misspellings and alternative names to canonical P-codes.

#### 5.1.2 Pakistan Census 2017 (Digitized CSV)
- **URL**: https://github.com/cerp-analytics/pbs2017
- **What it contains**: Complete 2017 Census results digitized into CSV. Population by district, sex, age group, urban/rural, literacy, employment. 207.68M total population.
- **Format**: CSV + Shapefiles
- **Schema**: District name, province, population_total, population_male, population_female, population_urban, population_rural, literacy_rate, plus age-disaggregated columns
- **License**: Open
- **Scraping**: NONE — git clone
- **Claude Code instruction**: Clone repo. Ingest all CSVs. Join to boundaries using district names (use crosswalk table for name normalization). Store as `census_2017` table with district P-code foreign key.

#### 5.1.3 HDX Population Statistics (COD-PS)
- **URL**: https://data.humdata.org/dataset/cod-ps-pak
- **What it contains**: Population estimates at admin levels 0-3 with P-codes already assigned
- **Format**: CSV/XLSX
- **Scraping**: NONE — direct download
- **Claude Code instruction**: Download and ingest. This provides the pre-matched P-code population denominators for per-capita calculations.

#### 5.1.4 OpenStreetMap Road Network
- **URL**: https://download.geofabrik.de/asia/pakistan.html
- **What it contains**: Complete road network including GT Road (N-5), all motorways (M-1 through M-9), highways, border crossings. 142 MB .osm.pbf file, daily updates.
- **Format**: .osm.pbf (convert to PostGIS with osm2pgsql) or pre-separated Shapefiles (330 MB)
- **Key tags**: `highway=*`, `border_type=*`, `name=*`
- **Claude Code instruction**: Download Shapefiles. Load major roads (`highway=motorway|trunk|primary|secondary`) into PostGIS as `road_network` table. Extract border crossing points (`barrier=border_control`) as `border_crossings` point table.

#### 5.1.5 Zenodo Brick Kiln Dataset ⭐ HIGHEST PRIORITY POINT DATA
- **URL**: https://zenodo.org/records/14038648
- **What it contains**: ~11,000 geolocated brick kilns across Pakistan's Indo-Gangetic Plain. Each kiln has: lat/lon coordinates, kiln type (FCBK/ZigZag), distance to nearest school (within 1km), distance to nearest hospital (within 1km), population within 1km radius.
- **Format**: CSV, GeoJSON, Shapefile (~11.8 MB)
- **Schema**: `latitude`, `longitude`, `kiln_type`, `nearest_school_dist_m`, `nearest_hospital_dist_m`, `population_1km`
- **License**: Open (Nature Scientific Data publication)
- **Scraping**: NONE — direct download
- **Why it matters**: Brick kilns are the single largest site of bonded child labor in Pakistan. ILO reports that 83% of surveyed kilns employed children. 4.5 million bonded laborers estimated. This dataset lets us plot every kiln and overlay it with trafficking incident data.
- **Claude Code instruction**: Download GeoJSON. Load into PostGIS as `brick_kilns` point table. Run spatial join with `boundaries_adm2` to assign each kiln a district P-code. Calculate kiln density per district. This becomes a core vulnerability indicator.

#### 5.1.6 GADM Boundaries (Backup)
- **URL**: https://gadm.org/download_country.html (select Pakistan)
- **Format**: GeoPackage, Shapefile, KMZ, R objects
- **Levels**: Up to 5 admin levels
- **License**: Non-commercial free
- **Claude Code instruction**: Download as backup/validation for HDX boundaries. Useful for tehsil-level data when HDX has gaps.

#### 5.1.7 UNOSAT Flood Extent Data (2022)
- **URL**: https://data.humdata.org/dataset/satellite-detected-water-extents-between-01-and-29-august-2022-over-pakistan
- **What it contains**: Pixel-level (30m resolution) flood polygons from 2022 floods. Flood-affected districts correlate strongly with trafficking vulnerability due to displacement and family separation.
- **Format**: Shapefiles
- **Claude Code instruction**: Load as `flood_extent_2022` layer. Calculate percentage of each district flooded. Store as vulnerability indicator.

---

### 5.2 VICTIM & INCIDENT DATA (P0-P1)

#### 5.2.1 CTDC Global Synthetic Dataset ⭐ P0
- **URL**: https://www.ctdatacollaborative.org/page/global-synthetic-dataset
- **GitHub**: https://github.com/UNMigration/HTCDS
- **What it contains**: 222,000+ trafficking victim case records across 197 countries (2002-2023). K-anonymized public dataset (~48,800 observations) AND full synthetic dataset using Microsoft differential privacy methodology.
- **Fields**: `victim_gender`, `victim_age`, `victim_citizenship`, `country_of_exploitation`, `exploitation_type` (forced_labor, sexual_exploitation, forced_marriage, etc.), `means_of_control` (threat, deception, debt_bondage, etc.), `recruitment_method`, `trafficking_duration`, `route_origin`, `route_transit`, `route_destination`
- **Format**: CSV download — no scraping needed
- **License**: Open (IOM/Polaris Project)
- **Claude Code instruction**: Download CSV. Filter for `country_of_exploitation = 'Pakistan'` OR `victim_citizenship = 'Pakistan'`. Load into `ctdc_victims` table. This gives us structured victim demographics, exploitation types, and recruitment patterns that no Pakistani source provides.

#### 5.2.2 Sahil "Cruel Numbers" Annual Reports ⭐ P1 — HIGHEST PRIORITY PDF EXTRACTION
- **URL**: https://sahil.org/cruel-numbers/
- **Available editions** (16 PDFs covering 2010-2024):

| Year | Direct Download URL |
|------|---------------------|
| 2024 | https://drive.google.com/file/d/1hwjN8dKRfy6ZIqsL240sScCfNUlCLX-m/view |
| 2023 | https://sahil.org/wp-content/uploads/2024/03/Curel-Numbers-2023-Finalll.pdf |
| 2022 | https://sahil.org/wp-content/uploads/2023/05/Cruel-Numbers-2022-Email.pdf |
| 2021 | https://drive.google.com/file/d/1UVATKnqmgpX9K2W5p76o2AiRGsz4fg3n/view |
| 2020 | https://drive.google.com/file/d/1TKxMWYc2w_iwtWMpGDt4UYDvCTtEPA0n/view |
| 2019 | https://sahil.org/wp-content/uploads/2020/03/Cruel-Numbers-2019-final.pdf |
| 2018 | https://drive.google.com/file/d/1EmISbZNQ7v6bRVUc4VwsoThbXPUzs7Xd/view |
| 2017 | https://sahil.org/wp-content/uploads/2018/04/Cruel-Numbers-Report-2017-1.pdf |
| 2016 | https://sahil.org/wp-content/uploads/2017/03/Cruel-numbers-Report-2016-Autosaved1-edited111.pdf |
| 2015 | https://sahil.org/wp-content/uploads/2016/04/Final-Cruel-Numbers-2015-16-03-16.pdf |
| 2014 | https://sahil.org/wp-content/uploads/2015/04/Cruel-Numbers-2014.pdf |
| 2013 | https://sahil.org/wp-content/uploads/2014/06/Cruel-Number-2013.pdf |
| 2012 | https://sahil.org/wp-content/uploads/2014/09/Cruel-Number-2012.pdf |
| 2011 | https://sahil.org/wp-content/uploads/2015/11/Creul-Number-2011.pdf |
| 2010 | https://sahil.org/wp-content/uploads/2015/11/cruel-numbers-2010.pdf |
| 5-Year Analysis (2007-2011) | https://sahil.org/wp-content/uploads/2014/09/FIVE-YEAR-ANALYSIS-200-2011.pdf |

- **Data structure per report**:
  - Total cases by crime category: rape, sodomy, gang rape, child sexual abuse murder, pornography, incest, abduction (total + with sexual abuse + with murder), missing children, child marriage, trafficking
  - Province-wise breakdown: Punjab, Sindh, KP, Balochistan, ICT, AJK, GB
  - Urban vs. rural split
  - Victim gender (male/female)
  - Victim age brackets: 0-5, 6-10, 11-15, 16-18
  - Abuser profile: acquaintance, stranger, family member, service provider, neighbor, teacher
  - Police registration rates (reported vs. FIR filed)
  - Location type where abuse occurred
- **Volume trajectory**: 2,388 (2010) → 3,002 (2013) → 4,139 (2016) → 3,832 (2018) → 4,253 (2022) → 4,213 (2023) → 7,608 (2024, SSDO figure)
- **Source methodology**: Monitors 80-91 newspapers across Pakistan. Reports are in English with Urdu summaries.
- **Extraction approach**:
  - Tool: `pdfplumber` for table extraction, `tabula-py` as fallback
  - Strategy: Each report has ~10-15 key tables with consistent column headers across years. Build a template parser per report era (format changed slightly over 15 years). Extract tables into structured JSON, then normalize into unified schema.
  - Challenge: Some years use charts instead of tables for certain breakdowns — use `camelot` or manual digitization for chart data
  - Output schema: `{year, province, district (if available), crime_category, victim_gender, victim_age_bracket, urban_rural, case_count, fir_registered_count}`
- **Claude Code instruction**: Download all 16 PDFs. Build a `sahil_parser.py` module with per-year extraction logic. Extract every table from every report. Normalize into `sahil_incidents` table in Neon. This becomes the primary trend analysis dataset. Province-level data is consistently available; district-level is sporadic (extract when present).

#### 5.2.3 SSDO (Sustainable Social Development Organization) Reports ⭐ P1
- **URL**: https://www.ssdo.org.pk/
- **What it contains**: Uses RTI-obtained official police data (not media monitoring). Complements Sahil.
- **2024 key data**: 7,608 total cases — Sexual abuse (2,954), Kidnapping (2,437), Child labour (895), Physical abuse (683), Child trafficking (586), Child marriage (53)
- **Provincial breakdown**: Punjab (6,083), KP (1,102), Sindh (354), ICT (138), Balochistan (69)
- **Conviction rates**: Mostly under 1% across categories
- **Punjab H1 2025 district hotspots**: Lahore, Gujranwala, Faisalabad, Rawalpindi, Sialkot
- **Format**: PDF reports + press conference data
- **Extraction**: PDF parsing similar to Sahil. Check for annual reports at `/media/` and `/reports/` paths.
- **Unique value**: Official police records rather than newspaper monitoring — provides conviction rate data that Sahil doesn't.
- **Claude Code instruction**: Scrape all available SSDO reports. Parse into `ssdo_incidents` table. Key advantage: conviction rate data by category and province.

#### 5.2.4 ZARRA Missing Children Data P2
- **URL**: https://zarra.mohr.gov.pk/ (web portal) 
- **PDF Report**: https://mohr.gov.pk/SiteImage/Misc/files/ZARRA%20Data%20Analysis%20Report%20Oct,%202021%20-%20June,%202022.pdf
- **What it contains**: Pakistan's national missing/abducted children database. 3,639 total cases processed; 2,130 successful closures; 592 open cases. District-level data with geo-tags.
- **Fields**: Child photo, name, age, district of disappearance, case status (active/recovered), reporting source
- **Provincial distribution**: Punjab ~72%, Sindh ~11%, KP ~3%, Balochistan ~2%, ICT ~6%
- **Format**: Web app (JS-rendered, requires registration), mobile app (AWAZ), PDF analysis reports
- **Extraction approach**: 
  - **Short term**: Parse published PDF analysis reports from MoHR website
  - **Long term**: Negotiate formal data sharing agreement with MoHR for API access
- **Claude Code instruction**: Download and parse ZARRA PDF reports. Extract district-level case counts. For ongoing monitoring, check MoHR website monthly for new PDF publications at predictable URL pattern: `mohr.gov.pk/SiteImage/Misc/files/ZARRA*`

#### 5.2.5 StateOfChildren.com (NCRC Portal) ⭐ P1
- **URL**: https://stateofchildren.com/children-dataset/
- **What it contains**: NCRC-operated aggregation portal with Sahil summary tables, ZARRA data, education/health/justice datasets — all in HTML table format
- **Format**: Standard HTML tables — the EASIEST government child protection source to scrape
- **Claude Code instruction**: Scrape all HTML tables from `/children-dataset/`, `/helplines/`, and related pages. This is a quick win — clean data, no authentication, simple BeautifulSoup extraction.

---

### 5.3 INTERNATIONAL ORGANIZATION DATA (P0-P1)

#### 5.3.1 US State Department TIP Report — Pakistan ⭐ P1
- **URL pattern**: `https://www.state.gov/reports/{YEAR}-trafficking-in-persons-report/pakistan/` (2001–2025)
- **Pre-2017 URL**: `https://2009-2017.state.gov/j/tip/rls/tiprpt/countries/...`
- **What it contains**: The single best longitudinal dataset on anti-trafficking enforcement in Pakistan. 24+ years of annual data.
- **Data per year**:
  - Tier ranking (Pakistan: Tier 2 Watch List historically, Tier 2 since 2022)
  - Number of investigations, prosecutions, convictions (disaggregated by PTPA vs. PPC)
  - Victim identification numbers
  - Budget allocations
  - Specific trafficking types documented (brick kiln bonded labor, domestic servitude, begging rings, sex trafficking, cross-border)
  - Provincial breakdown of enforcement (Punjab reports 98% of convictions)
  - Named hotspot locations and routes
- **2025 specific data**: 1,607 PTPA investigations (523 sex trafficking, 915 forced labor, 169 unspecified); 495 convictions; PPC cases: 23,629 investigations; 4.5M estimated bonded laborers; 19,954 victims identified
- **Format**: Clean HTML country pages (post-2017) + full PDF reports (all years)
- **Scraping feasibility**: EXCELLENT. No authentication, predictable URLs, consistent HTML structure
- **Claude Code instruction**: Build scraper to fetch all 24+ Pakistan country pages. Parse HTML to extract: tier_ranking, investigations_count, prosecutions_count, convictions_count, victims_identified, budget_allocated. Store in `tip_report_annual` table. Also extract qualitative named locations/routes into `tip_report_locations` table for geo-coding.

#### 5.3.2 US DOL Child Labor Report — Pakistan P1
- **URL**: https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan
- **PDF pattern**: `https://www.dol.gov/sites/dolgov/files/ILAB/child_labor_reports/tda{YEAR}/Pakistan.pdf`
- **Key data**: Working children ages 10-14: 9.8% (2,261,704). Sector breakdown: Agriculture 69.4%, Services 19.7%, Industry 10.9%. Provincial enforcement data.
- **Claude Code instruction**: Download all annual PDFs (2004-2023). Parse standardized tables for child labor statistics, enforcement actions, and legal framework compliance scores.

#### 5.3.3 UNODC Data Portal P1
- **URL**: https://dataunodc.un.org/dp-trafficking-persons
- **What it contains**: Interactive query tool with detected victims by country, age, sex, exploitation type, citizenship. CSV/Excel download available.
- **Pakistan-specific**: 800+ sex trafficking cases, 11,803 victims referred by provincial police
- **Global Reports**: https://www.unodc.org/unodc/data-and-analysis/glotip.html (biennial: 2009–2024)
- **GLO.ACT Pakistan**: https://www.unodc.org/documents/human-trafficking/GLO-ACTII/ (multiple PDFs)
- **Claude Code instruction**: Use data portal's download function to get Pakistan-filtered CSV. Parse GLO.ACT PDFs for Pakistan-specific program data and awareness survey results.

#### 5.3.4 Walk Free / Global Slavery Index P0
- **URL**: https://www.walkfree.org/global-slavery-index/downloads/
- **Pakistan snapshot**: https://cdn.walkfree.org/content/uploads/2023/09/27164917/GSI-Snapshot-Pakistan.pdf
- **Key data**: 2,349,000 people in modern slavery (2023), 4th globally. Vulnerability score (23 indicators), government response score (141 factors)
- **Format**: CSV/Excel download
- **Claude Code instruction**: Download country-level dataset. Extract Pakistan row with all 23 vulnerability indicators and 141 government response factors. These become comparison benchmarks.

#### 5.3.5 UNICEF MICS Data P2
- **URL**: https://mics.unicef.org/ (MICS Tabulator for custom queries)
- **Microdata**: https://microdata.worldbank.org/ (search "Pakistan MICS")
- **What it contains**: 120+ socioeconomic indicators at divisional/district levels. Child protection module: child labor, child marriage, birth registration (29% in Sindh), child discipline
- **Key Pakistan surveys**: Punjab MICS 2017-18 (district-representative), Sindh MICS 2014
- **Format**: SPSS/CSV microdata (registration required), MICS Tabulator for custom queries
- **Claude Code instruction**: Register for microdata access. Download Punjab MICS 2017-18 and Sindh MICS 2014. Extract child protection module variables at district level. Join to boundaries via district names.

#### 5.3.6 UNICEF Child Marriage Data Portal P0
- **URL**: https://childmarriagedata.org/country-profiles/pakistan/
- **Key data**: 18% married before 18 nationally; Balochistan 49.1% vs Punjab 29.8%. Disaggregated by wealth, rural/urban, education, province
- **Format**: Interactive dashboard (likely has underlying API/data download)
- **Claude Code instruction**: Scrape or download provincial child marriage rates. These are trafficking indicators.

#### 5.3.7 UNHCR Pakistan Data P1
- **URL**: https://reporting.unhcr.org/pakistan
- **Refugee Data Finder API**: https://www.unhcr.org/refugee-statistics/
- **Operational Data Portal**: https://data.unhcr.org/
- **Border Monitoring**: https://microdata.unhcr.org/index.php/catalog/1105 (Afghanistan unofficial crossing points)
- **Key data**: 1.4M+ registered Afghans, 500K+ undocumented. RAHA program: 4,260 projects in 47 specific districts. Refugee settlement locations georeferenced
- **Claude Code instruction**: Use Refugee Data Finder API for structured data. Download RAHA project locations for district-level refugee presence mapping. Extract unofficial border crossing coordinates from border monitoring data.

#### 5.3.8 IOM Migration Data Portal P1
- **URL**: https://www.migrationdataportal.org/themes/human-trafficking
- **Pakistan Migration Snapshot**: https://dtm.iom.int/sites/g/files/tmzbdl1461/files/reports/Pakistan%20Migration%20Snapshot%20Final.pdf
- **Claude Code instruction**: Parse migration snapshot PDF for trafficking-relevant migration flow data.

#### 5.3.9 DHS 2017-18 Pakistan P2
- **URL**: https://dhsprogram.com/ (registration required, free)
- **API**: https://api.dhsprogram.com/
- **Coverage**: 8 regions (not district-level), but GPS cluster coordinates available
- **Claude Code instruction**: Register for DHS data access. Use API for programmatic access. GPS clusters can be spatial-joined to districts for sub-regional estimates.

#### 5.3.10 World Bank Data P0
- **API**: https://api.worldbank.org/v2/country/PAK/indicator/
- **Key indicators**: GDP per capita, poverty headcount ratio, school enrollment, literacy rate — all as time series
- **Relative Wealth Index**: Via Meta Data for Good — 2.4km grid resolution poverty mapping
- **Claude Code instruction**: Use World Bank API to pull all relevant indicators. Download Relative Wealth Index raster for spatial overlay.

---

### 5.4 GOVERNMENT REPORTS & POLICY DATA (P1-P2)

#### 5.4.1 FIA Annual Reports P2
- **URL**: https://www.fia.gov.pk/
- **PDFs**: `/files/publications/686234992.pdf` (2024), `/files/publications/1069384536.pdf` (2019)
- **National Action Plan**: `/files/immigration/1815351109.pdf`
- **Data**: Case counts by year, deportee statistics, trafficking routes, AHTC personnel (781 staff)
- **Challenge**: Server unstable (ConnectTimeout). PDF extraction required.
- **Claude Code instruction**: Download all available PDFs when server responds. Parse for annual case statistics, route data, and AHTC contact information (geocode AHTC locations).

#### 5.4.2 PBS PSLM Microdata ⭐ P1
- **URL**: https://www.pbs.gov.pk/pslm-3/ and https://pslm-sdgs.data.gov.pk/
- **What it contains**: 195,000 household survey covering education enrollment/dropout, health, WASH, food insecurity, migration, disability, ICT access — district-level estimates for all provinces. 21 SDG indicators.
- **Format**: SPSS/Stata microdata on PBS website. Interactive dashboard may have API endpoints.
- **Claude Code instruction**: Download PSLM 2019-20 microdata. Calculate district-level vulnerability indicators: out-of-school children rate, food insecurity rate, migration rate. These are PREDICTIVE indicators for trafficking risk.

#### 5.4.3 PBS Labour Force Survey P1
- **URL**: https://www.pbs.gov.pk/labour-force-statistics/
- **Key findings PDF**: https://www.pbs.gov.pk/sites/default/files/labour_force/publications/lfs2020_21/Key_Findings_of_Labour_Force_Survey_2020-21.pdf
- **Data**: Employment by province/district/sex/age, child labor indicators (10-14 age group), NEET data
- **Claude Code instruction**: Download LFS publications. Extract child labor statistics by province and, where available, by district.

#### 5.4.4 NCRC Annual Report P2
- **URL**: https://ncrc.gov.pk/wp-content/uploads/2025/07/Annual-Report-24-25.pdf
- **What it contains**: First comprehensive State of Children report covering health, education, protection, welfare
- **Claude Code instruction**: Download and parse for trafficking/child protection data points, policy recommendations, and provincial breakdowns.

#### 5.4.5 NCSW/UNICEF Violence Against Children Mapping Study (2024) P1
- **URL**: https://ngdp-ncsw.org.pk/storage/6865729cf1528.pdf
- **What it contains**: District-level violence rates including 121 trafficking cases and 53 child marriage cases across 4 provinces
- **Claude Code instruction**: Parse this PDF — it contains rare DISTRICT-LEVEL trafficking case data that most sources lack.

#### 5.4.6 UK DFID Modern Slavery in Pakistan Report (2019) P2
- **URL**: https://assets.publishing.service.gov.uk/media/5e56a35a86650c53b6909337/DFID_Modern_Slavery_in_Pakistan_.pdf
- **Claude Code instruction**: Parse for sector-specific data (brick kilns, agriculture, domestic work) and geographic hotspot identification.

---

### 5.5 COURT & LEGAL DATA (P2-P3)

#### 5.5.1 Court Systems Overview

| Court | URL | Auth | JS Required | Scraping Tool |
|-------|-----|------|-------------|---------------|
| Supreme Court | https://supremecourt.nadra.gov.pk/judgement-search/ | No | Minimal | Requests + BS4 |
| Lahore HC | https://data.lhc.gov.pk/reported_judgments/ | No | Minimal | Requests + BS4 |
| Sindh HC (5 benches) | https://cases.shc.gov.pk/{khi,suk,hyd,lar,mpkhas} | No | Minimal | Requests + BS4 |
| Peshawar HC (4 benches) | https://peshawarhighcourt.gov.pk/app/site/15/p/Search_For_Case.html | No | Minimal | Requests + BS4 |
| Balochistan HC | https://portal.bhc.gov.pk/case-status/ | Unknown | YES (SPA) | Playwright |
| Islamabad HC | https://mis.ihc.gov.pk/frmCseSrch | No | Moderate | Requests (ASP.NET ViewState) |
| Punjab District Courts | https://dsj.punjab.gov.pk/ | Partial | Moderate | Mixed |
| Sindh District Courts | https://cases.districtcourtssindh.gos.pk/ | No | Minimal | Requests + BS4 |
| CommonLII (FREE) | https://www.commonlii.org/resources/245.html | No | No | Scrapy (bulk) |

**Critical limitation**: No Pakistani court allows searching by criminal offense. Must search by case type (Criminal Appeal, Criminal Petition) then keyword-filter.

**Relevant PPC sections**: 366-A (kidnapping woman to compel marriage), 366-B (importation of girl), 369 (kidnapping child under 10), 370 (buying/selling person for slavery), 371-A (selling person for prostitution), 371-B (buying person for prostitution)

**Relevant statutes**: Prevention of Trafficking in Persons Act 2018, Zainab Alert Act 2020, Punjab Destitute and Neglected Children Act 2004, Bonded Labour System (Abolition) Act 1992

#### 5.5.2 Legal Research Platforms

| Platform | URL | Access | Priority |
|----------|-----|--------|----------|
| CommonLII | https://www.commonlii.org/resources/245.html | FREE | P1 — start here |
| PakistanLawSite | https://www.pakistanlawsite.com/ | Rs. 36,000/year | P3 (ToS prohibits bulk download) |
| Pak Legal Database | https://www.paklegaldatabase.com/ | Subscription | P3 |
| legislation.pk | https://www.legislation.pk/ | FREE | P1 — for statute text |

#### 5.5.3 Court Scraping Strategy

**Phase 1**: Bulk download all freely available SCP decisions from CommonLII (2002-2011). Use keyword search for trafficking terms in English and Urdu.

**Phase 2**: Build targeted scrapers for each High Court. Search strategy: iterate all Criminal case types for each year, download judgment PDFs, run NLP pipeline to identify trafficking-related cases.

**Phase 3**: Build NLP extraction pipeline:
- Input: Raw judgment PDF text
- Extract: Date, court, judge name, parties, charges (PPC sections), district of incident, sentence, victim demographics
- Tools: spaCy with custom Pakistan legal NER model
- Output: `court_cases` table with structured fields and geographic identifiers

**Claude Code instruction**: Start with CommonLII bulk scraper. Then build modular High Court scrapers (one per court). Each scraper should: (1) search by Criminal case types, (2) download judgment PDFs, (3) store raw text + metadata in `court_judgments_raw` table, (4) queue for NLP processing.

---

### 5.6 NEWS MEDIA SOURCES (P2)

#### 5.6.1 Newspaper Scraping Registry

| Source | URL | RSS Feed | Paywall | JS | Priority | Scraping Tool |
|--------|-----|----------|---------|-----|----------|---------------|
| Dawn | dawn.com | `dawn.com/feeds/home` | No | No | ★★★★★ | Scrapy |
| Express Tribune | tribune.com.pk | `/feed` (WordPress) | No | No | ★★★★★ | Scrapy |
| The News | thenews.com.pk | Available | No | No | ★★★★ | Scrapy |
| Geo News | geo.tv | None | No | Heavy | ★★★★ | Playwright |
| ARY News | arynews.tv | `arynews.tv/feed` | No | No | ★★★ | Scrapy |
| Samaa TV | samaa.tv | Unknown | No | Heavy | ★★★ | Playwright |
| Pakistan Today | pakistantoday.com.pk | Likely (WP) | No | No | ★★★ | Scrapy |

**Express Tribune has a dedicated tag page**: `https://tribune.com.pk/child-trafficking/` — simplifies targeted crawling.

#### 5.6.2 News Aggregation APIs

- **Google News RSS**: `https://news.google.com/rss/search?q=child+trafficking+Pakistan&hl=en-PK&gl=PK`
- **NewsAPI.org**: JSON API with Pakistani sources included
- **NewsData.io**: Alternative news API

#### 5.6.3 News NER Pipeline

Every news article must pass through:

1. **Fetch** article text (RSS → full article via `web_fetch` or Scrapy)
2. **Classify** as trafficking-relevant (binary classifier using keywords + ML model)
3. **Extract entities**: 
   - Geographic: district, city, province, specific location (e.g., "brick kiln near Sheikhupura")
   - Temporal: date of incident
   - Victim: age, gender, count
   - Perpetrator: role (family, stranger, employer, gang)
   - Crime type: kidnapping, bonded labor, sexual exploitation, organ trafficking, begging
4. **Geocode** extracted locations using Pakistan gazetteer → lat/lon
5. **Store** in `news_incidents` table with source URL, extraction confidence scores, and geometry

**Custom Pakistan Gazetteer** requirements:
- All 160+ district names with alternative spellings (both English and Urdu transliterations)
- All major cities (500+ cities/towns)
- Known trafficking-relevant locations: brick kiln areas, border towns, bus stations, truck stops, shrines
- Regex patterns for Pakistani location references: "near [location]", "[location] district", "tehsil [name]"

**Claude Code instruction**: Build `pakistan_gazetteer.json` with 3000+ location entries. Each entry: `{name, variants: [], lat, lon, admin_level, district_pcode}`. Use as lookup for spaCy NER pipeline.

---

### 5.7 ACADEMIC & RESEARCH SOURCES (P2-P3)

| Source | URL | Key Content | Format |
|--------|-----|-------------|--------|
| Aurat Foundation Internal Trafficking Study | https://af.org.pk/gep/images/Research%20Studies%20(Gender%20Based%20Violence)/study%20on%20trafficking%20final.pdf | Internal trafficking routes, victim profiles, district-level field data | PDF |
| SDPI Child Trafficking Project (ILO-funded) | https://sdpi.org/sdpiweb/publications/files/2004-05.pdf | Swat Valley community-level surveys | PDF |
| LUMS CBS Child Labor Analysis | https://cbs.lums.edu.pk/student-research-series/child-labor-pakistan-policy-analysis | Policy analysis with data | PDF |
| ECPAT Pakistan Reports | https://ecpat.org/wp-content/uploads/2022/03/Gobal-Boys-Initiative_Pakistan-Report_FINAL.pdf | Hotspot identification (hotels, truck stops, shrines, mining) | PDF |
| ECPAT Supplementary Report | https://pahchaan.info/wp-content/uploads/2025/05/Supplementary-report-on-Sexual-Exploitation-of-Children-in-Pakistan.pdf | Prosecution data, legal framework analysis | PDF |
| HRW 1995 Bonded Labor Report | https://www.hrw.org/legacy/reports/1995/Pakistan.htm | Named brick kiln sites, district-specific data (historical baseline) | HTML |
| HRCP Modern Slavery Report | https://hrcp-web.org/hrcpweb/wp-content/uploads/2020/09/2022-Modern-slavery-1.pdf | Province-by-province trafficking analysis | PDF |
| Organized Crime Index — Pakistan | https://ocindex.net/country/pakistan | Structured crime assessment scores | Web (likely has API) |
| Google Scholar papers | Search: "child trafficking Pakistan", "bonded labor Pakistan children" | District-level field research | PDF (via ResearchGate) |

**Claude Code instruction**: Download all PDFs. Parse for any quantitative data (tables, statistics) and qualitative geographic references (named locations, routes, hotspots). Store academic data points in `research_data` table.

---

### 5.8 HELPLINE & REPORTING DATA (P3)

| Source | Contact | Data Held | Public Access |
|--------|---------|-----------|---------------|
| Roshni Helpline | 0800-22444 / https://roshnihelpline.org/ | 13,000+ children recovered since 2003; 2,633 missing cases (2023) | Press releases only |
| Madadgaar (LHRLA) | 1098 / http://madadgaar.org/ | 223,000+ calls; 71 data categories | Internal only |
| MoHR Helpline | 1099 | Case tracking, referrals | Internal (ZARRA linked) |
| Legal Aid Society SLACC | https://www.las.org.pk/nazassist/ | 475,000+ calls from 600+ towns since 2014 | Limited |

**These are P3 because data is internal.** Strategy: (1) extract whatever is in press releases/annual reports, (2) explore formal data sharing agreements.

---

### 5.9 PROVINCIAL POLICE DATA (P2-P3)

#### Punjab Police (Most Accessible)
- **Missing persons**: https://punjabpolice.gov.pk/missing-persons (quarterly lists)
- **Crime statistics**: https://punjabpolice.gov.pk/crimestatistics
- **e-FIR system**: 878K+ FIRs since 2017 — entirely behind police authentication
- **Claude Code instruction**: Scrape public missing persons lists and crime statistics pages. For e-FIR data, pursue RTI request (see SSDO methodology).

#### Sindh Police
- **Crime stats**: https://sindhpolice.gov.pk/annoucements/crime_stat_all_cities.html
- **Missing persons**: https://sindhpolice.gov.pk/missing_person.html (403 blocked)
- **Claude Code instruction**: Scrape crime_stat_all_cities.html for range-level (Karachi, Hyderabad, Sukkur, Larkana) crime data. Monitor for missing_person page becoming accessible.

#### KP Police
- **URL**: https://www.kppolice.gov.pk/
- **Status**: No public crime statistics found online. 403 errors on most data pages.
- **CPWC has facts page**: https://kpcpwc.gov.pk/factsandfigure.html — SCRAPE THIS

#### Balochistan Police
- **Crime stats**: https://balochistanpolice.gov.pk/crime_statistics
- **Subsections**: All Crime, Major Crime Heads, Terrorism
- **Claude Code instruction**: Scrape all crime_statistics subsections.

---

## 6. SCRAPER & PIPELINE SPECIFICATIONS

### 6.1 Pipeline Architecture

```
                    ┌──────────────────┐
                    │   SCHEDULER      │
                    │  (Celery Beat)   │
                    └───────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
    ┌─────────▼──┐  ┌──────▼─────┐  ┌───▼────────┐
    │ SCRAPERS   │  │ DOWNLOADERS│  │ API CLIENTS │
    │ (Scrapy/   │  │ (PDF/CSV   │  │ (REST/JSON  │
    │ Playwright)│  │  fetchers) │  │  fetchers)  │
    └─────────┬──┘  └──────┬─────┘  └───┬────────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                    ┌───────▼──────────┐
                    │   RAW STORAGE    │
                    │   (S3 bucket)    │
                    └───────┬──────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
    ┌─────────▼──┐  ┌──────▼─────┐  ┌───▼────────┐
    │ PDF PARSER │  │ HTML PARSER│  │ CSV LOADER  │
    │ (pdfplumber│  │ (BS4/lxml) │  │ (pandas)    │
    │  + tabula) │  │            │  │             │
    └─────────┬──┘  └──────┬─────┘  └───┬────────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
                    ┌───────▼──────────┐
                    │  NER / GEOCODER  │
                    │  (spaCy + gazet) │
                    └───────┬──────────┘
                            │
                    ┌───────▼──────────┐
                    │ NEON PostgreSQL   │
                    │ + PostGIS         │
                    └──────────────────┘
```

### 6.2 Scraper Schedule

| Scraper | Frequency | Source | Tool |
|---------|-----------|--------|------|
| `news_rss_scraper` | Every 6 hours | Dawn, Tribune, The News, ARY RSS feeds | Scrapy |
| `news_js_scraper` | Daily | Geo News, Samaa TV | Playwright |
| `sahil_checker` | Monthly | sahil.org/cruel-numbers/ | Requests |
| `tip_report_scraper` | Annually (June) | state.gov TIP Report | Requests + BS4 |
| `ctdc_updater` | Quarterly | ctdatacollaborative.org | Direct CSV download |
| `unodc_data_fetcher` | Biennial | dataunodc.un.org | Direct CSV download |
| `court_scraper_scp` | Weekly | Supreme Court | Requests (ASP.NET) |
| `court_scraper_lhc` | Weekly | Lahore HC | Requests + BS4 |
| `court_scraper_shc` | Weekly | Sindh HC (5 benches) | Requests + BS4 |
| `court_scraper_phc` | Weekly | Peshawar HC (4 benches) | Requests + BS4 |
| `court_scraper_bhc` | Weekly | Balochistan HC | Playwright |
| `court_scraper_ihc` | Weekly | Islamabad HC | Requests (ASP.NET) |
| `punjab_police_scraper` | Monthly | punjabpolice.gov.pk | Requests + BS4 |
| `sindh_police_scraper` | Monthly | sindhpolice.gov.pk | Requests + BS4 |
| `kpcpwc_scraper` | Monthly | kpcpwc.gov.pk | Requests + BS4 |
| `stateofchildren_scraper` | Monthly | stateofchildren.com | Requests + BS4 |
| `mohr_pdf_checker` | Monthly | mohr.gov.pk | Requests |
| `ssdo_report_checker` | Monthly | ssdo.org.pk | Requests |
| `worldbank_api` | Quarterly | api.worldbank.org | REST API |
| `unhcr_api` | Quarterly | unhcr.org/refugee-statistics | REST API |

### 6.3 Python Dependencies

```
# Scraping
scrapy>=2.11
playwright>=1.40
requests>=2.31
beautifulsoup4>=4.12
lxml>=5.1

# PDF Extraction
pdfplumber>=0.10
tabula-py>=2.9
camelot-py>=0.11
pytesseract>=0.3  # OCR for scanned PDFs

# NLP
spacy>=3.7
# Download: python -m spacy download en_core_web_trf

# Geospatial
geopandas>=0.14
shapely>=2.0
pyproj>=3.6
geopy>=2.4  # Geocoding

# Data Processing
pandas>=2.1
numpy>=1.26

# Database
sqlalchemy>=2.0
geoalchemy2>=0.14  # PostGIS support
asyncpg>=0.29  # Async PostgreSQL for FastAPI
alembic>=1.13  # Migrations

# Task Queue
celery>=5.3
redis>=5.0

# API Framework
fastapi>=0.109
uvicorn>=0.27
pydantic>=2.5
```

---

## 7. DATABASE SCHEMA

### Neon PostgreSQL + PostGIS

**Enable PostGIS**: `CREATE EXTENSION postgis;`

### 7.1 Core Tables

```sql
-- Administrative boundaries (loaded from HDX GeoJSON)
CREATE TABLE boundaries (
    id SERIAL PRIMARY KEY,
    admin_level INT NOT NULL,  -- 0=country, 1=province, 2=district, 3=tehsil
    name_en VARCHAR(255) NOT NULL,
    name_ur VARCHAR(255),
    pcode VARCHAR(20) UNIQUE NOT NULL,  -- OCHA P-code (universal join key)
    parent_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL,
    population_total BIGINT,
    population_male BIGINT,
    population_female BIGINT,
    population_urban BIGINT,
    population_rural BIGINT,
    area_sqkm FLOAT
);
CREATE INDEX idx_boundaries_geom ON boundaries USING GIST(geometry);
CREATE INDEX idx_boundaries_pcode ON boundaries(pcode);
CREATE INDEX idx_boundaries_admin ON boundaries(admin_level);

-- District name crosswalk for fuzzy matching
CREATE TABLE district_name_variants (
    id SERIAL PRIMARY KEY,
    variant_name VARCHAR(255) NOT NULL,
    canonical_pcode VARCHAR(20) NOT NULL REFERENCES boundaries(pcode),
    source VARCHAR(100),  -- Which dataset uses this variant
    UNIQUE(variant_name, source)
);

-- Master incidents table (normalized from all sources)
CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,  -- sahil, ssdo, zarra, news, court, tip_report, ctdc
    source_id VARCHAR(255),  -- Original ID from source
    source_url TEXT,
    
    -- Temporal
    incident_date DATE,
    report_date DATE,
    year INT NOT NULL,
    month INT,
    
    -- Geographic
    district_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    province_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    location_detail TEXT,  -- "near brick kiln in Sheikhupura" etc.
    geometry GEOMETRY(Point, 4326),  -- lat/lon if available
    geocode_confidence FLOAT,  -- 0-1 confidence of geocoding
    
    -- Classification
    incident_type VARCHAR(50) NOT NULL,  -- kidnapping, sexual_abuse, bonded_labor, trafficking, child_marriage, begging, organ_trafficking, missing
    sub_type VARCHAR(100),
    
    -- Victim demographics
    victim_count INT DEFAULT 1,
    victim_gender VARCHAR(20),  -- male, female, mixed, unknown
    victim_age_min INT,
    victim_age_max INT,
    victim_age_bracket VARCHAR(20),  -- 0-5, 6-10, 11-15, 16-18
    
    -- Perpetrator
    perpetrator_type VARCHAR(50),  -- acquaintance, stranger, family, employer, gang, unknown
    perpetrator_count INT,
    
    -- Case status
    fir_registered BOOLEAN,
    case_status VARCHAR(50),  -- reported, investigated, prosecuted, convicted, acquitted, pending
    conviction BOOLEAN,
    sentence_detail TEXT,
    
    -- Metadata
    extraction_confidence FLOAT,  -- NLP confidence score
    raw_text TEXT,  -- Original text for audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_incidents_geom ON incidents USING GIST(geometry);
CREATE INDEX idx_incidents_district ON incidents(district_pcode);
CREATE INDEX idx_incidents_year ON incidents(year);
CREATE INDEX idx_incidents_type ON incidents(incident_type);
CREATE INDEX idx_incidents_source ON incidents(source_type);

-- Brick kilns (loaded from Zenodo)
CREATE TABLE brick_kilns (
    id SERIAL PRIMARY KEY,
    geometry GEOMETRY(Point, 4326) NOT NULL,
    kiln_type VARCHAR(20),  -- FCBK, ZigZag
    nearest_school_m FLOAT,
    nearest_hospital_m FLOAT,
    population_1km INT,
    district_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    source VARCHAR(100) DEFAULT 'zenodo_2024'
);
CREATE INDEX idx_kilns_geom ON brick_kilns USING GIST(geometry);
CREATE INDEX idx_kilns_district ON brick_kilns(district_pcode);

-- Border crossings
CREATE TABLE border_crossings (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    border_country VARCHAR(50) NOT NULL,  -- afghanistan, iran, india, china
    crossing_type VARCHAR(50),  -- official, unofficial
    geometry GEOMETRY(Point, 4326) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    vulnerability_score FLOAT,  -- Calculated based on incident density nearby
    notes TEXT
);
CREATE INDEX idx_border_geom ON border_crossings USING GIST(geometry);

-- Trafficking routes (constructed from TIP reports, FIA data, research)
CREATE TABLE trafficking_routes (
    id SERIAL PRIMARY KEY,
    route_name VARCHAR(255),
    origin_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    origin_country VARCHAR(50),
    destination_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    destination_country VARCHAR(50),
    transit_points JSONB,  -- Array of {name, lat, lon, pcode}
    route_geometry GEOMETRY(LineString, 4326),
    trafficking_type VARCHAR(50),  -- labor, sexual, organ, begging, marriage
    evidence_source TEXT,
    confidence_level VARCHAR(20),  -- high, medium, low
    year_documented INT,
    notes TEXT
);

-- Court judgments
CREATE TABLE court_judgments (
    id SERIAL PRIMARY KEY,
    court_name VARCHAR(100) NOT NULL,
    court_bench VARCHAR(100),
    case_number VARCHAR(255),
    judgment_date DATE,
    judge_names TEXT[],
    
    -- Parties
    appellant TEXT,
    respondent TEXT,
    
    -- Classification
    ppc_sections TEXT[],  -- Array of PPC sections (366-A, 370, etc.)
    statutes TEXT[],  -- PTPA, Zainab Alert Act, etc.
    is_trafficking_related BOOLEAN,
    trafficking_type VARCHAR(50),
    
    -- Geographic
    incident_district_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    court_district_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    
    -- Outcome
    verdict VARCHAR(50),  -- convicted, acquitted, dismissed, pending
    sentence TEXT,
    sentence_years FLOAT,
    
    -- Raw data
    judgment_text TEXT,
    pdf_url TEXT,
    source_url TEXT,
    nlp_confidence FLOAT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_judgments_date ON court_judgments(judgment_date);
CREATE INDEX idx_judgments_district ON court_judgments(incident_district_pcode);
CREATE INDEX idx_judgments_sections ON court_judgments USING GIN(ppc_sections);

-- Vulnerability indicators (per district, per year)
CREATE TABLE vulnerability_indicators (
    id SERIAL PRIMARY KEY,
    district_pcode VARCHAR(20) NOT NULL REFERENCES boundaries(pcode),
    year INT NOT NULL,
    
    -- Education
    school_enrollment_rate FLOAT,
    school_dropout_rate FLOAT,
    out_of_school_children INT,
    literacy_rate FLOAT,
    
    -- Economic
    poverty_headcount_ratio FLOAT,
    food_insecurity_rate FLOAT,
    child_labor_rate FLOAT,
    unemployment_rate FLOAT,
    
    -- Demographic
    population_under_18 INT,
    birth_registration_rate FLOAT,
    child_marriage_rate FLOAT,
    refugee_population INT,
    
    -- Infrastructure
    brick_kiln_count INT,
    brick_kiln_density_per_sqkm FLOAT,
    distance_to_border_km FLOAT,
    
    -- Disaster
    flood_affected_pct FLOAT,
    
    -- Composite score
    trafficking_risk_score FLOAT,  -- Calculated composite 0-100
    
    source VARCHAR(100),
    UNIQUE(district_pcode, year)
);

-- TIP Report annual data (time series)
CREATE TABLE tip_report_annual (
    id SERIAL PRIMARY KEY,
    year INT UNIQUE NOT NULL,
    tier_ranking VARCHAR(50),
    
    -- PTPA cases
    ptpa_investigations INT,
    ptpa_prosecutions INT,
    ptpa_convictions INT,
    ptpa_sex_trafficking_inv INT,
    ptpa_forced_labor_inv INT,
    
    -- PPC cases
    ppc_investigations INT,
    ppc_prosecutions INT,
    ppc_convictions INT,
    
    -- Victims
    victims_identified INT,
    victims_referred INT,
    
    -- Budget
    budget_allocated_pkr BIGINT,
    
    -- Qualitative
    key_findings TEXT,
    recommendations TEXT,
    named_hotspots TEXT[],
    
    source_url TEXT
);

-- Public reports (citizen submissions)
CREATE TABLE public_reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,  -- suspicious_activity, missing_child, bonded_labor, begging_ring, other
    description TEXT,
    
    -- Location
    geometry GEOMETRY(Point, 4326),
    district_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    address_detail TEXT,
    
    -- Evidence
    photos JSONB,  -- Array of S3 URLs
    
    -- Reporter (anonymous allowed)
    reporter_name VARCHAR(255),
    reporter_contact VARCHAR(255),
    is_anonymous BOOLEAN DEFAULT true,
    
    -- Status
    status VARCHAR(50) DEFAULT 'submitted',  -- submitted, verified, referred, resolved, rejected
    referred_to VARCHAR(255),  -- Which agency it was referred to
    
    -- Metadata
    ip_hash VARCHAR(64),  -- Hashed IP for abuse prevention (NOT for identification)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_reports_geom ON public_reports USING GIST(geometry);
CREATE INDEX idx_reports_status ON public_reports(status);
CREATE INDEX idx_reports_type ON public_reports(report_type);

-- News articles
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    published_date DATE,
    
    -- Extracted data
    extracted_incidents JSONB,  -- Array of extracted incident objects
    extracted_locations JSONB,  -- Array of {name, lat, lon, confidence}
    extracted_entities JSONB,   -- NER results
    
    -- Classification
    is_trafficking_relevant BOOLEAN,
    relevance_score FLOAT,
    
    -- Raw
    full_text TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_news_date ON news_articles(published_date);
CREATE INDEX idx_news_source ON news_articles(source_name);

-- Data sources registry (for audit and freshness tracking)
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT,
    source_type VARCHAR(50),  -- government, ngo, international, news, academic, citizen
    priority VARCHAR(5),  -- P0, P1, P2, P3
    last_scraped TIMESTAMP,
    last_updated TIMESTAMP,
    scraper_name VARCHAR(100),
    record_count INT,
    is_active BOOLEAN DEFAULT true,
    notes TEXT
);
```

---

## 8. GEO-MAPPING ENGINE

### 8.1 Map Layers (Toggle-able in Frontend)

| Layer | Data Source | Geometry Type | Color Scheme |
|-------|-----------|---------------|-------------|
| **District Boundaries** | HDX COD-AB | Polygon | Neutral gray borders |
| **Incident Heat Map** | incidents table | Point → heatmap | Red gradient (intensity = count) |
| **Brick Kilns** | brick_kilns table | Point markers | Orange dots (size = population_1km) |
| **Border Crossings** | border_crossings table | Point markers | Red triangles (size = vulnerability) |
| **Trafficking Routes** | trafficking_routes table | LineString | Red dashed lines (thickness = evidence confidence) |
| **Missing Children** | incidents WHERE type='missing' | Point markers | Blue pulsing dots |
| **Poverty Index** | vulnerability_indicators | Polygon choropleth | Purple gradient (darker = higher poverty) |
| **School Dropout** | vulnerability_indicators | Polygon choropleth | Orange gradient |
| **Flood Affected** | flood_extent_2022 | Polygon | Blue overlay (20% opacity) |
| **Refugee Settlements** | UNHCR data | Point clusters | Green dots |
| **Conviction Rate** | court_judgments aggregated | Polygon choropleth | Green-red (green = higher rate) |
| **Public Reports** | public_reports | Point markers | Yellow pins |

### 8.2 Spatial Queries (PostGIS)

```sql
-- Find all incidents within 10km of a brick kiln
SELECT i.* FROM incidents i
JOIN brick_kilns bk ON ST_DWithin(i.geometry::geography, bk.geometry::geography, 10000);

-- Calculate district-level incident density
SELECT b.pcode, b.name_en, COUNT(i.id) as incident_count,
       COUNT(i.id)::float / (b.population_total / 100000) as per_100k
FROM boundaries b
LEFT JOIN incidents i ON b.pcode = i.district_pcode
WHERE b.admin_level = 2
GROUP BY b.pcode, b.name_en, b.population_total;

-- Identify hotspot clusters (districts with incidents AND high kiln density)
SELECT b.pcode, b.name_en,
       COUNT(DISTINCT i.id) as incidents,
       COUNT(DISTINCT bk.id) as kilns,
       vi.poverty_headcount_ratio,
       vi.school_dropout_rate
FROM boundaries b
JOIN incidents i ON b.pcode = i.district_pcode
JOIN brick_kilns bk ON ST_Contains(b.geometry, bk.geometry)
LEFT JOIN vulnerability_indicators vi ON b.pcode = vi.district_pcode
WHERE b.admin_level = 2
GROUP BY b.pcode, b.name_en, vi.poverty_headcount_ratio, vi.school_dropout_rate
HAVING COUNT(DISTINCT i.id) > 10
ORDER BY incidents DESC;
```

### 8.3 Frontend Map Implementation

**Library**: Mapbox GL JS with Deck.gl for advanced layers

```
Next.js App Router Structure:
/app
  /page.tsx                    -- Landing page
  /map
    /page.tsx                  -- Main interactive map
    /components
      /MapContainer.tsx        -- Mapbox GL wrapper
      /LayerControls.tsx       -- Toggle panel for map layers
      /DistrictPopup.tsx       -- Click-on-district info card
      /IncidentTimeline.tsx    -- Time slider for temporal filtering
      /SearchBar.tsx           -- Location + incident search
  /dashboard
    /page.tsx                  -- Trend analysis dashboard
    /components
      /TrendCharts.tsx         -- Recharts time series
      /ProvinceComparison.tsx  -- Province bar charts
      /CaseTypeBreakdown.tsx   -- Pie/donut charts
      /ConvictionRates.tsx     -- Prosecution vs conviction
  /report
    /page.tsx                  -- Public incident reporting form
    /success/page.tsx          -- Submission confirmation
  /district/[pcode]
    /page.tsx                  -- "Know Your District" profile
  /legal
    /page.tsx                  -- Court judgment search
  /resources
    /page.tsx                  -- Helplines, legal aid, shelters
  /about
    /page.tsx                  -- Project mission and methodology
  /api                         -- Next.js API routes (proxying to FastAPI)
```

---

## 9. FRONTEND APPLICATION

### 9.1 Tech Stack

- **Framework**: Next.js 14+ (App Router, Server Components)
- **Hosting**: Vercel (free tier → Pro as traffic grows)
- **Styling**: Tailwind CSS + shadcn/ui
- **Maps**: Mapbox GL JS + react-map-gl + @deck.gl/mapbox
- **Charts**: Recharts
- **Auth**: NextAuth.js (for admin/government portal login)
- **State**: Zustand (lightweight, perfect for map state management)
- **i18n**: next-intl (English + Urdu + Sindhi)
- **PWA**: next-pwa (mobile-first, works offline in areas with poor connectivity)

### 9.2 Key Pages

**Landing Page** (`/`): Dramatic hero with a live counter of documented incidents. Simple messaging: "Pakistan's children deserve a guardian. Nigehbaan maps the invisible." Three CTAs: "Explore the Map", "Report an Incident", "Know Your District". Mobile-optimized.

**Interactive Map** (`/map`): Full-screen map with collapsible layer panel on left. Time slider at bottom for temporal filtering (2010-2024). Click any district to see a popup card with incident count, trend arrow, top incident types, vulnerability score, and "View Full Profile" link. Search bar for district/city lookup. Toggle layers independently. Export visible data as CSV.

**Dashboard** (`/dashboard`): Trend analysis with Recharts. 15-year Sahil data as line charts. Province comparison bar charts. Case type donut chart. Conviction rate trend line. Filters: province, year range, incident type. Print-friendly layout for reports.

**Report Incident** (`/report`): Simple multi-step form. Step 1: What did you see? (category selector). Step 2: Where? (map pin or address input). Step 3: When? (date picker). Step 4: Details (text + photo upload). Step 5: Your info (optional — anonymous by default). Confirmation page with reference number and helpline numbers.

**District Profile** (`/district/[pcode]`): "Know Your District" page. Risk score gauge. Incident trend chart. Brick kiln count. Nearest border crossing. Active missing children alerts. Comparison to national average. Links to relevant helplines and child protection offices for that district.

**Legal Intelligence** (`/legal`): Court judgment search with filters: court, year range, PPC section, outcome. Conviction rate by district choropleth. Judge-level sentencing analysis (anonymized). Legislative gap analysis.

**Resources** (`/resources`): Emergency helplines (1099, 1098, 0800-22444). District-wise child protection offices. Legal aid organizations. NGO directory. How to report trafficking. Available in Urdu.

### 9.3 Design Principles

- **Urdu-first labels**: Map tooltips, district names, and navigation should support Urdu (RTL)
- **Mobile-first**: Most Pakistani citizens will access on mobile. The reporting form MUST work on a Rs. 15,000 Android phone on 3G
- **Offline capability**: PWA with cached district profiles and helpline numbers
- **Color scheme**: Dark map background (Mapbox dark style), warm accent colors (amber/orange for alerts, blue for data points, red for critical hotspots). Never gamify the data — respectful, serious visual language
- **Accessibility**: WCAG 2.1 AA compliant. High contrast text. Screen reader support for charts (aria-labels)
- **Performance**: Static generation for district profiles. ISR for dashboard. Client-side map rendering with Mapbox vector tiles.

---

## 10. BACKEND API

### 10.1 FastAPI Structure

```
/backend
  /app
    /main.py                   -- FastAPI app, CORS, middleware
    /config.py                 -- Environment variables, DB connection
    /models/                   -- SQLAlchemy ORM models
      /boundaries.py
      /incidents.py
      /brick_kilns.py
      /court_judgments.py
      /vulnerability.py
      /public_reports.py
      /news_articles.py
    /schemas/                  -- Pydantic schemas
      /incidents.py
      /reports.py
      /dashboard.py
      /map.py
    /api/
      /v1/
        /map.py                -- GET /map/layers, /map/incidents, /map/kilns, /map/routes
        /dashboard.py          -- GET /dashboard/trends, /dashboard/province-comparison
        /districts.py          -- GET /districts/{pcode}, /districts/{pcode}/profile
        /reports.py            -- POST /reports, GET /reports/{id}
        /legal.py              -- GET /legal/search, /legal/conviction-rates
        /search.py             -- GET /search?q=...
        /export.py             -- GET /export/csv, /export/geojson
    /services/
      /geocoder.py             -- Pakistan-specific geocoding service
      /nlp_pipeline.py         -- spaCy NER for news/court extraction
      /risk_scorer.py          -- Composite vulnerability score calculator
      /spatial_analysis.py     -- PostGIS query builders
    /scrapers/                 -- Celery task definitions
      /sahil_scraper.py
      /tip_report_scraper.py
      /news_scraper.py
      /court_scrapers/
        /scp.py
        /lhc.py
        /shc.py
        /phc.py
        /bhc.py
        /ihc.py
      /police_scrapers/
        /punjab.py
        /sindh.py
    /tasks/
      /celery_app.py           -- Celery configuration
      /schedule.py             -- Celery Beat schedule
    /utils/
      /gazetteer.py            -- Pakistan gazetteer loader
      /pdf_extractor.py        -- pdfplumber/tabula wrapper
      /name_normalizer.py      -- District name matching
```

### 10.2 Key API Endpoints

```
# Map Data
GET  /api/v1/map/boundaries?level=2                    -- District polygons (GeoJSON)
GET  /api/v1/map/incidents?year=2024&type=trafficking   -- Incident points (GeoJSON)
GET  /api/v1/map/kilns?district=PK0401                  -- Brick kiln points (GeoJSON)
GET  /api/v1/map/routes                                 -- Trafficking routes (GeoJSON)
GET  /api/v1/map/heatmap?year=2024                     -- Pre-computed heatmap data
GET  /api/v1/map/borders                                -- Border crossing points

# Dashboard
GET  /api/v1/dashboard/trends?source=sahil&years=2010-2024
GET  /api/v1/dashboard/province-comparison?year=2024
GET  /api/v1/dashboard/case-types?province=PK04
GET  /api/v1/dashboard/conviction-rates?years=2015-2024
GET  /api/v1/dashboard/summary                          -- Top-level stats

# District Profiles
GET  /api/v1/districts                                  -- All districts with basic stats
GET  /api/v1/districts/{pcode}                          -- Full district profile
GET  /api/v1/districts/{pcode}/incidents?years=2020-2024
GET  /api/v1/districts/{pcode}/vulnerability

# Public Reporting
POST /api/v1/reports                                    -- Submit new report
GET  /api/v1/reports/{id}                               -- Check report status

# Legal
GET  /api/v1/legal/search?section=370&court=lhc&year=2023
GET  /api/v1/legal/conviction-rates?level=district

# Search
GET  /api/v1/search?q=kasur+trafficking                -- Full-text search across all data

# Export
GET  /api/v1/export/csv?table=incidents&filters=...
GET  /api/v1/export/geojson?layer=kilns&district=PK0401
```

### 10.3 EC2 Instance Recommendation

- **Instance type**: t3.large (2 vCPU, 8 GB RAM) — sufficient for FastAPI + Celery workers + spaCy NLP model
- **Storage**: 100 GB EBS (for raw PDF storage and scraped data cache)
- **OS**: Ubuntu 22.04 LTS
- **Process manager**: supervisord or systemd for FastAPI (uvicorn), Celery worker, Celery Beat
- **Redis**: ElastiCache t3.micro (or Redis on same EC2 for cost savings during MVP)

---

## 11. AI/ML INTELLIGENCE LAYER

### 11.1 News Classification Model

- **Task**: Binary classification — is this article trafficking-relevant?
- **Approach**: Fine-tune a small transformer (distilbert) on manually labeled subset of Dawn/Tribune articles
- **Features**: Title + first 500 words
- **Training data**: Sahil monitors 80-91 newspapers — their annual report references serve as positive labels

### 11.2 Named Entity Recognition (NER) Pipeline

- **Base model**: spaCy `en_core_web_trf`
- **Custom entities**: `PAKISTAN_DISTRICT`, `PAKISTAN_CITY`, `PAKISTAN_PROVINCE`, `TRAFFICKING_TYPE`, `PPC_SECTION`, `VICTIM_AGE`, `VICTIM_GENDER`
- **Training**: Annotate 500+ Pakistani news articles with custom entity labels
- **Gazetteer augmentation**: 3000+ Pakistan location entries for rule-based matching

### 11.3 Risk Scoring Algorithm

```python
def calculate_risk_score(district_pcode: str) -> float:
    """
    Composite vulnerability score (0-100) based on weighted indicators.
    
    Weights determined by correlation analysis with actual incident data.
    """
    weights = {
        'incident_rate_per_100k': 0.25,      # Historical incident density
        'poverty_headcount_ratio': 0.15,      # Economic vulnerability
        'out_of_school_rate': 0.15,           # Education gaps
        'brick_kiln_density': 0.10,           # Bonded labor infrastructure
        'child_labor_rate': 0.10,             # Existing exploitation
        'border_proximity': 0.05,             # Cross-border trafficking risk
        'flood_affected_pct': 0.05,           # Disaster vulnerability
        'conviction_rate_inverse': 0.05,      # Impunity (lower conviction = higher risk)
        'child_marriage_rate': 0.05,          # Trafficking via marriage
        'refugee_population_ratio': 0.05,     # Displacement vulnerability
    }
    # Normalize each indicator to 0-1, apply weights, sum to 0-100
```

### 11.4 Spatial Clustering

- **Algorithm**: DBSCAN on geocoded incidents
- **Purpose**: Identify geographic clusters of trafficking activity that span district boundaries
- **Output**: Cluster polygons with incident counts, dominant trafficking types, and temporal patterns
- **Visualization**: Displayed as colored cluster boundaries on the map

---

## 12. PUBLIC REPORTING SYSTEM

### 12.1 Report Categories

1. **Suspicious Activity** — "I saw something that doesn't look right" (child begging ring, children being transported in groups, locked premises with children)
2. **Missing Child** — "A child from my community is missing" (links to ZARRA/Roshni)
3. **Bonded Labor** — "Children are working at a brick kiln / factory / farm"
4. **Begging Ring** — "Organized child begging at this location"
5. **Child Marriage** — "An underage marriage is being arranged"
6. **Other** — Free text

### 12.2 Report Flow

```
Citizen submits report (anonymous allowed)
         │
         ▼
Report stored in public_reports table
         │
         ▼
Auto-geocoded to district (if address provided)
         │
         ▼
Displayed on map (after basic validation — no spam, no PII exposure)
         │
         ▼
Flagged for review if it matches existing hotspot patterns
         │
         ▼
Referred to appropriate agency:
  - Missing child → ZARRA / Roshni Helpline
  - Bonded labor → District Labour Officer
  - Criminal activity → Relevant police station / FIA AHTC
  - Child marriage → CPWB/CPA + local administration
```

### 12.3 Safety & Privacy

- Anonymous reporting is the DEFAULT — no personal info required
- Reporter contact info (if provided) is encrypted at rest
- IP addresses are hashed (for abuse prevention only — NOT for identification)
- Reports involving minors never display identifying information publicly
- Photo uploads are stripped of EXIF metadata before storage
- Rate limiting: max 5 reports per IP per day

---

## 13. DEVELOPMENT ROADMAP

### Phase 1 — Foundation (Weeks 1-4)

**Goal**: Base map + structured data loaded + basic API

- [ ] Set up Neon database with PostGIS extension
- [ ] Set up FastAPI project on EC2
- [ ] Set up Next.js project on Vercel
- [ ] Load HDX administrative boundaries (admin 0-3) into PostGIS
- [ ] Load Census 2017 population data from CERP GitHub repo
- [ ] Load Zenodo brick kiln dataset (11K+ points)
- [ ] Load border crossing coordinates from OSM
- [ ] Build district name crosswalk table
- [ ] Build basic map page with Mapbox GL JS showing districts + kilns + borders
- [ ] Build API endpoints: boundaries, kilns, border crossings
- [ ] Deploy: FastAPI on EC2, Next.js on Vercel

**Deliverable**: Interactive map of Pakistan with 160 districts, 11K brick kiln markers, and border crossings visible.

### Phase 2 — Core Data Integration (Weeks 5-10)

**Goal**: Sahil, CTDC, TIP Report, and SSDO data ingested; dashboard functional

- [ ] Download and parse all 16 Sahil Cruel Numbers PDFs
- [ ] Build `sahil_parser.py` with per-year extraction logic
- [ ] Download CTDC synthetic dataset, filter for Pakistan
- [ ] Build TIP Report scraper (24 years of HTML pages)
- [ ] Parse SSDO reports for police-sourced data
- [ ] Scrape StateOfChildren.com HTML tables
- [ ] Build incidents normalization pipeline (all sources → unified schema)
- [ ] Load PSLM 2019-20 vulnerability indicators
- [ ] Load flood extent data (2022)
- [ ] Calculate district-level vulnerability scores
- [ ] Build Dashboard page with Recharts (trends, province comparison, case types)
- [ ] Build district profile pages
- [ ] Add heat map layer to main map
- [ ] Add time slider for temporal filtering

**Deliverable**: 15-year trend dashboard, district-level heat map, and district profiles with vulnerability scores.

### Phase 3 — Intelligence & Reporting (Weeks 11-16)

**Goal**: News pipeline, court data, public reporting, NLP

- [ ] Build Pakistan gazetteer (3000+ entries)
- [ ] Build spaCy NER pipeline for geographic entity extraction
- [ ] Build news RSS scraper (Dawn, Tribune, The News, ARY)
- [ ] Build news classification model (trafficking-relevant or not)
- [ ] Build court scrapers (start with CommonLII, then High Courts)
- [ ] Build court judgment NLP extraction pipeline
- [ ] Build public reporting form with map pin
- [ ] Build report submission API with geocoding
- [ ] Build trafficking route visualization (from TIP Report qualitative data)
- [ ] Build legal intelligence page (conviction rates by district)
- [ ] Build spatial clustering (DBSCAN on incidents)
- [ ] Add Urdu language support (map labels, navigation, reporting form)

**Deliverable**: Live news monitoring, court judgment database, public reporting portal, and Urdu support.

### Phase 4 — Scale & Impact (Weeks 17-24)

**Goal**: Complete platform, government outreach, public launch

- [ ] Build ZARRA PDF report parser
- [ ] File RTI requests to 4 provincial police departments
- [ ] Build advanced analytics (correlation analysis, pattern detection)
- [ ] Build export functionality (CSV, GeoJSON, PDF reports)
- [ ] Build admin dashboard for report moderation
- [ ] PWA optimization (offline district profiles, cached helplines)
- [ ] Performance optimization (ISR, vector tile caching, API pagination)
- [ ] Security audit (penetration testing, OWASP compliance)
- [ ] Build "About" page with full methodology documentation
- [ ] Prepare presentation for NCRC, FIA, provincial CPBs
- [ ] Media outreach (Dawn, Tribune, Geo coverage)
- [ ] Public launch

**Deliverable**: Production-ready platform with government engagement and media coverage.

---

## 14. SECURITY & ETHICS

### 14.1 Data Ethics Principles

1. **Do no harm**: No data that could identify individual victims is ever displayed publicly. All victim data is aggregated to district level minimum.
2. **No vigilantism**: The platform provides intelligence to AUTHORITIES, not vigilante tools. Public reports are moderated before being referred.
3. **Source transparency**: Every data point traces back to its source. Methodology is fully documented and publicly available.
4. **Accuracy over volume**: Better to show less data with high confidence than more data with poor quality. Every NLP extraction has a confidence score.
5. **No retraumatization**: Graphic details of abuse are NEVER displayed. Data is statistical, not narrative.
6. **Open data advocacy**: We advocate for government agencies to publish structured, machine-readable data. The platform demonstrates why this matters.

### 14.2 Technical Security

- HTTPS everywhere (Vercel handles frontend; Let's Encrypt for EC2)
- API rate limiting (10 req/sec for public endpoints; higher for authenticated government users)
- SQL injection prevention (SQLAlchemy parameterized queries)
- XSS prevention (Next.js built-in sanitization)
- CSRF protection (SameSite cookies + CSRF tokens)
- Photo upload validation (file type checking, EXIF stripping, size limits)
- Database encryption at rest (Neon handles this)
- Reporter identity encryption (AES-256 for optional contact info)
- Regular dependency audits (Dependabot / Snyk)
- Server hardening (UFW, fail2ban, SSH key-only)

### 14.3 Legal Compliance

- Pakistan Data Protection Bill 2023 (if enacted) — comply with data minimization and purpose limitation
- PECA 2016 — no unauthorized access to government systems
- RTI Act 2017 — use for legitimate data access from public bodies
- Copyright — scraped news articles stored as extracted data points, not full text reproduction

---

## 15. DEPLOYMENT & INFRASTRUCTURE

### 15.1 Deployment Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Vercel     │────▶│   EC2 (FastAPI)  │────▶│  Neon DB      │
│  (Next.js)   │     │  t3.large        │     │  (PostgreSQL  │
│  Free → Pro  │     │  Ubuntu 22.04    │     │   + PostGIS)  │
└──────────────┘     │                  │     │  Free → Pro   │
                     │  FastAPI (8000)  │     └───────────────┘
                     │  Celery Worker   │
                     │  Celery Beat     │     ┌───────────────┐
                     │  Redis           │     │  S3 Bucket    │
                     │                  │────▶│  (Raw PDFs,   │
                     └──────────────────┘     │   photos)     │
                                              └───────────────┘
```

### 15.2 Environment Variables

```bash
# .env.local (Next.js on Vercel)
NEXT_PUBLIC_MAPBOX_TOKEN=pk.xxxxx
NEXT_PUBLIC_API_URL=https://api.nigehbaan.pk
NEXTAUTH_SECRET=xxxxx
NEXTAUTH_URL=https://nigehbaan.pk

# .env (FastAPI on EC2)
DATABASE_URL=postgresql+asyncpg://user:pass@ep-xxx.neon.tech/nigehbaan
REDIS_URL=redis://localhost:6379
S3_BUCKET=nigehbaan-data
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
MAPBOX_TOKEN=pk.xxxxx
SECRET_KEY=xxxxx
CORS_ORIGINS=https://nigehbaan.pk,http://localhost:3000
```

### 15.3 Domain

Recommended: **nigehbaan.pk** (check availability on PKNIC)
Alternative: **nigehbaan.org** or **nigehbaan.org.pk**

### 15.4 Cost Estimate (MVP — Monthly)

| Service | Tier | Cost |
|---------|------|------|
| Vercel | Free (hobby) → Pro ($20) | $0-20 |
| EC2 t3.large | On-demand | ~$60 |
| Neon PostgreSQL | Free (0.5 GB) → Launch ($19) | $0-19 |
| S3 (50 GB storage) | Standard | ~$1 |
| Mapbox | Free (50K map loads) | $0 |
| Domain (.pk) | Annual | ~$10/year |
| **Total MVP** | | **~$60-100/month** |

### 15.5 Monitoring

- **Uptime**: UptimeRobot (free) for API and frontend
- **Errors**: Sentry (free tier) for both Next.js and FastAPI
- **Logs**: CloudWatch for EC2
- **Database**: Neon built-in monitoring
- **Scraper health**: Custom Celery monitoring dashboard (Flower)

---

## APPENDIX A: DISTRICT NAME CROSSWALK (SAMPLE)

```json
{
  "DI Khan": "PK0205",
  "D.I. Khan": "PK0205",
  "Dera Ismail Khan": "PK0205",
  "D I Khan": "PK0205",
  
  "Killa Abdullah": "PK0110",
  "Qilla Abdullah": "PK0110",
  "Quilla Abdullah": "PK0110",
  
  "Muzaffargarh": "PK0427",
  "Muzzafargarh": "PK0427",
  "Muzafar Garh": "PK0427",
  
  "Kashmore": "PK0312",
  "Kashmore at Kandhkot": "PK0312",
  "Kandhkot": "PK0312"
}
```

Full crosswalk must cover all 160+ districts with Urdu transliterations, common misspellings, historical names, and abbreviations.

---

## APPENDIX B: KNOWN DATA GAPS

| Gap | Impact | Mitigation |
|-----|--------|------------|
| No district-level FIR data publicly available | Cannot map incidents at high resolution from official sources | File RTI requests to 4 provincial police departments (follow SSDO methodology) |
| ZARRA data behind authentication | Best missing children dataset is inaccessible for automated ingestion | Parse published PDF reports; pursue formal data sharing with MoHR |
| No structured trafficking route data | Routes must be manually constructed from narrative sources | Extract from TIP Reports, FIA reports, research papers using NLP |
| Sahil data is province-level (district sporadic) | Heat maps limited to provincial resolution for primary dataset | Supplement with SSDO district data, news NER for district-level incident extraction, and NCSW mapping study |
| No Balochistan CPC online | Poorest province has worst data coverage | Rely on federal sources (TIP, CTDC) + news monitoring |
| Court systems don't search by offense | Cannot directly query trafficking cases | Must download broadly, then NLP-classify |
| Social media data cost-prohibitive | Twitter/Facebook data inaccessible at scale | Focus on news media monitoring instead |

---

## APPENDIX C: KEY CONTACTS FOR DATA ACCESS

| Organization | What to Request | Contact Method |
|-------------|----------------|----------------|
| NCRC | Data sharing partnership for StateOfChildren.com | https://ncrc.gov.pk/contact-us/ |
| MoHR / ZARRA | API access or data export from ZARRA system | MoHR Helpline 1099 / official letter |
| Sahil | Structured dataset behind Cruel Numbers | https://sahil.org/contact-us/ |
| SSDO | Full RTI-sourced police data tables | https://www.ssdo.org.pk/contact-us |
| Punjab Police | RTI request for district-level crime data | Punjab Information Commission |
| Sindh Police | RTI request for district-level crime data | Sindh Information Commission |
| KP Police | RTI request for district-level crime data | KP Information Commission |
| IOM/CTDC | Extended dataset access beyond public download | ctdc@iom.int |

---

*This document is the single source of truth for the Nigehbaan project. Every scraper, every pipeline, every API endpoint, every database table traces back to a data source documented here. When in doubt, refer to this file.*

*Built by Hassan Arshad and the Zensbot team. For Pakistan's children.*
