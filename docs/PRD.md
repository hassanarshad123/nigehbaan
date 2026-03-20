# Product Requirements Document (PRD)

## Nigehbaan — Pakistan Child Trafficking Intelligence Platform

**Version:** 1.0
**Date:** March 19, 2026
**Author:** Hassan Arshad / Zensbot
**Status:** Pre-Development

---

## 1. Problem Statement

Pakistan has an estimated **2.35 million people trapped in modern slavery** (Walk Free Foundation, 2023), ranking 4th globally in prevalence. The US State Department's 2025 TIP Report documents **1,607 trafficking investigations under PTPA alone**, with only **495 convictions**. Sahil's "Cruel Numbers" reports track **7,608 incidents of child abuse in 2024**, including kidnapping, sexual exploitation, and trafficking — a number representing only what newspapers report.

The data that exists today is:

- **Scattered** across 90+ sources in 3 languages (English, Urdu, Sindhi)
- **Siloed** between federal agencies, 4 provincial governments, dozens of NGOs, and international bodies
- **Locked in PDFs** — Sahil's 16 annual reports, FIA annual reports, court judgments, and ZARRA analysis exist as unstructured PDF documents
- **Not geocoded** — no single map shows where trafficking happens, where children go missing, where they are recovered, and what routes connect origin to exploitation
- **Not connected** — nobody is cross-referencing brick kiln locations with missing children reports with poverty data with school dropout rates to reveal predictive patterns

The result: law enforcement operates blind, NGOs duplicate effort, policymakers legislate without evidence, and citizens have no way to report or understand the threat in their own communities.

---

## 2. User Personas

### Persona A: Government / Law Enforcement

**Representative users:**
- FIA Anti-Human Trafficking Circle officers (Lahore, Islamabad, Karachi, Peshawar, Quetta)
- ZARRA / Ministry of Human Rights case managers
- NCRC (National Commission on Rights of the Child) policy analysts
- Provincial Child Protection Bureau officers (Punjab CPWB, Sindh CPA, KP CPWC)
- District Police Officers (DPOs) and District Administration

**Needs:**
- Route intelligence and cross-border pattern analysis
- District-level hotspot identification for resource allocation
- Evidence base for policy recommendations and budget justifications
- Missing children geo-tracking with real-time alerts
- Prosecution and conviction rate analytics

**Success scenario:** A DPO in Kasur opens Nigehbaan, sees a cluster of missing children reports near known brick kilns, and dispatches a targeted operation.

### Persona B: NGOs & International Organizations

**Representative users:**
- Sahil, SPARC, Roshni Helpline, Madadgaar Foundation researchers
- UNICEF, ILO, IOM, UNODC Pakistan program officers
- Walk Free, ECPAT, Human Rights Watch advocacy teams

**Needs:**
- Unified view of data that each organization partially holds
- Pakistan-specific analytics for global programs and reports
- Evidence for international advocacy, donor reporting, and media engagement
- Trend analysis showing whether interventions are working

**Success scenario:** An NGO in Balochistan uses district-level vulnerability scores to decide where to open their next child protection center.

### Persona C: Citizens of Pakistan

**Representative users:**
- Parents concerned about safety in their area
- Community members witnessing suspicious activity
- Journalists investigating trafficking stories
- Students and researchers studying the issue

**Needs:**
- Easy incident reporting (anonymous, mobile-friendly, works on 3G)
- "Know Your District" risk profiles showing local threat levels
- Helpline directory with emergency contacts
- Awareness of the scale and geography of the problem

**Success scenario:** A citizen in Lahore sees a child begging at a traffic signal, opens Nigehbaan on their phone, and files an anonymous report with GPS location.

---

## 3. Core Capabilities

### A. Interactive Geo-Intelligence Map

The centerpiece of the platform. A full-screen, dark-themed map of Pakistan at district resolution with toggleable data layers.

**Layers include:**
- Heat maps of child trafficking incidents by district (sourced from Sahil, SSDO, ZARRA, news media)
- Point markers for 11,000+ brick kilns (Zenodo dataset) with bonded labor indicators
- Trafficking route visualization (origin to transit to exploitation) constructed from TIP Reports and FIA data
- Border crossing vulnerability overlay (8 Afghanistan crossings, 4 Iran crossings, 1 India crossing)
- Poverty index, school dropout rates, flood-affected areas, and police jurisdiction boundaries as contextual layers

### B. Trend Analysis Dashboard

Longitudinal analytics enabling users to understand how trafficking patterns have evolved over 15+ years.

