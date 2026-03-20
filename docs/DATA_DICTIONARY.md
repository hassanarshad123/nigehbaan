# Data Dictionary

## Nigehbaan — Complete Data Source Registry & Database Schema

**Version:** 1.0
**Date:** March 19, 2026
**Total Sources:** 90+
**Priority Tiers:** P0 (immediate, structured) | P1 (high, scrapable) | P2 (medium, PDF/complex) | P3 (long-term, institutional access)

---

## Part 1: Data Sources by Priority Tier

---

### P0 — IMMEDIATE (Structured, Downloadable, No Scraping Needed)

#### 1.1 HDX Administrative Boundaries (OCHA COD-AB)

| Field | Value |
|-------|-------|
| URL | https://data.humdata.org/dataset/cod-ab-pak |
| Format | Shapefile, GeoJSON, Geoservice API |
| Content | Pakistan admin boundaries levels 0-3 (country, province, district, tehsil). 160 districts, 577 tehsils. |
| Key Fields | `ADM0_EN`, `ADM0_PCODE`, `ADM1_EN`, `ADM1_PCODE`, `ADM2_EN`, `ADM2_PCODE`, `ADM3_EN`, `ADM3_PCODE`, `geometry` |
| Geographic Granularity | Tehsil (admin level 3) |
| Update Frequency | Irregular (boundary changes rare) |
| License | Open (humanitarian use) |
| Scraping | None — direct download |
| Notes | P-codes are the UNIVERSAL JOIN KEY for all geographic data. Every other dataset maps to these codes. |

#### 1.2 Pakistan Census 2017 (Digitized CSV)

| Field | Value |
|-------|-------|
| URL | https://github.com/cerp-analytics/pbs2017 |
| Format | CSV + Shapefiles |
| Content | Complete 2017 Census: population by district, sex, age group, urban/rural, literacy, employment. 207.68M total population. |
| Key Fields | `district_name`, `province`, `population_total`, `population_male`, `population_female`, `population_urban`, `population_rural`, `literacy_rate` |
| Geographic Granularity | District |
| Update Frequency | Decennial (next census pending) |
| License | Open |
| Scraping | None — git clone |

#### 1.3 HDX Population Statistics (COD-PS)

| Field | Value |
|-------|-------|
| URL | https://data.humdata.org/dataset/cod-ps-pak |
| Format | CSV/XLSX |
| Content | Population estimates at admin levels 0-3 with P-codes pre-assigned |
| Geographic Granularity | Tehsil |
| Update Frequency | Annual estimates |
| Scraping | None — direct download |
| Notes | Provides pre-matched P-code population denominators for per-capita calculations |

#### 1.4 OpenStreetMap Road Network

| Field | Value |
|-------|-------|
| URL | https://download.geofabrik.de/asia/pakistan.html |
| Format | .osm.pbf (142 MB) or pre-separated Shapefiles (330 MB) |
| Content | Complete road network: GT Road (N-5), motorways (M-1 through M-9), highways, border crossings |
| Key Tags | `highway=*`, `border_type=*`, `name=*`, `barrier=border_control` |
| Update Frequency | Daily |
| Scraping | None — direct download |

#### 1.5 Zenodo Brick Kiln Dataset

| Field | Value |
|-------|-------|
| URL | https://zenodo.org/records/14038648 |
| Format | CSV, GeoJSON, Shapefile (~11.8 MB) |
| Content | ~11,000 geolocated brick kilns across Pakistan's Indo-Gangetic Plain |
| Key Fields | `latitude`, `longitude`, `kiln_type` (FCBK/ZigZag), `nearest_school_dist_m`, `nearest_hospital_dist_m`, `population_1km` |
| Geographic Granularity | Point (lat/lon) |
| Update Frequency | One-time (academic publication) |
| License | Open (Nature Scientific Data) |
| Scraping | None — direct download |
| Notes | ILO reports 83% of surveyed kilns employed children. 4.5M estimated bonded laborers. |

#### 1.6 GADM Boundaries (Backup)

| Field | Value |
|-------|-------|
| URL | https://gadm.org/download_country.html (select Pakistan) |
| Format | GeoPackage, Shapefile, KMZ |
| Content | Admin boundaries up to 5 levels |
| License | Non-commercial free |
| Notes | Backup/validation for HDX boundaries. Useful for tehsil-level gaps. |

#### 1.7 UNOSAT Flood Extent Data (2022)

