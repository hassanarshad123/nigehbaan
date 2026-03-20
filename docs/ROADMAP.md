# Development Roadmap

## Nigehbaan — Phased Development Plan

**Total Duration:** 24 weeks (6 months)
**Team:** Hassan Arshad / Zensbot + Claude
**Start Date:** TBD

---

## Phase 1 — Foundation (Weeks 1-4)

**Goal:** Base map with structured data loaded, basic API endpoints, and deployment infrastructure.

### Tasks

- [ ] **Infrastructure Setup**
  - [ ] Provision Neon PostgreSQL database with PostGIS extension enabled
  - [ ] Set up FastAPI project skeleton on EC2 (t3.large, Ubuntu 22.04)
  - [ ] Set up Next.js 14+ project with App Router, Tailwind CSS, shadcn/ui
  - [ ] Configure Docker Compose for local development (PostgreSQL + Redis + API + Frontend)
  - [ ] Set up CI/CD pipeline (GitHub Actions for lint, test, deploy)
  - [ ] Configure environment variables for all services

- [ ] **Geographic Foundation Data**
  - [ ] Download HDX administrative boundaries (admin levels 0-3) as GeoJSON
  - [ ] Load boundaries into PostGIS as `boundaries` table with spatial indexes
  - [ ] Download Census 2017 population data from CERP GitHub repo
  - [ ] Join census data to boundaries using district name crosswalk
  - [ ] Download Zenodo brick kiln dataset (11K+ geolocated kilns)
  - [ ] Load brick kilns into PostGIS as `brick_kilns` point table
  - [ ] Spatial join kilns to districts (assign P-codes)
  - [ ] Extract border crossing coordinates from OpenStreetMap data
  - [ ] Load border crossings into `border_crossings` table
  - [ ] Build `district_name_variants` crosswalk table covering all 160+ districts with common misspellings, abbreviations, and Urdu transliterations

- [ ] **Backend API (v1)**
  - [ ] Implement SQLAlchemy ORM models for boundaries, brick_kilns, border_crossings
  - [ ] Build `GET /api/v1/map/boundaries?level={0-3}` — return district polygons as GeoJSON
  - [ ] Build `GET /api/v1/map/kilns?district={pcode}` — return brick kiln points as GeoJSON
  - [ ] Build `GET /api/v1/map/borders` — return border crossing points
  - [ ] Build `GET /api/v1/districts` — return all districts with basic stats
  - [ ] Build `GET /api/v1/districts/{pcode}` — return single district profile
  - [ ] Configure CORS, rate limiting, and error handling middleware
  - [ ] Set up Alembic for database migrations

- [ ] **Frontend Map**
  - [ ] Implement Mapbox GL JS map component with dark-v11 base style
  - [ ] Render district boundary polygons on map
  - [ ] Render brick kiln point markers (orange dots, size proportional to population_1km)
  - [ ] Render border crossing markers (red triangles)
  - [ ] Implement layer toggle panel (show/hide boundaries, kilns, borders)
  - [ ] Implement click-on-district popup showing name, P-code, population, kiln count
  - [ ] Basic responsive layout (desktop sidebar + mobile bottom sheet)

