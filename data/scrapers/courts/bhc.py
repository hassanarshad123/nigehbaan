"""Balochistan High Court (BHC) scraper.

Scrapes the Balochistan High Court case status portal. BHC uses
a Single Page Application (SPA) for its portal, requiring
Playwright for headless browser automation.

Strategy:
    1. Launch Playwright headless browser
    2. Navigate to the BHC case status portal
    3. Fill and submit the search form via DOM interaction
    4. Wait for AJAX results to load
    5. Extract case listings from rendered DOM
    6. Download judgment PDFs where available

URL: https://portal.bhc.gov.pk/case-status/
Tool: Playwright (SPA requires JS rendering)
Schedule: Weekly (0 3 * * 5)
Priority: P1 — Balochistan has underreported trafficking
"""

import re
from typing import Any

import logging

from data.scrapers.courts.base_court_scraper import (
    BaseCourtScraper,
    PPC_SECTIONS_OF_INTEREST,
)

logger = logging.getLogger(__name__)

# Attempt to import Playwright; it is an optional heavy dependency
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(
        "Playwright is not installed. BHC scraper will not function. "
        "Install with: pip install playwright && python -m playwright install chromium"
    )


class BHCScraper(BaseCourtScraper):
    """Scraper for Balochistan High Court case status portal.

    BHC uses a Single Page Application (SPA) that requires
    JavaScript rendering. This scraper uses Playwright for
    headless browser automation to interact with the portal.

    Note: Playwright adds overhead per page interaction (~3-5s).
    The SPA may have rate limiting or CAPTCHA protections.

    Attributes:
        name: Scraper identifier.
        court_name: Full court name.
        source_url: BHC case status portal URL.
        schedule: Weekly on Fridays.
    """

    name: str = "bhc"
    court_name: str = "Balochistan High Court"
    source_url: str = "https://portal.bhc.gov.pk/case-status/"
    schedule: str = "0 3 * * 5"
    priority: str = "P1"

    def __init__(self) -> None:
        super().__init__()
        self._playwright: Any = None
        self._browser: Any = None
        self._page: Any = None

    async def init_browser(self) -> None:
        """Initialize Playwright browser for BHC SPA interaction.

        Launches a headless Chromium instance with viewport and
        user-agent configured for the BHC portal.

        Raises:
            RuntimeError: If Playwright is not installed.
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright is required for BHC scraper but is not installed. "
                "Install with: pip install playwright && python -m playwright install chromium"
            )

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = await context.new_page()
        logger.info("[%s] Playwright browser initialized", self.name)

    async def close_browser(self) -> None:
        """Close Playwright browser and release resources."""
        try:
            if self._page:
                await self._page.close()
                self._page = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("[%s] Playwright browser closed", self.name)
        except Exception as exc:
            logger.warning("[%s] Error closing browser: %s", self.name, exc)

    def _parse_dom_results(self, html_content: str) -> list[dict[str, Any]]:
        """Parse rendered DOM content into case reference dicts.

        Args:
            html_content: HTML string from the rendered SPA page.

        Returns:
            List of case reference dicts.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")
        cases: list[dict[str, Any]] = []

        # Try table layout
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue

                pdf_url = ""
                link_tag = row.find("a", href=True)
                if link_tag:
                    href = link_tag["href"]
                    if href.startswith("/"):
                        pdf_url = f"https://portal.bhc.gov.pk{href}"
                    elif href.startswith("http"):
                        pdf_url = href
                    else:
                        pdf_url = f"{self.source_url}{href}"

                case_number = cells[0].get_text(strip=True)
                parties = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                date_decided = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                result = cells[3].get_text(strip=True) if len(cells) > 3 else ""

                year_val = ""
                if "/" in case_number:
                    parts = case_number.split("/")
                    year_val = parts[-1].strip()
                if not year_val and date_decided:
                    potential = date_decided[-4:]
                    if potential.isdigit():
                        year_val = potential

                cases.append({
                    "case_number": case_number,
                    "year": year_val,
                    "parties": parties,
                    "title": parties,
                    "date_decided": date_decided,
                    "result": result,
                    "pdf_url": pdf_url,
                    "court": self.court_name,
                })
            return cases

        # Fallback: card / list items rendered by SPA
        cards = soup.find_all("div", class_=re.compile(r"case|card|result", re.I))
        for card in cards:
            text = card.get_text(" ", strip=True)
            link = card.find("a", href=True)
            pdf_url = ""
            if link:
                href = link["href"]
                if href.startswith("/"):
                    pdf_url = f"https://portal.bhc.gov.pk{href}"
                elif href.startswith("http"):
                    pdf_url = href
                else:
                    pdf_url = f"{self.source_url}{href}"

            cn_match = re.search(r"([\w\s.-]+\d+/\d{4})", text)
            case_number = cn_match.group(1).strip() if cn_match else ""
            date_match = re.search(r"(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", text)
            date_decided = date_match.group(1) if date_match else ""

            year_val = ""
            if "/" in case_number:
                parts = case_number.split("/")
                year_val = parts[-1].strip()

            cases.append({
                "case_number": case_number,
                "year": year_val,
                "parties": text[:200],
                "title": text[:200],
                "description": text,
                "date_decided": date_decided,
                "pdf_url": pdf_url,
                "court": self.court_name,
            })

        return cases

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search BHC case status portal using Playwright.

        Navigates the SPA, fills the search form with year and
        PPC section criteria, submits, and waits for AJAX results
        to render before extracting case data from the DOM.

        Args:
            year: Year to search.
            case_type: Optional case type filter.

        Returns:
            List of case reference dicts from rendered results.
        """
        if not self._page:
            logger.error("[%s] Browser not initialized; call init_browser() first", self.name)
            return []

        all_cases: list[dict[str, Any]] = []

        for section in PPC_SECTIONS_OF_INTEREST:
            try:
                # Navigate to the case status page
                await self._page.goto(self.source_url, wait_until="networkidle")

                # Fill the search form fields
                # Try common selector patterns for year input
                year_selectors = [
                    'input[name="year"]',
                    'input[name="Year"]',
                    'select[name="year"]',
                    "#year",
                    "#txtYear",
                ]
                for sel in year_selectors:
                    el = await self._page.query_selector(sel)
                    if el:
                        tag_name = await el.evaluate("el => el.tagName.toLowerCase()")
                        if tag_name == "select":
                            await el.select_option(str(year))
                        else:
                            await el.fill(str(year))
                        break

                # Fill PPC section / case type field
                section_selectors = [
                    'input[name="section"]',
                    'input[name="ppc_section"]',
                    'input[name="keyword"]',
                    "#section",
                    "#txtSection",
                    "#txtKeyword",
                ]
                for sel in section_selectors:
                    el = await self._page.query_selector(sel)
                    if el:
                        await el.fill(section)
                        break

                # Set case type to Criminal if a selector exists
                type_selectors = [
                    'select[name="case_type"]',
                    'select[name="caseType"]',
                    "#caseType",
                    "#ddlCaseType",
                ]
                for sel in type_selectors:
                    el = await self._page.query_selector(sel)
                    if el:
                        try:
                            await el.select_option(label="Criminal")
                        except Exception:
                            try:
                                await el.select_option(value="Criminal")
                            except Exception:
                                pass
                        break

                # Click search button
                search_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    "#btnSearch",
                    "#searchBtn",
                    "button.btn-primary",
                ]
                for sel in search_selectors:
                    el = await self._page.query_selector(sel)
                    if el:
                        await el.click()
                        break

                # Wait for results to load
                try:
                    await self._page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    # Timeout waiting for network idle is acceptable
                    pass

                # Also wait a moment for SPA rendering
                await self._page.wait_for_timeout(2000)

                # Extract rendered HTML
                html_content = await self._page.content()
                page_cases = self._parse_dom_results(html_content)
                all_cases.extend(page_cases)

            except Exception as exc:
                logger.warning(
                    "[%s] Error searching section=%s year=%d: %s",
                    self.name, section, year, exc,
                )
                continue

        logger.info(
            "[%s] Found %d total cases for year %d",
            self.name, len(all_cases), year,
        )
        return all_cases

    async def download_judgment(
        self, case_ref: dict[str, Any]
    ) -> bytes | None:
        """Download BHC judgment PDF via browser automation.

        If a pdf_url is available, uses the standard HTTP download
        from the base class. Otherwise, attempts to trigger a
        download through the Playwright browser context.

        Args:
            case_ref: Case reference with case number.

        Returns:
            Raw PDF bytes or None.
        """
        pdf_url = case_ref.get("pdf_url")
        if not pdf_url:
            return None

        # Try standard HTTP download first
        try:
            return await self.fetch_bytes(pdf_url)
        except Exception:
            pass

        # Fall back to Playwright download if HTTP fails
        if not self._page:
            return None

        try:
            async with self._page.expect_download(timeout=30000) as download_info:
                await self._page.goto(pdf_url)
            download = await download_info.value
            path = await download.path()
            if path:
                import aiofiles
                try:
                    async with aiofiles.open(path, "rb") as f:
                        return await f.read()
                except ImportError:
                    # aiofiles not available; use sync read
                    from pathlib import Path
                    return Path(path).read_bytes()
        except Exception as exc:
            logger.warning(
                "[%s] Playwright download failed for %s: %s",
                self.name, case_ref.get("case_number", "?"), exc,
            )

        return None

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the BHC scraping pipeline with Playwright.

        Initializes browser, searches for cases, downloads
        judgments, and cleans up browser resources.

        Returns:
            List of case records with metadata.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error(
                "[%s] Playwright not available; skipping BHC scrape", self.name
            )
            return []

        logger.info("[%s] Starting BHC scrape", self.name)
        try:
            await self.init_browser()
            results = await self.scrape_year_range()
            logger.info("[%s] BHC scrape complete: %d records", self.name, len(results))
            return results
        except Exception as exc:
            logger.error("[%s] BHC scrape failed: %s", self.name, exc)
            return []
        finally:
            await self.close_browser()

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate a BHC case record.

        Args:
            record: A case record dictionary.

        Returns:
            True if required fields are present.
        """
        required_fields = ["case_number", "year", "court"]
        return all(record.get(f) for f in required_fields)