| Field | Value |
|-------|-------|
| URL | https://data.humdata.org/dataset/satellite-detected-water-extents-between-01-and-29-august-2022-over-pakistan |
| Format | Shapefiles |
| Content | Pixel-level (30m resolution) flood polygons from 2022 floods |
| Geographic Granularity | 30m grid |
| Notes | Flood-affected districts correlate strongly with trafficking vulnerability (displacement, family separation) |

#### 1.8 CTDC Global Synthetic Dataset

| Field | Value |
|-------|-------|
| URL | https://www.ctdatacollaborative.org/page/global-synthetic-dataset |
| GitHub | https://github.com/UNMigration/HTCDS |
| Format | CSV |
| Content | 222,000+ trafficking victim case records across 197 countries (2002-2023). K-anonymized (~48,800 observations) + synthetic dataset. |
| Key Fields | `victim_gender`, `victim_age`, `victim_citizenship`, `country_of_exploitation`, `exploitation_type`, `means_of_control`, `recruitment_method`, `trafficking_duration`, `route_origin`, `route_transit`, `route_destination` |
| License | Open (IOM/Polaris Project) |
| Scraping | None — CSV download |

#### 1.9 Walk Free / Global Slavery Index

| Field | Value |
|-------|-------|
| URL | https://www.walkfree.org/global-slavery-index/downloads/ |
| Snapshot | https://cdn.walkfree.org/content/uploads/2023/09/27164917/GSI-Snapshot-Pakistan.pdf |
| Format | CSV/Excel |
| Content | Pakistan: 2,349,000 people in modern slavery (2023), 4th globally. 23 vulnerability indicators, 141 government response factors. |
| Update Frequency | Irregular (major publications every few years) |

#### 1.10 UNICEF Child Marriage Data Portal

| Field | Value |
|-------|-------|
| URL | https://childmarriagedata.org/country-profiles/pakistan/ |
| Format | Interactive dashboard (likely has API/data download) |
| Content | 18% married before 18 nationally; Balochistan 49.1% vs Punjab 29.8%. Disaggregated by wealth, rural/urban, education, province. |
| Geographic Granularity | Province |

#### 1.11 World Bank Data

| Field | Value |
|-------|-------|
| API | https://api.worldbank.org/v2/country/PAK/indicator/ |
| Format | REST API (JSON) |
| Content | GDP per capita, poverty headcount ratio, school enrollment, literacy rate — all as time series |
| Geographic Granularity | National (some sub-national via Relative Wealth Index) |
| Update Frequency | Annual |
| Notes | Relative Wealth Index (Meta Data for Good) provides 2.4km grid resolution poverty mapping |

---

### P1 — HIGH (Scrapable HTML or Consistent PDFs, High Value)

#### 2.1 Sahil "Cruel Numbers" Annual Reports

| Field | Value |
|-------|-------|
| URL | https://sahil.org/cruel-numbers/ |
| Format | PDF (16 reports covering 2010-2024) |
| Content | Annual child abuse statistics from newspaper monitoring (80-91 newspapers) |
| Key Fields | `year`, `province`, `crime_category` (rape, sodomy, kidnapping, trafficking, child marriage, missing), `victim_gender`, `victim_age_bracket` (0-5, 6-10, 11-15, 16-18), `urban_rural`, `case_count`, `fir_registered_count`, `perpetrator_type` |
| Geographic Granularity | Province (district sporadic) |
| Volume Trajectory | 2,388 (2010) -> 7,608 (2024) |
| Extraction Tool | pdfplumber + tabula-py |
| Update Frequency | Annual (March-April release) |

**Direct download URLs for all 16 PDFs:**

| Year | URL |
|------|-----|
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
| 5-Year Analysis | https://sahil.org/wp-content/uploads/2014/09/FIVE-YEAR-ANALYSIS-200-2011.pdf |

#### 2.2 SSDO (Sustainable Social Development Organization) Reports

| Field | Value |
|-------|-------|
| URL | https://www.ssdo.org.pk/ |
| Format | PDF reports + press conference data |
| Content | Uses RTI-obtained official police data. 2024: 7,608 total cases. Provincial breakdown. Conviction rates. |
| Key Data | Sexual abuse (2,954), Kidnapping (2,437), Child labour (895), Physical abuse (683), Child trafficking (586), Child marriage (53) |
| Unique Value | Conviction rate data by category and province (mostly under 1%) |
| Geographic Granularity | Province + district hotspots (Punjab H1 2025: Lahore, Gujranwala, Faisalabad, Rawalpindi, Sialkot) |

