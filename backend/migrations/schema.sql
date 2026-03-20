-- =============================================================================
-- Nigehbaan — Pakistan Child Trafficking Intelligence Platform
-- Complete database schema (PostgreSQL + PostGIS)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ---------------------------------------------------------------------------
-- 1. Administrative Boundaries
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS boundaries (
    id              SERIAL PRIMARY KEY,
    admin_level     INTEGER NOT NULL,                        -- 1=country,2=province,3=division,4=district,5=tehsil
    name_en         VARCHAR(255) NOT NULL,
    name_ur         VARCHAR(255),
    pcode           VARCHAR(20) NOT NULL UNIQUE,
    parent_pcode    VARCHAR(20) REFERENCES boundaries(pcode),
    geometry        GEOMETRY(MULTIPOLYGON, 4326),
    population_total    INTEGER,
    population_male     INTEGER,
    population_female   INTEGER,
    population_urban    INTEGER,
    population_rural    INTEGER,
    area_sqkm       DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_boundaries_pcode       ON boundaries (pcode);
CREATE INDEX IF NOT EXISTS idx_boundaries_parent       ON boundaries (parent_pcode);
CREATE INDEX IF NOT EXISTS idx_boundaries_admin_level  ON boundaries (admin_level);
CREATE INDEX IF NOT EXISTS idx_boundaries_geom         ON boundaries USING GIST (geometry);

-- ---------------------------------------------------------------------------
-- 2. District Name Variants (crosswalk)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS district_name_variants (
    id              SERIAL PRIMARY KEY,
    variant_name    VARCHAR(255) NOT NULL,
    canonical_pcode VARCHAR(20) NOT NULL REFERENCES boundaries(pcode),
    source          VARCHAR(100),
    UNIQUE (variant_name, source)
);

CREATE INDEX IF NOT EXISTS idx_dnv_variant   ON district_name_variants (variant_name);
CREATE INDEX IF NOT EXISTS idx_dnv_pcode     ON district_name_variants (canonical_pcode);

-- ---------------------------------------------------------------------------
-- 3. Incidents
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS incidents (
    id                      SERIAL PRIMARY KEY,
    source_type             VARCHAR(50),
    source_id               VARCHAR(100),
    source_url              TEXT,
    incident_date           DATE,
    report_date             DATE,
    year                    INTEGER,
    month                   INTEGER,
    district_pcode          VARCHAR(20) REFERENCES boundaries(pcode),
    province_pcode          VARCHAR(20) REFERENCES boundaries(pcode),
    location_detail         TEXT,
    geometry                GEOMETRY(POINT, 4326),
    geocode_confidence      DOUBLE PRECISION,
    incident_type           VARCHAR(100),
    sub_type                VARCHAR(100),
    victim_count            INTEGER,
    victim_gender           VARCHAR(20),
    victim_age_min          INTEGER,
    victim_age_max          INTEGER,
    victim_age_bracket      VARCHAR(30),
    perpetrator_type        VARCHAR(100),
    perpetrator_count       INTEGER,
    fir_registered          BOOLEAN,
    case_status             VARCHAR(50),
    conviction              BOOLEAN,
    sentence_detail         TEXT,
    extraction_confidence   DOUBLE PRECISION,
    raw_text                TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_incidents_year          ON incidents (year);
CREATE INDEX IF NOT EXISTS idx_incidents_district      ON incidents (district_pcode);
CREATE INDEX IF NOT EXISTS idx_incidents_province      ON incidents (province_pcode);
CREATE INDEX IF NOT EXISTS idx_incidents_type          ON incidents (incident_type);
CREATE INDEX IF NOT EXISTS idx_incidents_geom          ON incidents USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_incidents_source_type   ON incidents (source_type);

-- ---------------------------------------------------------------------------
-- 4. Brick Kilns
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS brick_kilns (
    id                  SERIAL PRIMARY KEY,
    geometry            GEOMETRY(POINT, 4326) NOT NULL,
    kiln_type           VARCHAR(50),
    nearest_school_m    DOUBLE PRECISION,
    nearest_hospital_m  DOUBLE PRECISION,
    population_1km      INTEGER,
    district_pcode      VARCHAR(20) REFERENCES boundaries(pcode),
    source              VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_kilns_district ON brick_kilns (district_pcode);
CREATE INDEX IF NOT EXISTS idx_kilns_geom     ON brick_kilns USING GIST (geometry);

-- ---------------------------------------------------------------------------
-- 5. Border Crossings
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS border_crossings (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(255) NOT NULL,
    border_country      VARCHAR(100),
    crossing_type       VARCHAR(50),
    geometry            GEOMETRY(POINT, 4326) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    vulnerability_score DOUBLE PRECISION,
    notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_borders_geom ON border_crossings USING GIST (geometry);

-- ---------------------------------------------------------------------------
-- 6. Trafficking Routes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trafficking_routes (
    id                  SERIAL PRIMARY KEY,
    route_name          VARCHAR(255),
    origin_pcode        VARCHAR(20) REFERENCES boundaries(pcode),
    origin_country      VARCHAR(100),
    destination_pcode   VARCHAR(20) REFERENCES boundaries(pcode),
    destination_country VARCHAR(100),
    transit_points      JSONB,
    route_geometry      GEOMETRY(LINESTRING, 4326),
    trafficking_type    VARCHAR(100),
    evidence_source     VARCHAR(255),
    confidence_level    DOUBLE PRECISION,
    year_documented     INTEGER,
    notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_routes_geom ON trafficking_routes USING GIST (route_geometry);

-- ---------------------------------------------------------------------------
-- 7. Court Judgments
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS court_judgments (
    id                      SERIAL PRIMARY KEY,
    court_name              VARCHAR(100),
    court_bench             VARCHAR(100),
    case_number             VARCHAR(100),
    judgment_date           DATE,
    judge_names             TEXT[],
    appellant               TEXT,
    respondent              TEXT,
    ppc_sections            TEXT[],
    statutes                TEXT[],
    is_trafficking_related  BOOLEAN,
    trafficking_type        VARCHAR(100),
    incident_district_pcode VARCHAR(20) REFERENCES boundaries(pcode),
    court_district_pcode    VARCHAR(20) REFERENCES boundaries(pcode),
    verdict                 VARCHAR(50),
    sentence                TEXT,
    sentence_years          DOUBLE PRECISION,
    judgment_text           TEXT,
    pdf_url                 TEXT,
    source_url              TEXT,
    nlp_confidence          DOUBLE PRECISION,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cj_court        ON court_judgments (court_name);
CREATE INDEX IF NOT EXISTS idx_cj_case_number  ON court_judgments (case_number);
CREATE INDEX IF NOT EXISTS idx_cj_judgment_date ON court_judgments (judgment_date);
CREATE INDEX IF NOT EXISTS idx_cj_district     ON court_judgments (incident_district_pcode);
CREATE INDEX IF NOT EXISTS idx_cj_ppc          ON court_judgments USING GIN (ppc_sections);
CREATE INDEX IF NOT EXISTS idx_cj_statutes     ON court_judgments USING GIN (statutes);

-- ---------------------------------------------------------------------------
-- 8. Vulnerability Indicators
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vulnerability_indicators (
    id                          SERIAL PRIMARY KEY,
    district_pcode              VARCHAR(20) NOT NULL REFERENCES boundaries(pcode),
    year                        INTEGER NOT NULL,
    school_enrollment_rate      DOUBLE PRECISION,
    school_dropout_rate         DOUBLE PRECISION,
    out_of_school_children      INTEGER,
    literacy_rate               DOUBLE PRECISION,
    poverty_headcount_ratio     DOUBLE PRECISION,
    food_insecurity_rate        DOUBLE PRECISION,
    child_labor_rate            DOUBLE PRECISION,
    unemployment_rate           DOUBLE PRECISION,
    population_under_18         INTEGER,
    birth_registration_rate     DOUBLE PRECISION,
    child_marriage_rate         DOUBLE PRECISION,
    refugee_population          INTEGER,
    brick_kiln_count            INTEGER,
    brick_kiln_density_per_sqkm DOUBLE PRECISION,
    distance_to_border_km       DOUBLE PRECISION,
    flood_affected_pct          DOUBLE PRECISION,
    trafficking_risk_score      DOUBLE PRECISION,
    source                      VARCHAR(255),
    UNIQUE (district_pcode, year)
);

CREATE INDEX IF NOT EXISTS idx_vuln_district ON vulnerability_indicators (district_pcode);
CREATE INDEX IF NOT EXISTS idx_vuln_year     ON vulnerability_indicators (year);

-- ---------------------------------------------------------------------------
-- 9. TIP Report Annual
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tip_report_annual (
    id                      SERIAL PRIMARY KEY,
    year                    INTEGER NOT NULL UNIQUE,
    tier_ranking            VARCHAR(20),
    ptpa_investigations     INTEGER,
    ptpa_prosecutions       INTEGER,
    ptpa_convictions        INTEGER,
    ptpa_sex_trafficking_inv INTEGER,
    ptpa_forced_labor_inv   INTEGER,
    ppc_investigations      INTEGER,
    ppc_prosecutions        INTEGER,
    ppc_convictions         INTEGER,
    victims_identified      INTEGER,
    victims_referred        INTEGER,
    budget_allocated_pkr    DOUBLE PRECISION,
    key_findings            TEXT,
    recommendations         TEXT,
    named_hotspots          TEXT[],
    source_url              TEXT
);

CREATE INDEX IF NOT EXISTS idx_tip_year ON tip_report_annual (year);

-- ---------------------------------------------------------------------------
-- 10. Public Reports
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public_reports (
    id              SERIAL PRIMARY KEY,
    report_type     VARCHAR(100) NOT NULL,
    description     TEXT NOT NULL,
    geometry        GEOMETRY(POINT, 4326),
    district_pcode  VARCHAR(20) REFERENCES boundaries(pcode),
    address_detail  TEXT,
    photos          JSONB,
    reporter_name   VARCHAR(255),
    reporter_contact VARCHAR(255),
    is_anonymous    BOOLEAN NOT NULL DEFAULT TRUE,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending',
    referred_to     VARCHAR(255),
    ip_hash         VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pr_district ON public_reports (district_pcode);
CREATE INDEX IF NOT EXISTS idx_pr_status   ON public_reports (status);
CREATE INDEX IF NOT EXISTS idx_pr_geom     ON public_reports USING GIST (geometry);

-- ---------------------------------------------------------------------------
-- 11. News Articles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS news_articles (
    id                      SERIAL PRIMARY KEY,
    source_name             VARCHAR(255),
    url                     TEXT NOT NULL UNIQUE,
    title                   TEXT,
    published_date          DATE,
    extracted_incidents     JSONB,
    extracted_locations     JSONB,
    extracted_entities      JSONB,
    is_trafficking_relevant BOOLEAN,
    relevance_score         DOUBLE PRECISION,
    full_text               TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_na_source   ON news_articles (source_name);
CREATE INDEX IF NOT EXISTS idx_na_pubdate  ON news_articles (published_date);
CREATE INDEX IF NOT EXISTS idx_na_url      ON news_articles (url);
CREATE INDEX IF NOT EXISTS idx_na_entities ON news_articles USING GIN (extracted_entities);

-- ---------------------------------------------------------------------------
-- 12. Data Sources
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_sources (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    url             TEXT,
    source_type     VARCHAR(50),
    priority        INTEGER,
    last_scraped    TIMESTAMPTZ,
    last_updated    TIMESTAMPTZ,
    scraper_name    VARCHAR(100),
    record_count    INTEGER,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    notes           TEXT
);