**Visualizations:**
- 15-year time series from Sahil Cruel Numbers (2010-2024)
- Province-wise comparison across Punjab, Sindh, KP, Balochistan, ICT, AJK, GB
- Case type breakdown: kidnapping, sexual abuse, trafficking, child marriage, bonded labor, begging mafia
- Prosecution vs. conviction rates over time from 24 years of TIP Report data
- Seasonal patterns and year-over-year change indicators

### C. Pattern Detection Engine

Analytical backend that connects data across sources to reveal patterns invisible in any single dataset.

**Capabilities:**
- Correlation analysis linking poverty, trafficking incidents, school dropout, and brick kiln density
- Hotspot identification using spatial clustering (DBSCAN on geocoded incidents)
- Network graph of repeat offenders, locations, and connections from court judgment NLP
- Early warning scores for vulnerable districts based on leading indicators

### D. Public Reporting Portal

Citizen-facing tool for reporting suspicious activity and accessing resources.

**Features:**
- Anonymous incident reporting with location pin, photo upload, and category selection
- Missing children alert feed aggregated from ZARRA, Roshni Helpline, and media
- Community awareness through "Know Your District" risk profiles
- Resource directory: helplines (1099, 1098, Roshni 0800-22444), legal aid, shelter homes

### E. Legal Intelligence Module

Court judgment analytics for understanding prosecution and sentencing patterns.

**Features:**
- Court judgment search filtered by trafficking-related PPC sections (366-A, 366-B, 369, 370, 371-A, 371-B)
- Conviction rate mapping by district and court
- Sentencing pattern analysis showing variation across jurisdictions
- Legislative gap identification comparing enacted laws against enforcement reality

---

## 4. Functional Requirements

### 4.1 Map Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| MAP-01 | Display Pakistan administrative boundaries at levels 0-3 (country, province, district, tehsil) with OCHA P-codes | P0 |
| MAP-02 | Render 11,000+ brick kiln point markers with size proportional to population within 1km | P0 |
| MAP-03 | Display border crossing points with vulnerability scoring | P0 |
| MAP-04 | Show incident heat map with intensity based on case count per district | P1 |
| MAP-05 | Render trafficking route lines connecting origin, transit, and destination points | P1 |
| MAP-06 | Provide time slider for temporal filtering across all layers (2010-2024) | P1 |
| MAP-07 | Enable layer toggle panel for independent control of each data layer | P0 |
| MAP-08 | Support click-on-district popup showing incident count, trend arrow, top incident types, and vulnerability score | P1 |
| MAP-09 | Implement district/city search with autocomplete | P1 |
| MAP-10 | Export visible map data as CSV or GeoJSON | P2 |

### 4.2 Dashboard Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| DASH-01 | Display 15-year Sahil trend data as interactive line charts with hover tooltips | P1 |
| DASH-02 | Show province-wise comparison as grouped bar charts | P1 |
| DASH-03 | Show case type breakdown as donut/pie charts | P1 |
| DASH-04 | Show prosecution vs. conviction rate trend from TIP Report data | P1 |
| DASH-05 | Provide filters for province, year range, and incident type | P1 |
| DASH-06 | Display top-level summary counters with animated digits | P1 |
| DASH-07 | Support print-friendly layout for embedding in reports | P2 |

### 4.3 Reporting Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| RPT-01 | Accept anonymous reports with no personal information required | P1 |
| RPT-02 | Support location selection via map pin drop or address text input | P1 |
| RPT-03 | Categorize reports: suspicious activity, missing child, bonded labor, begging ring, child marriage, other | P1 |
| RPT-04 | Accept photo uploads with automatic EXIF stripping | P2 |
| RPT-05 | Assign reference number for status tracking | P1 |
| RPT-06 | Auto-geocode submitted address to district P-code | P1 |
| RPT-07 | Rate limit submissions to 5 per IP per day | P1 |
| RPT-08 | Display confirmation page with helpline numbers | P1 |

### 4.4 Legal Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| LGL-01 | Search court judgments by PPC section, court, year range, and outcome | P2 |
| LGL-02 | Display conviction rate choropleth map by district | P2 |
| LGL-03 | Show sentencing pattern statistics (average sentence, range) | P2 |
| LGL-04 | Link to relevant statute text on legislation.pk | P2 |
| LGL-05 | Display judge-level sentencing analysis (anonymized) | P3 |

### 4.5 Search Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| SRCH-01 | Full-text search across incidents, court judgments, news articles, and locations | P2 |
| SRCH-02 | Return results grouped by data source with relevance scoring | P2 |
| SRCH-03 | Support both English and Urdu search terms | P3 |

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target |
|--------|--------|
| Map initial load (with district boundaries + kiln markers) | < 3 seconds on 4G connection |
| API response time (p95) | < 500ms |
| Dashboard chart rendering | < 2 seconds |
| Map layer toggle | < 500ms |
| Search results | < 1 second |
| Concurrent users supported | 500+ |