#### 2.3 StateOfChildren.com (NCRC Portal)

| Field | Value |
|-------|-------|
| URL | https://stateofchildren.com/children-dataset/ |
| Format | Standard HTML tables |
| Content | NCRC-operated aggregation portal with Sahil summary tables, ZARRA data, education/health/justice datasets |
| Scraping | Easiest government source — clean HTML, no auth, BeautifulSoup |
| Feasibility | Excellent |

#### 2.4 US State Department TIP Report — Pakistan

| Field | Value |
|-------|-------|
| URL Pattern | `https://www.state.gov/reports/{YEAR}-trafficking-in-persons-report/pakistan/` (2001-2025) |
| Format | Clean HTML (post-2017) + full PDF reports (all years) |
| Content | 24+ years of annual anti-trafficking enforcement data |
| Key Fields | `tier_ranking`, `investigations_count`, `prosecutions_count`, `convictions_count`, `victims_identified`, `budget_allocated`, `named_hotspots` |
| 2025 Data | 1,607 PTPA investigations (523 sex, 915 labor, 169 unspecified); 495 convictions; 4.5M estimated bonded laborers; 19,954 victims identified |
| Scraping Feasibility | Excellent — no auth, predictable URLs, consistent HTML |

#### 2.5 US DOL Child Labor Report — Pakistan

| Field | Value |
|-------|-------|
| URL | https://www.dol.gov/agencies/ilab/resources/reports/child-labor/pakistan |
| PDF Pattern | `https://www.dol.gov/sites/dolgov/files/ILAB/child_labor_reports/tda{YEAR}/Pakistan.pdf` |
| Content | Working children ages 10-14: 9.8% (2,261,704). Agriculture 69.4%, Services 19.7%, Industry 10.9%. |
| Update Frequency | Annual |

#### 2.6 UNODC Data Portal

| Field | Value |
|-------|-------|
| URL | https://dataunodc.un.org/dp-trafficking-persons |
| Format | Interactive query tool with CSV/Excel download |
| Content | Detected victims by country, age, sex, exploitation type, citizenship |
| Pakistan Data | 800+ sex trafficking cases, 11,803 victims referred by provincial police |
| GLO.ACT Reports | https://www.unodc.org/documents/human-trafficking/GLO-ACTII/ |

#### 2.7 UNHCR Pakistan Data

| Field | Value |
|-------|-------|
| URL | https://reporting.unhcr.org/pakistan |
| API | https://www.unhcr.org/refugee-statistics/ |
| Border Monitoring | https://microdata.unhcr.org/index.php/catalog/1105 |
| Content | 1.4M+ registered Afghans, 500K+ undocumented. RAHA program: 4,260 projects in 47 districts. |
| Geographic Granularity | District (RAHA project locations georeferenced) |

#### 2.8 IOM Migration Data Portal

| Field | Value |
|-------|-------|
| URL | https://www.migrationdataportal.org/themes/human-trafficking |
| Snapshot PDF | https://dtm.iom.int/sites/g/files/tmzbdl1461/files/reports/Pakistan%20Migration%20Snapshot%20Final.pdf |
| Content | Trafficking-relevant migration flow data |

#### 2.9 PBS PSLM Microdata

| Field | Value |
|-------|-------|
| URL | https://www.pbs.gov.pk/pslm-3/ and https://pslm-sdgs.data.gov.pk/ |
| Format | SPSS/Stata microdata, interactive dashboard |
| Content | 195,000 household survey: education, health, WASH, food insecurity, migration, disability. District-level estimates. 21 SDG indicators. |
| Key Indicators | Out-of-school children rate, food insecurity rate, migration rate — PREDICTIVE indicators for trafficking risk |

#### 2.10 PBS Labour Force Survey

| Field | Value |
|-------|-------|
| URL | https://www.pbs.gov.pk/labour-force-statistics/ |
| Key PDF | https://www.pbs.gov.pk/sites/default/files/labour_force/publications/lfs2020_21/Key_Findings_of_Labour_Force_Survey_2020-21.pdf |
| Content | Employment by province/district/sex/age, child labor indicators (10-14 age group), NEET data |

#### 2.11 NCSW/UNICEF Violence Against Children Mapping Study (2024)

