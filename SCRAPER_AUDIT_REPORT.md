# Nigehbaan Scraper Audit Report

**Date:** 2026-03-20
**Auditor:** Claude Opus 4.6
**EC2:** ubuntu@3.110.174.178 (t2.small, Mumbai)
**DB:** Neon PostgreSQL (ep-dawn-scene-a1vqoqjj.ap-southeast-1.aws.neon.tech)

---

## Executive Summary

**Data IS flowing.** 436 news articles were created today via Celery scheduled tasks. The monitoring loop's "no data growth" concern was misleading because:

1. All 436 articles were created TODAY (March 20) — the system started fresh
2. After initial scrape, subsequent runs find duplicates (URL dedup) so counts stabilize
3. Non-news scrapers save to raw files but **do NOT persist to the database**

**Critical finding:** Only 6 news scrapers write to `news_articles` table. The other 17 scrapers (courts, police, international, government) only update the `data_sources` metadata table — their actual scraped data goes to raw JSON files only.

---

## Database State

### Table Counts (Post-Audit)

| Table | Records | Notes |
|-------|---------|-------|
| news_articles | 436 | All created 2026-03-20 |
| incidents | 189 | Created 2026-03-19 (seed data) |
| data_sources | 46 | Scraper registry |
| court_judgments | 0 | No court data saved to DB |
| public_reports | 1 | Single record |
| vulnerability_indicators | 121 | Seed/init data |
| trafficking_routes | 8 | Seed/init data |
| border_crossings | 15 | Seed/init data |
| brick_kilns | 11,272 | GIS dataset |
| tip_report_annual | 0 | Never populated |

### Articles by Source

| Source | Count | First Created | Last Created |
|--------|-------|---------------|--------------|
| rss_monitor | 404 | 2026-03-20 00:36 UTC | 2026-03-20 07:00 UTC |
| tribune | 23 | 2026-03-20 01:03 UTC | 2026-03-20 01:03 UTC |
| geo_news | 4 | 2026-03-20 08:15 UTC | 2026-03-20 08:15 UTC |
| the_news | 4 | 2026-03-20 00:51 UTC | 2026-03-20 00:51 UTC |
| dawn | 1 | 2026-03-20 00:35 UTC | 2026-03-20 00:35 UTC |

### Active Data Sources (with last_scraped timestamps)

| Scraper | Record Count | Last Scraped |
|---------|-------------|-------------|
| geo_news | 4 | 2026-03-20 08:15 UTC |
| ary_news | 0 | 2026-03-20 08:00 UTC |
| the_news | 12 | 2026-03-20 07:45 UTC |
| tribune | 69 | 2026-03-20 07:30 UTC |
| dawn | 4 | 2026-03-20 07:15 UTC |
| rss_monitor | 968 | 2026-03-20 07:00 UTC |
| worldbank_api | 501 | 2026-03-20 00:34 UTC |

27 other data_sources entries have NULL last_scraped (never ran via Celery).

---

## Phase 2: Hard-Run Results (All 23 Scrapers)

### International Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| worldbank_api | PASS | 501 | - |
| tip_report | PARTIAL | ~10+ | Many year URLs return 404 (2004-2005 reports removed from state.gov) |
| unhcr_api | PASS | 166 | - |
| unodc | FAIL | 0 | GLO.ACT publications page returns 404 (site restructured) |
| dol_child_labor | FAIL | 0 | Page loads but 0 report links found (selector mismatch) |

### News Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| dawn | PASS | 3 | - |
| tribune | PASS | 23 | RSS feed returns 403, but HTML fallback works |
| the_news | PASS | 4 | - |
| ary_news | FAIL | 0 | Returns 0 records (no matching articles found) |
| geo_news | PASS | 3 | Playwright not installed but httpx fallback works |
| rss_monitor | PASS | 316 | Tribune feed 403 (skipped), all others work |

### Government Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| stateofchildren | PASS | 66 | - |
| punjab_police | FAIL | 0 | Timeout — site blocks datacenter IPs |
| sindh_police | FAIL | 0 | 403 Forbidden (WAF blocks EC2) |
| kpcpwc | PASS | 16 | - |
| ssdo_checker | PASS | 15 | Live site returns 404, Wayback Machine fallback works |
| mohr_checker | FAIL | 0 | Timeout — site unresponsive |

### Court Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| scp | FAIL | 0 | 403 Forbidden (NADRA WAF blocks EC2) |
| lhc | FAIL | 0 | Timeout — site blocks datacenter IPs |
| shc | PARTIAL | 0 | Site responds but search returns no matching cases |
| phc | PARTIAL | 0 | Site responds (200 OK) but 0 cases match filters |
| bhc | FAIL | 0 | 0 records returned |
| ihc | FAIL | 0 | 0 records returned |
| commonlii | FAIL | 0 | 0 records returned |

