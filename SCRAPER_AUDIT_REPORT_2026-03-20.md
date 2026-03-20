# Nigehbaan Scraper Audit Report

**Date:** 2026-03-20
**Instance:** ubuntu@3.110.174.178 (t2.small, Mumbai)
**Database:** Neon PostgreSQL (ep-dawn-scene-a1vqoqjj.ap-southeast-1.aws.neon.tech)

---

## Executive Summary

- **9 of 23 scrapers produce data** (raw files)
- **Only 6 scrapers insert data into the database** (all are news scrapers)
- **436 articles** in DB, **189 incidents** extracted
- **0 articles marked as trafficking-relevant** (OpenAI API key is invalid)
- **14 scrapers are completely broken** (blocked, timeout, or missing dependencies)

### Root Cause: Why No Data Growth Was Observed

Two critical pipeline gaps:

1. **`run_scraper.py` does NOT write to the database.** It only saves raw JSON files to `data/raw/`. Database insertion only happens through Celery scheduled tasks.

2. **Non-news scrapers never insert into DB.** Even via Celery, only the 6 news scraper tasks call `_save_news_articles()`. Courts, police, government, and international API scrapers only call `_update_data_source()` — they update the registry but discard their actual records.

---

## Database State (Pre-Audit Baseline)

| Table | Count |
|-------|-------|
| news_articles | 436 |
| incidents | 189 |
| data_sources | 46 |

| Source | Articles | First Created | Last Created |
|--------|----------|---------------|--------------|
| rss_monitor | 404 | 2026-03-20 00:36 | 2026-03-20 07:00 |
| tribune | 23 | 2026-03-20 01:03 | 2026-03-20 01:03 |
| geo_news | 4 | 2026-03-20 08:15 | 2026-03-20 08:15 |
| the_news | 4 | 2026-03-20 00:51 | 2026-03-20 00:51 |
| dawn | 1 | 2026-03-20 00:35 | 2026-03-20 00:35 |

**Incidents:** 188 from rss_monitor, 1 from dawn (all keyword-extracted, none AI-extracted)

**AI Processing:** 436/436 articles processed, but **0 marked as trafficking-relevant** because OpenAI API returns 401 (invalid key), so all fall back to keyword-only detection with `is_relevant=False, confidence=0.0`.

---

## Database State (Post-Audit)

| Table | Before | After | Delta |
|-------|--------|-------|-------|
| news_articles | 436 | 436 | 0 |
| incidents | 189 | 189 | 0 |
| data_sources | 46 | 46 | 0 |

**No change** — because `run_scraper.py` only saves raw files, not DB records.

---

## Scraper Hard-Run Results

### International API Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| worldbank_api | PASS | 501 | — |
| unhcr_api | PASS | 166 | — |
| tip_report | PARTIAL | ~10 | Years 2001-2004 all 404; 2005+ partial via archive redirect |
| unodc | FAIL | 0 | 404 on glo-act/publications.html (page migrated) |
| dol_child_labor | FAIL | 0 | API returns no data (format may have changed) |

### News Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| rss_monitor | PASS | 316 | Tribune RSS 403 (skipped), all other feeds OK |
| tribune | PASS | 23 | RSS feed 403, falls back to HTML scraping |
| the_news | PASS | 4 | — |
| dawn | PASS | 3 | — |
| geo_news | PASS | 3 | Playwright missing, falls back to RSS/HTTP |
| ary_news | PASS | 1 | Low article count (narrow keyword match) |

### Government Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| stateofchildren | PASS | 66 | — |
| kpcpwc | PASS | 16 | — |
| ssdo_checker | PASS | 15 | Live site 404, Wayback Machine fallback works |
| mohr_checker | TIMEOUT | ? | No output captured (likely slow/hanging) |
| punjab_police | FAIL | 0 | Connection timeout to punjabpolice.gov.pk |
| sindh_police | FAIL | 0 | 403 Forbidden (WAF blocks scraper) |

### Court Scrapers

| Scraper | Status | Records | Error |
|---------|--------|---------|-------|
| scp | FAIL | 0 | 403 Forbidden (NADRA firewall blocks all requests) |
| lhc | FAIL | 0 | Connection timeout to data.lhc.gov.pk |
| shc | FAIL | 0 | Timeout / no output |
| phc | FAIL | 0 | Timeout / no output |
| bhc | FAIL | 0 | Playwright not installed (chromium missing) |
| ihc | FAIL | 0 | Returns 0 records (no matching judgments found) |
| commonlii | FAIL | 0 | Returns 0 records (search yields no results) |

---

## Raw File Evidence