| Field | Value |
|-------|-------|
| URL | https://ngdp-ncsw.org.pk/storage/6865729cf1528.pdf |
| Content | District-level violence rates including 121 trafficking cases and 53 child marriage cases across 4 provinces |
| Notes | Contains rare DISTRICT-LEVEL trafficking case data that most sources lack |

---

### P2 — MEDIUM (PDF Parsing or Complex Scraping Required)

#### 3.1 ZARRA Missing Children Data

| Field | Value |
|-------|-------|
| URL | https://zarra.mohr.gov.pk/ (web portal, JS-rendered, requires registration) |
| PDF Report | https://mohr.gov.pk/SiteImage/Misc/files/ZARRA%20Data%20Analysis%20Report%20Oct,%202021%20-%20June,%202022.pdf |
| Content | National missing/abducted children database. 3,639 cases; 2,130 closures; 592 open. District-level with geo-tags. |
| Distribution | Punjab ~72%, Sindh ~11%, KP ~3%, Balochistan ~2%, ICT ~6% |
| Access Limitation | Web portal behind authentication; PDF reports are the accessible path |

#### 3.2 FIA Annual Reports

| Field | Value |
|-------|-------|
| URL | https://www.fia.gov.pk/ |
| PDFs | `/files/publications/686234992.pdf` (2024), `/files/publications/1069384536.pdf` (2019) |
| Content | Case counts by year, deportee statistics, trafficking routes, AHTC personnel (781 staff) |
| Challenge | Server unstable (ConnectTimeout). PDF extraction required. |

#### 3.3 UNICEF MICS Data

| Field | Value |
|-------|-------|
| URL | https://mics.unicef.org/ (MICS Tabulator for custom queries) |
| Microdata | https://microdata.worldbank.org/ (search "Pakistan MICS") |
| Content | 120+ socioeconomic indicators at divisional/district levels. Child protection module: child labor, child marriage, birth registration. |
| Key Surveys | Punjab MICS 2017-18 (district-representative), Sindh MICS 2014 |
| Access | Registration required for microdata |

#### 3.4 DHS 2017-18 Pakistan

| Field | Value |
|-------|-------|
| URL | https://dhsprogram.com/ (registration required, free) |
| API | https://api.dhsprogram.com/ |
| Content | 8 regions with GPS cluster coordinates. Health, education, protection indicators. |

#### 3.5 Court Systems

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

**Relevant PPC sections:** 366-A (kidnapping woman to compel marriage), 366-B (importation of girl), 369 (kidnapping child under 10), 370 (buying/selling person for slavery), 371-A (selling person for prostitution), 371-B (buying person for prostitution)

**Relevant statutes:** Prevention of Trafficking in Persons Act 2018, Zainab Alert Act 2020, Punjab Destitute and Neglected Children Act 2004, Bonded Labour System (Abolition) Act 1992

#### 3.6 News Media Sources

| Source | URL | RSS Feed | Paywall | JS | Priority | Scraping Tool |
|--------|-----|----------|---------|-----|----------|---------------|
| Dawn | dawn.com | `dawn.com/feeds/home` | No | No | P2-A | Scrapy |
| Express Tribune | tribune.com.pk | `/feed` (WordPress) | No | No | P2-A | Scrapy |
| The News | thenews.com.pk | Available | No | No | P2-B | Scrapy |
| Geo News | geo.tv | None | No | Heavy | P2-B | Playwright |
| ARY News | arynews.tv | `arynews.tv/feed` | No | No | P2-C | Scrapy |
| Samaa TV | samaa.tv | Unknown | No | Heavy | P2-C | Playwright |
| Pakistan Today | pakistantoday.com.pk | Likely (WP) | No | No | P2-C | Scrapy |

**Express Tribune dedicated tag:** `https://tribune.com.pk/child-trafficking/`

#### 3.7 Provincial Police Data

| Province | URL | Public Data | Status |
|----------|-----|-------------|--------|
| Punjab | https://punjabpolice.gov.pk/missing-persons, /crimestatistics | Missing persons (quarterly), crime stats | Accessible |
| Sindh | https://sindhpolice.gov.pk/annoucements/crime_stat_all_cities.html | Range-level crime stats | Partially blocked (missing_person: 403) |
| KP | https://www.kppolice.gov.pk/ | KP CPWC facts: https://kpcpwc.gov.pk/factsandfigure.html | Most data pages return 403 |
| Balochistan | https://balochistanpolice.gov.pk/crime_statistics | All Crime, Major Crime Heads, Terrorism | Accessible |