- [ ] **Deployment**
  - [ ] Deploy Next.js frontend to Vercel
  - [ ] Deploy FastAPI backend to EC2 with uvicorn + systemd
  - [ ] Configure Nginx reverse proxy with SSL (Let's Encrypt)
  - [ ] Verify end-to-end data flow: Vercel -> EC2 API -> Neon DB

### Deliverable

Interactive map of Pakistan displaying 160 districts with administrative boundaries, 11,000+ brick kiln markers, and 13 border crossing points. Click any district to see population data and local kiln count. Deployed and publicly accessible.

### Acceptance Criteria

- Map loads in under 3 seconds on 4G connection
- All 160 districts render correctly with accurate boundaries
- Brick kiln markers are visible and clickable
- API responds in under 500ms for all endpoints
- Frontend and backend are deployed and accessible via HTTPS

---

## Phase 2 — Core Data Integration (Weeks 5-10)

**Goal:** Ingest primary incident datasets (Sahil, CTDC, TIP Report, SSDO), build the trend analysis dashboard, and calculate district-level vulnerability scores.

### Tasks

- [ ] **Sahil PDF Extraction Pipeline**
  - [ ] Download all 16 Sahil "Cruel Numbers" PDFs (2010-2024)
  - [ ] Build `sahil_parser.py` with per-year extraction logic using pdfplumber
  - [ ] Extract every table from every report into structured JSON
  - [ ] Handle format variations across 15 years (tables vs. charts, layout changes)
  - [ ] Normalize extracted data into unified schema: `{year, province, district, crime_category, victim_gender, victim_age_bracket, urban_rural, case_count, fir_registered_count}`
  - [ ] Load into `incidents` table with `source_type='sahil'`
  - [ ] Validate extraction accuracy against known totals from reports

- [ ] **CTDC Dataset Integration**
  - [ ] Download CTDC Global Synthetic Dataset CSV from IOM
  - [ ] Filter for `country_of_exploitation='Pakistan'` OR `victim_citizenship='Pakistan'`
  - [ ] Map CTDC fields to unified incident schema
  - [ ] Load into `incidents` table with `source_type='ctdc'`

- [ ] **TIP Report Scraper**
  - [ ] Build scraper for all 24+ Pakistan country pages (2001-2025)
  - [ ] Parse HTML to extract: tier ranking, investigation counts, prosecution counts, conviction counts, victims identified, budget allocated
  - [ ] Extract qualitative named locations and routes into `tip_report_locations` for geocoding
  - [ ] Load into `tip_report_annual` time series table
  - [ ] Store annual data as structured records for dashboard consumption

- [ ] **SSDO Report Parsing**
  - [ ] Download available SSDO PDF reports
  - [ ] Parse for police-sourced incident data with conviction rates
  - [ ] Extract provincial breakdown: Punjab, KP, Sindh, ICT, Balochistan
  - [ ] Load into `incidents` table with `source_type='ssdo'`

- [ ] **StateOfChildren.com Scraping**
  - [ ] Scrape all HTML tables from `/children-dataset/` and related pages
  - [ ] Extract Sahil summary tables, ZARRA data, education/health/justice datasets
  - [ ] Normalize and cross-reference with existing data

- [ ] **Vulnerability Indicators**
  - [ ] Download PSLM 2019-20 microdata from PBS
  - [ ] Calculate district-level indicators: out-of-school rate, food insecurity rate, migration rate
  - [ ] Download Walk Free GSI vulnerability indicators for Pakistan
  - [ ] Download UNICEF child marriage data by province
  - [ ] Load flood extent data (2022 UNOSAT) and calculate district-level flood-affected percentage
  - [ ] Calculate kiln density per district from spatial join
  - [ ] Implement composite risk scoring algorithm (10 weighted indicators, 0-100 scale)
  - [ ] Store in `vulnerability_indicators` table

- [ ] **Dashboard Frontend**
  - [ ] Build Dashboard page (`/dashboard`) with Recharts
  - [ ] 15-year Sahil trend line chart with hover tooltips
  - [ ] Province-wise comparison grouped bar chart
  - [ ] Case type breakdown donut chart
  - [ ] Prosecution vs. conviction rate trend line (TIP Report data)
  - [ ] Top-level summary counters with animated digits
  - [ ] Filters: province selector, year range slider, incident type dropdown
  - [ ] Print-friendly layout mode

- [ ] **District Profiles**
  - [ ] Build District Profile page (`/district/[pcode]`)
  - [ ] Risk score gauge visualization
  - [ ] District-specific incident trend chart
  - [ ] Brick kiln count and density stat
  - [ ] Nearest border crossing distance
  - [ ] Comparison to national and provincial averages

- [ ] **Map Enhancements**
  - [ ] Add incident heat map layer (color intensity = case count per district)
  - [ ] Add time slider component for temporal filtering (2010-2024)
  - [ ] Add choropleth layer for vulnerability score
  - [ ] Enhance district popup with incident count, trend arrow, and "View Full Profile" link

### Deliverable

15-year trend analysis dashboard with interactive charts. District-level heat map showing incident density. District profiles with vulnerability scores combining 10 indicators. All primary data sources (Sahil, CTDC, TIP Report, SSDO) ingested and normalized.

### Acceptance Criteria

- Dashboard displays accurate 15-year trend data matching Sahil report totals
- Heat map correctly reflects relative incident density across districts
- Vulnerability scores are calculated for 100+ districts
- All dashboard charts are interactive with filters
- Province comparison accurately reflects source data

---

## Phase 3 — Intelligence & Reporting (Weeks 11-16)

**Goal:** Build the NLP pipeline for news monitoring, court judgment extraction, public reporting portal, and Urdu language support.

### Tasks

- [ ] **Pakistan Gazetteer**
  - [ ] Build `pakistan_gazetteer.json` with 3,000+ location entries
  - [ ] Each entry: `{name, variants: [], lat, lon, admin_level, district_pcode}`
  - [ ] Cover all 160+ districts with alternative spellings (English + Urdu transliterations)
  - [ ] Include 500+ cities/towns, trafficking-relevant locations (brick kiln areas, border towns, bus stations, truck stops, shrines)
  - [ ] Build regex patterns for Pakistani location references

- [ ] **NLP Pipeline**
  - [ ] Set up spaCy with `en_core_web_trf` base model
  - [ ] Define custom entity types: PAKISTAN_DISTRICT, PAKISTAN_CITY, PAKISTAN_PROVINCE, TRAFFICKING_TYPE, PPC_SECTION, VICTIM_AGE, VICTIM_GENDER
  - [ ] Train custom NER model on 500+ annotated Pakistani news articles
  - [ ] Integrate gazetteer for rule-based geographic entity matching
  - [ ] Build geocoding service that maps extracted locations to lat/lon coordinates
  - [ ] Implement confidence scoring for all NLP extractions

- [ ] **News Monitoring Pipeline**
  - [ ] Build RSS scraper for Dawn, Express Tribune, The News, ARY News
  - [ ] Build Playwright scraper for JS-heavy sites (Geo News, Samaa TV)
  - [ ] Build binary classifier for trafficking-relevance (distilbert fine-tuned on labeled articles)
  - [ ] Implement entity extraction pipeline: classify -> extract -> geocode -> store
  - [ ] Set up Celery Beat schedule: RSS every 6 hours, JS sites daily
  - [ ] Store in `news_articles` table with extracted incidents linked to `incidents` table

- [ ] **Court Judgment Scrapers**
  - [ ] Build CommonLII bulk scraper for Supreme Court decisions (2002-2011)
  - [ ] Build Lahore High Court scraper (requests + BeautifulSoup)
  - [ ] Build Sindh High Court scraper (5 benches)
  - [ ] Build Peshawar High Court scraper (4 benches)
  - [ ] Build Balochistan High Court scraper (Playwright for SPA)
  - [ ] Build Islamabad High Court scraper (ASP.NET ViewState handling)
  - [ ] Implement court judgment NLP extraction: date, court, judge, charges, district, sentence, victim demographics
  - [ ] Load into `court_judgments` table with geographic identifiers
  - [ ] Set up weekly scraping schedule via Celery Beat

- [ ] **Public Reporting Portal**
  - [ ] Build multi-step report submission form (`/report`)
  - [ ] Step 1: Category selector (suspicious activity, missing child, bonded labor, begging ring, child marriage, other)
  - [ ] Step 2: Location via map pin drop or address text input
  - [ ] Step 3: Date picker
  - [ ] Step 4: Details textarea + photo upload (max 5MB, EXIF stripped)
  - [ ] Step 5: Optional reporter contact info (encrypted at rest)
  - [ ] Build `POST /api/v1/reports` endpoint with validation and geocoding
  - [ ] Build `GET /api/v1/reports/{id}` for status checking
  - [ ] Build confirmation page with reference number and helpline numbers
  - [ ] Implement rate limiting (5 reports per IP per day)
  - [ ] Implement spam detection (basic content filtering)

- [ ] **Trafficking Route Visualization**
  - [ ] Extract route information from TIP Report qualitative sections
  - [ ] Manually construct initial route geometries from FIA and research data
  - [ ] Build route layer on map (red dashed lines, thickness proportional to evidence confidence)
  - [ ] Build `GET /api/v1/map/routes` endpoint

- [ ] **Legal Intelligence Page**
  - [ ] Build Legal page (`/legal`) with court judgment search
  - [ ] Filters: court, year range, PPC section, outcome
  - [ ] Conviction rate choropleth map by district
  - [ ] Build `GET /api/v1/legal/search` and `GET /api/v1/legal/conviction-rates` endpoints

- [ ] **Spatial Clustering**
  - [ ] Implement DBSCAN clustering on geocoded incidents
  - [ ] Generate cluster polygons with incident counts and dominant types
  - [ ] Visualize clusters as colored boundary overlays on the map

- [ ] **Urdu Language Support**
  - [ ] Set up next-intl with English and Urdu locales
  - [ ] Translate navigation, reporting form, and district names to Urdu
  - [ ] Implement RTL layout support for Urdu pages
  - [ ] Add Noto Nastaliq Urdu font for Urdu text rendering

### Deliverable

Live news monitoring pipeline processing articles from 7+ sources. Court judgment database with NLP-extracted structured data. Public reporting portal accepting anonymous citizen reports. Trafficking route visualization on the map. Urdu language support for key user flows.

### Acceptance Criteria

- News pipeline classifies and geocodes articles with >80% accuracy
- Court scrapers successfully extract judgments from 6+ court systems
- Reporting form works on low-end Android devices over 3G
- Routes display correctly on the map
- Urdu navigation and reporting form are functional with proper RTL layout

---

## Phase 4 — Scale & Impact (Weeks 17-24)

**Goal:** Complete the platform with advanced analytics, admin tools, PWA optimization, security hardening, and public launch with government engagement.

### Tasks

- [ ] **Additional Data Sources**
  - [ ] Build ZARRA PDF report parser for MoHR publications
  - [ ] File RTI requests to 4 provincial police departments (follow SSDO methodology)
  - [ ] Parse NCSW/UNICEF Violence Against Children mapping study for district-level data
  - [ ] Download and process DHS 2017-18 Pakistan data (registration required)
  - [ ] Parse NCRC Annual Report for trafficking/child protection data
  - [ ] Integrate World Bank API indicators (poverty, school enrollment, literacy)

- [ ] **Advanced Analytics**
  - [ ] Build correlation analysis: poverty x trafficking x school dropout x kiln density
  - [ ] Build early warning system: flag districts with rising leading indicators
  - [ ] Build network graph visualization of repeat locations and connections
  - [ ] Seasonal pattern analysis with year-over-year change detection

- [ ] **Export & Reporting**
  - [ ] Build CSV export for any filtered dataset
  - [ ] Build GeoJSON export for map layers
  - [ ] Build PDF report generation for district profiles
  - [ ] Build `GET /api/v1/export/csv` and `GET /api/v1/export/geojson` endpoints

- [ ] **Admin Dashboard**
  - [ ] Build admin panel for report moderation (approve, reject, refer)
  - [ ] Build scraper health monitoring dashboard (Celery Flower integration)
  - [ ] Build data quality dashboard showing extraction confidence scores
  - [ ] Implement NextAuth.js for admin authentication

- [ ] **PWA & Mobile Optimization**
  - [ ] Configure next-pwa for offline capability
  - [ ] Cache district profiles and helpline numbers for offline access
  - [ ] Optimize for low-end Android devices (Rs. 15,000 phones)
  - [ ] Add app install prompt for mobile users
  - [ ] Test on 3G connections with throttling

- [ ] **Performance Optimization**
  - [ ] Implement Incremental Static Regeneration (ISR) for district profiles
  - [ ] Set up vector tile caching for map boundaries
  - [ ] Implement API pagination for large result sets
  - [ ] Optimize database queries with materialized views for dashboard aggregations
  - [ ] Load test API for 500+ concurrent users

- [ ] **Security Hardening**
  - [ ] Conduct penetration testing
  - [ ] OWASP Top 10 compliance audit
  - [ ] Set up Dependabot for dependency vulnerability scanning
  - [ ] Configure server hardening: UFW, fail2ban, SSH key-only access
  - [ ] Verify reporter identity encryption (AES-256)
  - [ ] Verify all photo uploads stripped of EXIF metadata

- [ ] **Content & Documentation**
  - [ ] Build "About" page with full methodology documentation
  - [ ] Build "Resources" page with helplines, legal aid, shelter homes
  - [ ] Write API documentation for potential data partners
  - [ ] Prepare data sharing agreement template for government agencies

- [ ] **Launch Preparation**
  - [ ] Register domain (nigehbaan.pk or nigehbaan.org)
  - [ ] Prepare presentation deck for NCRC, FIA, and provincial CPBs
  - [ ] Brief journalists at Dawn, Express Tribune, Geo News
  - [ ] Prepare social media launch campaign
  - [ ] Set up UptimeRobot monitoring for all services
  - [ ] Set up Sentry error tracking for frontend and backend
  - [ ] Final QA testing across devices and browsers

- [ ] **Public Launch**
  - [ ] Deploy production configuration
  - [ ] Announce on social media and through NGO networks
  - [ ] Present to government stakeholders
  - [ ] Monitor for first 48 hours post-launch

### Deliverable

Production-ready platform with advanced analytics, admin moderation tools, PWA support, full security audit, and active government engagement. Public launch with media coverage.

### Acceptance Criteria

- Platform handles 500+ concurrent users without degradation
- All security audit findings resolved before launch
- PWA works offline for cached content
- At least 2 government agency meetings completed
- At least 1 media outlet briefed and interested in covering the launch
- Export functionality works for CSV, GeoJSON, and PDF
- Admin panel enables efficient report moderation

---

## Cost Summary

| Phase | Duration | Estimated Monthly Cost |
|-------|----------|----------------------|
| Phase 1 | Weeks 1-4 | $60-80 (EC2 + Neon free + Vercel free) |
| Phase 2 | Weeks 5-10 | $60-80 (same infrastructure) |
| Phase 3 | Weeks 11-16 | $80-100 (increased storage for PDFs, Redis) |
| Phase 4 | Weeks 17-24 | $80-100 (production optimization) |
| **Post-Launch** | Ongoing | **$60-100/month** |

---

*This roadmap is derived from the [MASTER.md](../MASTER.md) blueprint. For technical details, see [ARCHITECTURE.md](ARCHITECTURE.md). For data sources referenced in each phase, see [DATA_DICTIONARY.md](DATA_DICTIONARY.md).*