### 5.2 Accessibility

- WCAG 2.1 AA compliance across all pages
- High contrast text on dark backgrounds (minimum 4.5:1 ratio)
- Screen reader support with aria-labels for all charts and map interactions
- Keyboard navigation for all interactive elements
- Text scaling up to 200% without layout breakage

### 5.3 Internationalization (i18n)

- **English** — primary language for data, interface, and documentation
- **Urdu** — map labels, navigation, reporting form, district names, helpline information (RTL layout support)
- **Sindhi** — future phase for Sindh-specific content
- Date formatting: DD/MM/YYYY (Pakistan standard)
- Number formatting: English numerals with Urdu labels where appropriate

### 5.4 Security

- HTTPS everywhere (Vercel for frontend, Let's Encrypt for backend)
- API rate limiting: 10 req/sec for public endpoints, higher for authenticated government users
- SQL injection prevention via SQLAlchemy parameterized queries
- XSS prevention via Next.js built-in sanitization
- CSRF protection with SameSite cookies and CSRF tokens
- Photo upload validation: file type checking, EXIF stripping, size limits (max 5MB)
- Database encryption at rest (Neon managed)
- Reporter identity encryption (AES-256 for optional contact info)
- IP address hashing for abuse prevention (not identification)
- Regular dependency audits via Dependabot/Snyk
- CORS configured to allow only trusted origins

---

## 6. Success Metrics

| Metric | Year 1 Target |
|--------|---------------|
| Districts with mapped incident data | 100+ of 160 |
| Total incidents geocoded and mapped | 50,000+ |
| Unique data sources integrated | 30+ |
| Citizen reports submitted | 1,000+ |
| Government agency partnerships | 2+ (NCRC, FIA, or provincial CPB) |
| Media stories citing Nigehbaan data | 10+ |
| Monthly active users | 5,000+ |
| Average map load time | < 3 seconds |
| API uptime | 99.5%+ |

---

## 7. MVP Scope (Phase 1)

The minimum viable product delivers the foundation:

1. Interactive map of Pakistan with 160 district boundaries, 11K+ brick kiln markers, and border crossings
2. Basic API serving boundary GeoJSON, kiln points, and border crossing data
3. District click popup with population data
4. Dark-themed map with Mapbox dark-v11 base style
5. Deployed: Next.js on Vercel, FastAPI on EC2, PostgreSQL+PostGIS on Neon

Phase 1 does NOT include: dashboard charts, reporting portal, court data, news pipeline, NLP, or Urdu support. These are delivered in Phases 2-4 per the [ROADMAP](ROADMAP.md).

---

## 8. Constraints and Assumptions

### Constraints

- Budget is limited to approximately $60-100/month for infrastructure
- No access to authenticated government databases (ZARRA, e-FIR) without formal agreements
- Court systems do not support search by criminal offense type
- Sahil data is province-level (district-level is sporadic)
- Balochistan has the poorest data coverage of any province

### Assumptions

- Mapbox free tier (50K map loads/month) is sufficient for the first year
- Neon free tier (0.5 GB) is sufficient during development; will upgrade to Launch tier ($19/mo) for production
- Data sources listed in the Data Dictionary will remain publicly accessible
- OCHA P-codes are stable and will not change during the project lifecycle
- Users will primarily access the platform on mobile devices (Android, 3G/4G)

---

## 9. Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Government takedown request | High | Low | Host outside Pakistan jurisdiction; open methodology reduces suspicion |
| Data source URLs change or break | Medium | High | Store raw data in S3; monitor scraper health; build URL fallback logic |
| PDF format changes break parsers | Medium | Medium | Version parser logic per report year; manual verification of extraction accuracy |
| Low citizen adoption | Medium | Medium | Partner with existing NGO helplines; integrate with existing reporting channels |
| Accuracy challenges in NLP geocoding | Medium | High | Confidence scoring on all extractions; manual review queue for low-confidence results |
| Sensitive data exposure | High | Low | No individual victim data displayed; aggregation to district level minimum; security audit before launch |

---

*This PRD is the product-level specification for Nigehbaan. For technical architecture, see [ARCHITECTURE.md](ARCHITECTURE.md). For data sources, see [DATA_DICTIONARY.md](DATA_DICTIONARY.md). For development timeline, see [ROADMAP.md](ROADMAP.md).*