#### 3.8 UK DFID Modern Slavery Report (2019)

| Field | Value |
|-------|-------|
| URL | https://assets.publishing.service.gov.uk/media/5e56a35a86650c53b6909337/DFID_Modern_Slavery_in_Pakistan_.pdf |
| Content | Sector-specific data (brick kilns, agriculture, domestic work) and geographic hotspot identification |

#### 3.9 NCRC Annual Report

| Field | Value |
|-------|-------|
| URL | https://ncrc.gov.pk/wp-content/uploads/2025/07/Annual-Report-24-25.pdf |
| Content | First comprehensive State of Children report covering health, education, protection, welfare |

#### 3.10 Academic & Research Sources

| Source | URL | Content | Format |
|--------|-----|---------|--------|
| Aurat Foundation Internal Trafficking Study | https://af.org.pk/gep/images/Research%20Studies%20(Gender%20Based%20Violence)/study%20on%20trafficking%20final.pdf | Internal trafficking routes, victim profiles, district-level field data | PDF |
| SDPI Child Trafficking Project (ILO) | https://sdpi.org/sdpiweb/publications/files/2004-05.pdf | Swat Valley community-level surveys | PDF |
| LUMS CBS Child Labor Analysis | https://cbs.lums.edu.pk/student-research-series/child-labor-pakistan-policy-analysis | Policy analysis with data | PDF |
| ECPAT Pakistan Reports | https://ecpat.org/wp-content/uploads/2022/03/Gobal-Boys-Initiative_Pakistan-Report_FINAL.pdf | Hotspot identification (hotels, truck stops, shrines, mining) | PDF |
| ECPAT Supplementary Report | https://pahchaan.info/wp-content/uploads/2025/05/Supplementary-report-on-Sexual-Exploitation-of-Children-in-Pakistan.pdf | Prosecution data, legal framework analysis | PDF |
| HRW 1995 Bonded Labor Report | https://www.hrw.org/legacy/reports/1995/Pakistan.htm | Named brick kiln sites, district-specific data (historical) | HTML |
| HRCP Modern Slavery Report | https://hrcp-web.org/hrcpweb/wp-content/uploads/2020/09/2022-Modern-slavery-1.pdf | Province-by-province trafficking analysis | PDF |
| Organized Crime Index | https://ocindex.net/country/pakistan | Structured crime assessment scores | Web (may have API) |

---

### P3 — LONG-TERM (Institutional Access, RTI Requests, or Internal Data)

#### 4.1 Helpline & Reporting Data

| Source | Contact | Data Held | Public Access |
|--------|---------|-----------|---------------|
| Roshni Helpline | 0800-22444 / https://roshnihelpline.org/ | 13,000+ children recovered since 2003; 2,633 missing cases (2023) | Press releases only |
| Madadgaar (LHRLA) | 1098 / http://madadgaar.org/ | 223,000+ calls; 71 data categories | Internal only |
| MoHR Helpline | 1099 | Case tracking, referrals | Internal (ZARRA linked) |
| Legal Aid Society SLACC | https://www.las.org.pk/nazassist/ | 475,000+ calls from 600+ towns since 2014 | Limited |

**Strategy:** Extract from press releases/annual reports. Pursue formal data sharing agreements.

#### 4.2 Paid Legal Databases

| Platform | URL | Access | Notes |
|----------|-----|--------|-------|
| PakistanLawSite | https://www.pakistanlawsite.com/ | Rs. 36,000/year | ToS prohibits bulk download |
| Pak Legal Database | https://www.paklegaldatabase.com/ | Subscription | |
| legislation.pk | https://www.legislation.pk/ | FREE | For statute text only (P1) |

#### 4.3 Punjab Police e-FIR System

878K+ FIRs since 2017. Entirely behind police authentication. Requires formal data sharing agreement or RTI request.

---

## Part 2: Database Schema

### Extensions

```sql
CREATE EXTENSION postgis;
CREATE EXTENSION pg_trgm;
CREATE EXTENSION unaccent;
```

### Table 1: boundaries