| Scraper | Raw Files | Latest File |
|---------|-----------|-------------|
| dawn | 6 | 2026-03-20 |
| rss_monitor | 6 | 2026-03-20 |
| kpcpwc | 3 | 2026-03-20 |
| stateofchildren | 3 | 2026-03-20 |
| unhcr_api | 3 | 2026-03-20 |
| worldbank_api | 3 | 2026-03-20 |
| geo_news | (in container only) | 2026-03-20 |
| the_news | (in container only) | 2026-03-20 |
| tribune | (in container only) | 2026-03-20 |
| ssdo_checker | (in container only) | 2026-03-20 |
| tip_report | (in container only) | 2026-03-20 |

---

## Summary Scorecard

| Category | Pass | Partial | Fail | Total |
|----------|------|---------|------|-------|
| International APIs | 2 | 1 | 2 | 5 |
| News | 6 | 0 | 0 | 6 |
| Government | 3 | 0 | 3 | 6 |
| Courts | 0 | 0 | 7 | 7 |
| **TOTAL** | **11** | **1** | **12** | **24** |

**Overall: 11 PASS / 1 PARTIAL / 12 FAIL (46% success rate)**

---

## Critical Issues

### 1. BLOCKER: Non-News Scrapers Don't Insert Into Database

**File:** `backend/app/tasks/scraping_tasks.py`

Only the 6 news Celery tasks call `_save_news_articles()`. All other tasks (courts, police, government, international) only call `_update_data_source()` which updates the registry counter but **never inserts actual records** into any table.

**Impact:** 11 working scrapers produce data that is saved to raw JSON files but **never reaches the database**.

**Fix needed:** Add DB insert logic for non-news data types (WorldBank indicators, UNHCR refugee stats, court judgments, government reports, etc.). This may require:
- New DB tables (e.g., `indicator_data`, `court_judgments`, `reports`)
- Or a generic `raw_records` table for all non-article data
- Or extend `_save_news_articles()` to handle non-article record formats

### 2. BLOCKER: OpenAI API Key Invalid (401)

**Error:** `Incorrect API key provided: sk-proj-...Gb0A`

**Impact:** AI extraction fails for all articles. Keyword pre-filter still works (creates 189 incidents from keyword matches), but `is_trafficking_relevant` is always `False` and `relevance_score` is always `0.0`. No structured entity extraction occurs.

**Fix:** Replace the invalid OpenAI API key in the environment configuration.

### 3. HIGH: All Court Scrapers Blocked

Every court website blocks the scraper:
- **SCP:** 403 Forbidden (NADRA firewall)
- **LHC:** Connection timeout
- **SHC/PHC:** No response
- **BHC:** Requires Playwright (not installed in container)
- **IHC/CommonLII:** Return 0 results

**Fix:** Court scrapers need browser automation (Playwright) with proper User-Agent headers, or switch to official court APIs if available.

### 4. HIGH: Playwright Not Installed in Container

Multiple scrapers that need JS rendering fail:
- `geo_news`: Falls back to RSS (partial data)
- `bhc`: Complete failure

**Fix:** Add Playwright + Chromium to the Docker image: `RUN pip install playwright && playwright install chromium`

### 5. MEDIUM: Police Websites Blocking Scrapers

- **Punjab Police:** Connection timeout
- **Sindh Police:** 403 Forbidden (WAF)

**Fix:** Needs proxy rotation or manual data collection approach.

### 6. LOW: UNODC Page Migrated

The `glo-act/publications.html` page returns 404. UNODC has restructured their website.

**Fix:** Update UNODC scraper URLs to match current site structure.

---

## Recommendations (Priority Order)

1. **Add DB insert for non-news scrapers** — This is the #1 reason data isn't growing. WorldBank (501 records), UNHCR (166), StateOfChildren (66), KPCPWC (16), SSDO (15) are all producing data that gets discarded.

2. **Replace the OpenAI API key** — Without this, no AI-based incident extraction works. The keyword filter catches some cases but misses nuanced articles.

3. **Install Playwright in Docker** — Enables JS-rendered site scraping (BHC, Geo News full scraping).

4. **Fix court scraper access** — Consider using CommonLII API or PakistanLawSite as alternative data sources for court judgments.

5. **Update UNODC and DOL scraper URLs** — Both source sites have changed their URL structures.

6. **Add monitoring** — Set up alerts for when scrapers return 0 records for 3+ consecutive runs.

---

## Data Flow Diagram (Current State)

```
SCRAPER EXECUTION
    │
    ├── save_raw() → data/raw/<name>/<timestamp>.json  [ALL scrapers]
    │
    └── Celery Task
         │
         ├── News scrapers (6) ─── _save_news_articles() ──→ news_articles table ✅
         │                              │
         │                              └── _enqueue_ai_processing()
         │                                       │
         │                                       └── process_article_ai() ──→ incidents table
         │                                                                     (BLOCKED: OpenAI 401)
         │
         └── All other scrapers (17) ── _update_data_source() ──→ data_sources table (registry only)
                                                                    ❌ ACTUAL DATA DISCARDED
```
