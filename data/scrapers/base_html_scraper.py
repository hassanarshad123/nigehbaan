"""Base HTML table scraper for Nigehbaan data pipeline.

Extends BaseScraper with HTML-specific capabilities: table extraction,
link extraction, and province name normalization for Pakistan.
"""

import re

import logging

from data.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Province name normalization map
_PROVINCE_MAP: dict[str, str] = {
    "punjab": "Punjab",
    "sindh": "Sindh",
    "kp": "Khyber Pakhtunkhwa",
    "kpk": "Khyber Pakhtunkhwa",
    "khyber pakhtunkhwa": "Khyber Pakhtunkhwa",
    "nwfp": "Khyber Pakhtunkhwa",
    "balochistan": "Balochistan",
    "baluchistan": "Balochistan",
    "ict": "Islamabad Capital Territory",
    "islamabad": "Islamabad Capital Territory",
    "ajk": "Azad Jammu & Kashmir",
    "azad kashmir": "Azad Jammu & Kashmir",
    "azad jammu and kashmir": "Azad Jammu & Kashmir",
    "gb": "Gilgit-Baltistan",
    "gilgit baltistan": "Gilgit-Baltistan",
    "gilgit-baltistan": "Gilgit-Baltistan",
    "fata": "FATA",
}


class BaseHTMLTableScraper(BaseScraper):
    """Base class for scrapers that extract data from HTML tables.

    Provides HTML table extraction, link discovery by pattern,
    and Pakistan province name normalization.
    """

    def extract_tables(self, html: str) -> list[list[dict[str, str]]]:
        """Extract all HTML tables as list-of-dicts.

        Args:
            html: Raw HTML content.

        Returns:
            List of tables, each a list of row-dicts keyed by header names.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        tables: list[list[dict[str, str]]] = []

        for table_el in soup.find_all("table"):
            rows = table_el.find_all("tr")
            if len(rows) < 2:
                continue

            # Extract headers from first row
            header_row = rows[0]
            headers = [
                th.get_text(strip=True)
                for th in header_row.find_all(["th", "td"])
            ]
            if not headers:
                continue

            # Extract data rows
            table_data: list[dict[str, str]] = []
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) != len(headers):
                    # Pad or truncate to match headers
                    values = [c.get_text(strip=True) for c in cells]
                    while len(values) < len(headers):
                        values.append("")
                    values = values[: len(headers)]
                else:
                    values = [c.get_text(strip=True) for c in cells]

                row_dict = dict(zip(headers, values))
                if any(v for v in row_dict.values()):
                    table_data.append(row_dict)

            if table_data:
                tables.append(table_data)

        return tables

    def extract_links(self, html: str, pattern: str) -> list[dict[str, str]]:
        """Extract links matching a regex pattern.

        Args:
            html: Raw HTML content.
            pattern: Regex pattern to match against href values.

        Returns:
            List of dicts with 'url', 'text', 'href' keys.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links: list[dict[str, str]] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if re.search(pattern, href, re.IGNORECASE):
                links.append({
                    "url": href,
                    "text": a_tag.get_text(strip=True),
                    "href": href,
                })

        return links

    @staticmethod
    def normalize_province(text: str) -> str:
        """Normalize a Pakistan province name to its standard form.

        Args:
            text: Raw province name string.

        Returns:
            Standardized province name, or original if not recognized.
        """
        if not text:
            return text
        key = text.strip().lower()
        return _PROVINCE_MAP.get(key, text.strip())