Administrative boundary polygons. The geographic foundation table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-increment ID |
| admin_level | INT | NOT NULL | 0=country, 1=province, 2=district, 3=tehsil |
| name_en | VARCHAR(255) | NOT NULL | English name |
| name_ur | VARCHAR(255) | | Urdu name |
| pcode | VARCHAR(20) | UNIQUE NOT NULL | OCHA P-code (universal join key) |
| parent_pcode | VARCHAR(20) | FK -> boundaries(pcode) | Parent boundary P-code |
| geometry | GEOMETRY(MultiPolygon, 4326) | NOT NULL | Boundary polygon (WGS84) |
| population_total | BIGINT | | Total population (Census 2017) |
| population_male | BIGINT | | Male population |
| population_female | BIGINT | | Female population |
| population_urban | BIGINT | | Urban population |
| population_rural | BIGINT | | Rural population |
| area_sqkm | FLOAT | | Area in square kilometers |

**Indexes:** GiST on geometry, B-tree on pcode, B-tree on admin_level.

### Table 2: district_name_variants

Crosswalk for fuzzy district name matching.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| variant_name | VARCHAR(255) | NOT NULL | Alternative name/spelling |
| canonical_pcode | VARCHAR(20) | FK -> boundaries(pcode), NOT NULL | Canonical P-code |
| source | VARCHAR(100) | | Which dataset uses this variant |

**Unique constraint:** (variant_name, source)

### Table 3: incidents

Master normalized incident table aggregating all sources.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| source_type | VARCHAR(50) | NOT NULL | sahil, ssdo, zarra, news, court, tip_report, ctdc |
| source_id | VARCHAR(255) | | Original ID from source system |
| source_url | TEXT | | URL of original source |
| incident_date | DATE | | Date of incident |
| report_date | DATE | | Date incident was reported |
| year | INT | NOT NULL | Year of incident |
| month | INT | | Month of incident |
| district_pcode | VARCHAR(20) | FK -> boundaries(pcode) | District where incident occurred |
| province_pcode | VARCHAR(20) | FK -> boundaries(pcode) | Province P-code |
| location_detail | TEXT | | Descriptive location text |
| geometry | GEOMETRY(Point, 4326) | | Geocoded point (lat/lon) |
| geocode_confidence | FLOAT | | 0-1 geocoding confidence score |
| incident_type | VARCHAR(50) | NOT NULL | kidnapping, sexual_abuse, bonded_labor, trafficking, child_marriage, begging, organ_trafficking, missing |
| sub_type | VARCHAR(100) | | More specific classification |
| victim_count | INT | DEFAULT 1 | Number of victims |
| victim_gender | VARCHAR(20) | | male, female, mixed, unknown |
| victim_age_min | INT | | Youngest victim age |
| victim_age_max | INT | | Oldest victim age |
| victim_age_bracket | VARCHAR(20) | | 0-5, 6-10, 11-15, 16-18 |
| perpetrator_type | VARCHAR(50) | | acquaintance, stranger, family, employer, gang, unknown |
| perpetrator_count | INT | | Number of perpetrators |
| fir_registered | BOOLEAN | | Whether FIR was filed |
| case_status | VARCHAR(50) | | reported, investigated, prosecuted, convicted, acquitted, pending |
| conviction | BOOLEAN | | Whether conviction was obtained |
| sentence_detail | TEXT | | Sentencing information |
| extraction_confidence | FLOAT | | NLP extraction confidence |
| raw_text | TEXT | | Original text for audit |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation time |
| updated_at | TIMESTAMP | DEFAULT NOW() | Last update time |

**Indexes:** GiST on geometry, B-tree on district_pcode, year, incident_type, source_type.

### Table 4: brick_kilns

Geolocated brick kiln points from Zenodo.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| geometry | GEOMETRY(Point, 4326) | NOT NULL | Kiln location |
| kiln_type | VARCHAR(20) | | FCBK, ZigZag |
| nearest_school_m | FLOAT | | Distance to nearest school (meters) |
| nearest_hospital_m | FLOAT | | Distance to nearest hospital (meters) |
| population_1km | INT | | Population within 1km radius |
| district_pcode | VARCHAR(20) | FK -> boundaries(pcode) | Assigned via spatial join |
| source | VARCHAR(100) | DEFAULT 'zenodo_2024' | Data source |

**Indexes:** GiST on geometry, B-tree on district_pcode.

### Table 5: border_crossings

International border crossing points.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| name | VARCHAR(255) | NOT NULL | Crossing name |
| border_country | VARCHAR(50) | NOT NULL | afghanistan, iran, india, china |
| crossing_type | VARCHAR(50) | | official, unofficial |
| geometry | GEOMETRY(Point, 4326) | NOT NULL | Crossing location |
| is_active | BOOLEAN | DEFAULT true | Whether currently operational |
| vulnerability_score | FLOAT | | Calculated vulnerability (0-100) |
| notes | TEXT | | Additional information |