---

## Summary Scorecard

| Category | Pass | Partial | Fail | Total |
|----------|------|---------|------|-------|
| International | 2 | 1 | 2 | 5 |
| News | 5 | 0 | 1 | 6 |
| Government | 3 | 0 | 3 | 6 |
| Courts | 0 | 2 | 5 | 7 |
| **TOTAL** | **10** | **3** | **11** | **24** |

**Overall: 10 PASS / 3 PARTIAL / 11 FAIL (42% pass rate)**

---

## Phase 3: Data Pipeline Analysis

### How Data Flows

```
Scraper.run() → raw JSON files (data/raw/<scraper>/<timestamp>.json)
                ↓ (only for news scrapers via Celery tasks)
         _save_news_articles() → news_articles table (URL dedup)
                ↓
         _enqueue_ai_processing() → process_article_ai (FAILS: OpenAI 401)
```

### Critical Pipeline Gap

**Non-news scrapers do NOT save to the database.** The Celery task code for courts, police, and international scrapers only calls `_update_data_source()` (updates metadata) but never calls a function to insert actual records into any table.

Affected scrapers:
- `scrape_tip_report` — saves raw files, updates data_sources, no DB insert
- `update_ctdc` (unodc) — same
- `scrape_worldbank_api` — same (501 records scraped but only saved to JSON)
- `scrape_unhcr_api` — same
- `scrape_courts` — same
- `scrape_police_data` — same
- `scrape_stateofchildren` — same
- `check_sahil_updates` — same

### Raw Data Files (Confirmed Present)

```
data/raw/dawn/          — 3 JSON files
data/raw/tribune/       — 2 JSON files
data/raw/the_news/      — 3 JSON files
data/raw/geo_news/      — 4 JSON files
data/raw/rss_monitor/   — 3 JSON files
data/raw/unodc/         — 4 CSV files
data/raw/ssdo_checker/  — 2 JSON files
data/raw/tip_report/    — 3 JSON files
```

---

## Blocking Issues

### 1. OpenAI API Key Invalid (401)
- AI extraction (`process_article_ai`) fails for all articles
- `is_trafficking_relevant`, `extracted_incidents`, `extracted_locations`, `extracted_entities` columns remain NULL
- **Impact:** No incident extraction, no AI classification

### 2. Government WAFs Block EC2 IPs
- Supreme Court (NADRA), Punjab Police, Sindh Police all return 403
- These sites block datacenter/cloud IP ranges
- **Fix options:** Residential proxy, or manual data collection

### 3. UNODC Site Restructured
- GLO.ACT publications page moved/removed (404)
- CTDC API endpoint may have changed
- **Fix:** Update URLs to new UNODC site structure

### 4. DOL Child Labor Selector Mismatch
- Page loads successfully (200 OK) but 0 report links extracted
- **Fix:** Update CSS selectors to match current page structure

### 5. Non-News Data Never Reaches DB
- 17 scrapers produce raw files but no DB records
- Missing: DB models + insert logic for worldbank, UNHCR, TIP, court, police data
- **Fix:** Create DB tables and insert functions for each data type

---

## Recommendations

### Priority 1 (Immediate)
1. **Fix the data pipeline gap** — Add DB insert logic for worldbank_api (501 records), unhcr_api (166 records), stateofchildren (66 records), kpcpwc (16 records), ssdo_checker (15 records). These scrapers work but data only goes to raw files.
2. **Fix OpenAI API key** — Replace with valid key so AI extraction works on the 436 existing articles.

### Priority 2 (Short-term)
3. **Fix DOL child labor selectors** — Page loads fine, just needs updated CSS selectors.
4. **Fix UNODC URLs** — Find new GLO.ACT publications page location.
5. **Fix ARY News scraper** — Returns 0 records despite site being accessible.

### Priority 3 (Requires Infrastructure)
6. **Add residential proxy** — For Punjab Police, Sindh Police, Supreme Court, LHC scrapers that block EC2 IPs.
7. **Install Playwright** — For JS-heavy sites (Geo News currently falls back to httpx).

### Priority 4 (Nice-to-have)
8. **Fix TIP Report old year URLs** — Update URL patterns for pre-2010 reports.
9. **Court scraper search refinement** — SHC and PHC respond but return 0 cases (may need broader search terms).
10. **CommonLII scraper review** — Returns 0 records, may need complete rewrite.

---

## Why "No Data Growth" Was Observed

The monitoring loop was checking DB record counts. After the initial scrape inserted 436 articles:
- Subsequent scraper runs found the same URLs → URL dedup prevented duplicates
- Non-news scrapers never wrote to DB anyway
- Data was growing in **raw files** but not in the database
- New articles only appear when fresh content is published on news sites

**The system is working as designed** — it's just that the design only covers news → DB for 6 scrapers, while the other 17 only save raw files.
