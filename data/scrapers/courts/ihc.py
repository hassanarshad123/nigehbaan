"""Islamabad High Court (IHC) scraper.

Scrapes the Islamabad High Court Management Information System
for trafficking and child abuse cases. IHC uses an ASP.NET web
application with ViewState-based form submissions.

Strategy:
    1. GET the search page to obtain __VIEWSTATE token
    2. POST search form with ViewState and search parameters
    3. Parse result HTML tables
    4. Handle ASP.NET postback pagination
    5. Download judgment PDFs from result links

URL: https://mis.ihc.gov.pk/frmCseSrch
Tool: Requests with ViewState handling (ASP.NET form)
Schedule: Weekly (0 3 * * 6)
Priority: P1 — Covers Islamabad Capital Territory
"""

import re
from typing import Any
from urllib.parse import urljoin

import logging

from bs4 import BeautifulSoup

from data.scrapers.courts.base_court_scraper import BaseCourtScraper

logger = logging.getLogger(__name__)

# ASP.NET hidden fields required for ViewState round-tripping
VIEWSTATE_FIELDS: list[str] = [
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__EVENTVALIDATION",
    "__VIEWSTATEENCRYPTED",
]


class IHCScraper(BaseCourtScraper):
    """Scraper for Islamabad High Court MIS portal.

    IHC uses an ASP.NET web application that requires ViewState
    token management for form submissions. Each search request
    must include the correct __VIEWSTATE, __VIEWSTATEGENERATOR,
    and __EVENTVALIDATION tokens from the previous response.

    Attributes:
        name: Scraper identifier.
        court_name: Full court name.
        source_url: IHC MIS case search URL.
        schedule: Weekly on Saturdays.
    """

    name: str = "ihc"
    court_name: str = "Islamabad High Court"
    source_url: str = "https://mis.ihc.gov.pk/frmCseSrch"
    schedule: str = "0 3 * * 6"
    priority: str = "P1"
    request_timeout: float = 60.0

    async def get_viewstate(self) -> dict[str, str]:
        """Fetch the IHC search page and extract ASP.NET tokens.

        ASP.NET forms require __VIEWSTATE, __VIEWSTATEGENERATOR,
        and __EVENTVALIDATION tokens to be submitted with each
        POST request. This method GETs the page and parses them.

        Returns:
            Dictionary with ASP.NET hidden form field values.
        """
        response = await self.fetch(self.source_url, method="GET")
        soup = BeautifulSoup(response.text, "html.parser")

        tokens: dict[str, str] = {}
        for field_name in VIEWSTATE_FIELDS:
            hidden = soup.find("input", attrs={"name": field_name})
            if hidden and hidden.get("value") is not None:
                tokens[field_name] = hidden["value"]

        # Also grab any additional hidden fields (e.g. __PREVIOUSPAGE)
        for inp in soup.find_all("input", attrs={"type": "hidden"}):
            name = inp.get("name", "")
            if name and name.startswith("__") and name not in tokens:
                tokens[name] = inp.get("value", "")

        if not tokens.get("__VIEWSTATE"):
            logger.warning(
                "[%s] Could not extract __VIEWSTATE from %s",
                self.name, self.source_url,
            )

        return tokens

    async def submit_search(
        self,
        viewstate: dict[str, str],
        year: int,
        case_type: str | None = None,
    ) -> str:
        """Submit search form with ASP.NET ViewState tokens.

        Constructs the POST body with ViewState tokens and search
        parameters, then submits to the IHC form handler.

        Args:
            viewstate: Dict of ASP.NET hidden field values.
            year: Year to search for cases.
            case_type: Optional case type filter.

        Returns:
            HTML response body containing search results.
        """
        form_data: dict[str, str] = {}
        # Include all ViewState tokens
        form_data.update(viewstate)

        # Add search parameters using common ASP.NET control names
        form_data["ctl00$ContentPlaceHolder1$txtYear"] = str(year)
        form_data["ctl00$ContentPlaceHolder1$ddlCaseType"] = case_type or "Criminal"
        form_data["ctl00$ContentPlaceHolder1$btnSearch"] = "Search"
        form_data["ctl00$ContentPlaceHolder1$txtKeyword"] = "trafficking 370 366-A 377"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = await self.fetch(
            self.source_url,
            method="POST",
            data=form_data,
            headers=headers,
        )
        return response.text

    async def handle_pagination(
        self, viewstate: dict[str, str], page: int
    ) -> str:
        """Navigate to a specific results page via ASP.NET postback.

        ASP.NET pagination uses __doPostBack JavaScript calls
        which are simulated as POST requests with updated
        __EVENTTARGET and __EVENTARGUMENT fields.

        Args:
            viewstate: Current page's ViewState tokens.
            page: Target page number.

        Returns:
            HTML response body for the requested page.
        """
        form_data: dict[str, str] = {}
        form_data.update(viewstate)

        # ASP.NET postback for GridView pagination
        form_data["__EVENTTARGET"] = "ctl00$ContentPlaceHolder1$gvResults"
        form_data["__EVENTARGUMENT"] = f"Page${page}"

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = await self.fetch(
            self.source_url,
            method="POST",
            data=form_data,
            headers=headers,
        )
        return response.text

    def _extract_viewstate_from_html(self, html: str) -> dict[str, str]:
        """Extract updated ViewState tokens from an HTML response.

        After each POST, ASP.NET returns updated tokens that must
        be used for the next request (including pagination).

        Args:
            html: HTML response text.

        Returns:
            Updated dictionary of ViewState tokens.
        """
        soup = BeautifulSoup(html, "html.parser")
        tokens: dict[str, str] = {}
        for field_name in VIEWSTATE_FIELDS:
            hidden = soup.find("input", attrs={"name": field_name})
            if hidden and hidden.get("value") is not None:
                tokens[field_name] = hidden["value"]

        for inp in soup.find_all("input", attrs={"type": "hidden"}):
            name = inp.get("name", "")
            if name and name.startswith("__") and name not in tokens:
                tokens[name] = inp.get("value", "")

        return tokens

    def _parse_results_table(self, html: str) -> list[dict[str, Any]]:
        """Parse IHC search results HTML table.

        Args:
            html: HTML response text containing the results GridView.

        Returns:
            List of case reference dicts.
        """
        soup = BeautifulSoup(html, "html.parser")
        cases: list[dict[str, Any]] = []

        # ASP.NET GridView renders as a standard HTML table
        table = (
            soup.find("table", id=re.compile(r"gvResults", re.I))
            or soup.find("table", class_="table")
            or soup.find("table")
        )
        if not table:
            return cases

        rows = table.find_all("tr")
        for row in rows[1:]:
            # Skip pager rows (typically contain nested tables)
            if row.find("table"):
                continue
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            pdf_url = ""
            link_tag = row.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                pdf_url = urljoin(self.source_url, href)

            case_number = cells[0].get_text(strip=True)
            parties = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            date_decided = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            result = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            judge = cells[4].get_text(strip=True) if len(cells) > 4 else ""

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
                "judge": judge,
                "pdf_url": pdf_url,
                "court": self.court_name,
            })

        return cases

    def _get_total_pages(self, html: str) -> int:
        """Determine the total number of result pages from the pager row.

        Args:
            html: HTML response text.

        Returns:
            Total number of pages (1 if no pagination).
        """
        soup = BeautifulSoup(html, "html.parser")

        # ASP.NET GridView pager is often the last row with links
        table = (
            soup.find("table", id=re.compile(r"gvResults", re.I))
            or soup.find("table", class_="table")
            or soup.find("table")
        )
        if not table:
            return 1

        # Look for pager row: a row containing a nested table with page links
        pager_row = None
        for row in table.find_all("tr"):
            if row.find("table"):
                pager_row = row
                break

        if not pager_row:
            return 1

        # Count page links/numbers in the pager
        page_links = pager_row.find_all("a")
        page_spans = pager_row.find_all("span")

        max_page = 1
        for el in page_links + page_spans:
            text = el.get_text(strip=True)
            if text.isdigit():
                page_num = int(text)
                if page_num > max_page:
                    max_page = page_num

        return max_page

    async def search_cases(
        self, year: int, case_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Search IHC MIS for cases with ViewState management.

        Handles the full ASP.NET form submission cycle:
        GET page -> extract tokens -> POST search -> parse results
        -> handle pagination.

        Searches multiple case types: Criminal, Criminal Appeal,
        and Criminal Revision for broader coverage.

        Args:
            year: Year to search.
            case_type: Optional case type filter.

        Returns:
            List of case reference dicts from search results.
        """
        all_cases: list[dict[str, Any]] = []
        seen_case_numbers: set[str] = set()

        # Search multiple case types for broader coverage
        case_types_to_search: list[str] = (
            [case_type] if case_type
            else ["Criminal", "Criminal Appeal", "Criminal Revision"]
        )

        for ct in case_types_to_search:
            try:
                # Step 1: Get initial ViewState tokens (fresh for each case type)
                viewstate = await self.get_viewstate()
                if not viewstate:
                    logger.warning("[%s] Failed to get ViewState for year %d, type %s", self.name, year, ct)
                    continue

                # Step 2: Submit search form
                result_html = await self.submit_search(viewstate, year, ct)

                # Step 3: Parse first page of results
                first_page_cases = self._parse_results_table(result_html)

                # Step 4: Determine total pages and paginate
                total_pages = self._get_total_pages(result_html)
                current_viewstate = self._extract_viewstate_from_html(result_html)

                page_cases_all = list(first_page_cases)
                for page_num in range(2, total_pages + 1):
                    try:
                        if not current_viewstate:
                            break
                        page_html = await self.handle_pagination(
                            current_viewstate, page_num
                        )
                        page_cases = self._parse_results_table(page_html)
                        if not page_cases:
                            break
                        page_cases_all.extend(page_cases)
                        # Update ViewState for next page
                        current_viewstate = self._extract_viewstate_from_html(page_html)
                    except Exception as exc:
                        logger.warning(
                            "[%s] Error on page %d for year %d type %s: %s",
                            self.name, page_num, year, ct, exc,
                        )
                        break

                # Deduplicate by case_number across case types
                for case in page_cases_all:
                    cn = case.get("case_number", "")
                    if cn not in seen_case_numbers:
                        seen_case_numbers.add(cn)
                        all_cases.append(case)

            except Exception as exc:
                logger.error(
                    "[%s] Error searching year %d type %s: %s",
                    self.name, year, ct, exc,
                )

        logger.info(
            "[%s] Found %d total cases for year %d",
            self.name, len(all_cases), year,
        )
        return all_cases

    async def download_judgment(
        self, case_ref: dict[str, Any]
    ) -> bytes | None:
        """Download IHC judgment PDF.

        IHC PDFs may require session cookies from the search.
        Delegates to the base class which uses the shared httpx
        client that retains cookies across requests.

        Args:
            case_ref: Case reference with download link.

        Returns:
            Raw PDF bytes or None.
        """
        return await super().download_judgment(case_ref)

    async def scrape(self) -> list[dict[str, Any]]:
        """Execute the IHC scraping pipeline.

        Returns:
            List of case records with metadata.
        """
        logger.info("[%s] Starting IHC scrape", self.name)
        results = await self.scrape_year_range()
        logger.info("[%s] IHC scrape complete: %d records", self.name, len(results))
        return results

    def validate(self, record: dict[str, Any]) -> bool:
        """Validate an IHC case record.

        Args:
            record: A case record dictionary.

        Returns:
            True if required fields are present.
        """
        required_fields = ["case_number", "year", "court"]
        return all(record.get(f) for f in required_fields)