### Table 6: trafficking_routes

Constructed trafficking route geometries.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| route_name | VARCHAR(255) | | Descriptive route name |
| origin_pcode | VARCHAR(20) | FK -> boundaries(pcode) | Origin district |
| origin_country | VARCHAR(50) | | Origin country (if cross-border) |
| destination_pcode | VARCHAR(20) | FK -> boundaries(pcode) | Destination district |
| destination_country | VARCHAR(50) | | Destination country |
| transit_points | JSONB | | Array of {name, lat, lon, pcode} |
| route_geometry | GEOMETRY(LineString, 4326) | | Route line |
| trafficking_type | VARCHAR(50) | | labor, sexual, organ, begging, marriage |
| evidence_source | TEXT | | Source documentation |
| confidence_level | VARCHAR(20) | | high, medium, low |
| year_documented | INT | | Year evidence was documented |
| notes | TEXT | | |

### Table 7: court_judgments

Structured court case records with NLP-extracted fields.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| court_name | VARCHAR(100) | NOT NULL | Court name |
| court_bench | VARCHAR(100) | | Bench/city |
| case_number | VARCHAR(255) | | Official case number |
| judgment_date | DATE | | Date of judgment |
| judge_names | TEXT[] | | Array of judge names |
| appellant | TEXT | | Appellant party |
| respondent | TEXT | | Respondent party |
| ppc_sections | TEXT[] | | Array of PPC sections cited |
| statutes | TEXT[] | | Array of statutes cited |
| is_trafficking_related | BOOLEAN | | NLP classification |
| trafficking_type | VARCHAR(50) | | Type of trafficking |
| incident_district_pcode | VARCHAR(20) | FK -> boundaries(pcode) | District of incident |
| court_district_pcode | VARCHAR(20) | FK -> boundaries(pcode) | District of court |
| verdict | VARCHAR(50) | | convicted, acquitted, dismissed, pending |
| sentence | TEXT | | Full sentencing text |
| sentence_years | FLOAT | | Numeric sentence duration |
| judgment_text | TEXT | | Full judgment text |
| pdf_url | TEXT | | URL to judgment PDF |
| source_url | TEXT | | URL of source system |
| nlp_confidence | FLOAT | | NLP extraction confidence |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes:** B-tree on judgment_date, incident_district_pcode. GIN on ppc_sections array.

### Table 8: vulnerability_indicators

Per-district, per-year composite vulnerability data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| district_pcode | VARCHAR(20) | FK -> boundaries(pcode), NOT NULL | District |
| year | INT | NOT NULL | Year of data |
| school_enrollment_rate | FLOAT | | Education enrollment rate |
| school_dropout_rate | FLOAT | | School dropout rate |
| out_of_school_children | INT | | Count of out-of-school children |
| literacy_rate | FLOAT | | Literacy rate |
| poverty_headcount_ratio | FLOAT | | Poverty rate |
| food_insecurity_rate | FLOAT | | Food insecurity rate |
| child_labor_rate | FLOAT | | Child labor rate |
| unemployment_rate | FLOAT | | Unemployment rate |
| population_under_18 | INT | | Population under 18 |
| birth_registration_rate | FLOAT | | Birth registration rate |
| child_marriage_rate | FLOAT | | Child marriage rate |
| refugee_population | INT | | Refugee population |
| brick_kiln_count | INT | | Brick kilns in district |
| brick_kiln_density_per_sqkm | FLOAT | | Kilns per square km |
| distance_to_border_km | FLOAT | | Distance to nearest border |
| flood_affected_pct | FLOAT | | Percent area flood-affected |
| trafficking_risk_score | FLOAT | | Composite score 0-100 |
| source | VARCHAR(100) | | Data source |

**Unique constraint:** (district_pcode, year)

### Table 9: tip_report_annual

24-year time series from US State Department TIP Reports.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| year | INT | UNIQUE NOT NULL | Report year |
| tier_ranking | VARCHAR(50) | | Tier ranking |
| ptpa_investigations | INT | | PTPA investigation count |
| ptpa_prosecutions | INT | | PTPA prosecution count |
| ptpa_convictions | INT | | PTPA conviction count |
| ptpa_sex_trafficking_inv | INT | | Sex trafficking investigations |
| ptpa_forced_labor_inv | INT | | Forced labor investigations |
| ppc_investigations | INT | | PPC investigation count |
| ppc_prosecutions | INT | | PPC prosecution count |
| ppc_convictions | INT | | PPC conviction count |
| victims_identified | INT | | Victims identified |
| victims_referred | INT | | Victims referred to services |
| budget_allocated_pkr | BIGINT | | Budget in PKR |
| key_findings | TEXT | | Qualitative findings |
| recommendations | TEXT | | TIP Report recommendations |
| named_hotspots | TEXT[] | | Named locations/hotspots |
| source_url | TEXT | | URL to TIP Report page |

### Table 10: public_reports

Citizen-submitted incident reports.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| report_type | VARCHAR(50) | NOT NULL | suspicious_activity, missing_child, bonded_labor, begging_ring, child_marriage, other |
| description | TEXT | | Report description |
| geometry | GEOMETRY(Point, 4326) | | Report location |
| district_pcode | VARCHAR(20) | FK -> boundaries(pcode) | Auto-geocoded district |
| address_detail | TEXT | | Address text |
| photos | JSONB | | Array of S3 URLs |
| reporter_name | VARCHAR(255) | | Optional (encrypted) |
| reporter_contact | VARCHAR(255) | | Optional (encrypted) |
| is_anonymous | BOOLEAN | DEFAULT true | |
| status | VARCHAR(50) | DEFAULT 'submitted' | submitted, verified, referred, resolved, rejected |
| referred_to | VARCHAR(255) | | Agency referred to |
| ip_hash | VARCHAR(64) | | SHA-256 hashed IP |
| created_at | TIMESTAMP | DEFAULT NOW() | |
| updated_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes:** GiST on geometry, B-tree on status, report_type.

### Table 11: news_articles

Scraped news articles with NER-extracted data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| source_name | VARCHAR(100) | NOT NULL | News source name |
| url | TEXT | UNIQUE NOT NULL | Article URL |
| title | TEXT | NOT NULL | Article headline |
| published_date | DATE | | Publication date |
| extracted_incidents | JSONB | | Array of extracted incident objects |
| extracted_locations | JSONB | | Array of {name, lat, lon, confidence} |
| extracted_entities | JSONB | | Full NER results |
| is_trafficking_relevant | BOOLEAN | | Classification result |
| relevance_score | FLOAT | | Classification confidence |
| full_text | TEXT | | Full article text |
| created_at | TIMESTAMP | DEFAULT NOW() | |

**Indexes:** B-tree on published_date, source_name.

### Table 12: data_sources

Registry for tracking data source health and freshness.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | |
| name | VARCHAR(255) | NOT NULL | Source name |
| url | TEXT | | Source URL |
| source_type | VARCHAR(50) | | government, ngo, international, news, academic, citizen |
| priority | VARCHAR(5) | | P0, P1, P2, P3 |
| last_scraped | TIMESTAMP | | Last successful scrape |
| last_updated | TIMESTAMP | | Last time new data was found |
| scraper_name | VARCHAR(100) | | Name of the scraper module |
| record_count | INT | | Number of records from this source |
| is_active | BOOLEAN | DEFAULT true | Whether source is being actively scraped |
| notes | TEXT | | |

---

## Part 3: Known Data Gaps

| Gap | Impact | Mitigation |
|-----|--------|------------|
| No district-level FIR data publicly available | Cannot map incidents at high resolution from official sources | File RTI requests to 4 provincial police departments (follow SSDO methodology) |
| ZARRA data behind authentication | Best missing children dataset is inaccessible for automation | Parse published PDF reports; pursue formal data sharing with MoHR |
| No structured trafficking route data | Routes must be manually constructed from narrative sources | Extract from TIP Reports, FIA reports, research papers using NLP |
| Sahil data province-level (district sporadic) | Heat maps limited to provincial resolution for primary dataset | Supplement with SSDO district data, news NER, NCSW mapping study |
| No Balochistan CPC online | Poorest province has worst data coverage | Rely on federal sources (TIP, CTDC) + news monitoring |
| Court systems don't search by offense | Cannot directly query trafficking cases | Download broadly, then NLP-classify |
| Social media data cost-prohibitive | Twitter/Facebook data inaccessible at scale | Focus on news media monitoring |

---

*This data dictionary is the reference for all data ingestion work. For API endpoints serving this data, see [API_SPEC.md](API_SPEC.md). For the full master blueprint, see [MASTER.md](../MASTER.md).*
