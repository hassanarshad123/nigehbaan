"""Run a single scraper and collect sample data.

Usage: python run_scraper.py <scraper_name>
Example: python run_scraper.py worldbank_api
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

SCRAPERS = {
    # International APIs (safest to test first — public APIs)
    "worldbank_api": ("data.scrapers.international.worldbank_api", "WorldBankAPIScraper"),
    "tip_report": ("data.scrapers.international.tip_report", "TIPReportScraper"),
    "unhcr_api": ("data.scrapers.international.unhcr_api", "UNHCRAPIScraper"),
    "unodc": ("data.scrapers.international.unodc", "UNODCScraper"),
    "dol_child_labor": ("data.scrapers.international.dol_child_labor", "DOLChildLaborScraper"),
    # News scrapers
    "dawn": ("data.scrapers.news.dawn_scraper", "DawnScraper"),
    "tribune": ("data.scrapers.news.tribune_scraper", "TribuneScraper"),
    "the_news": ("data.scrapers.news.the_news_scraper", "TheNewsScraper"),
    "ary_news": ("data.scrapers.news.ary_scraper", "ARYScraper"),
    "geo_news": ("data.scrapers.news.geo_scraper", "GeoScraper"),
    "rss_monitor": ("data.scrapers.news.rss_monitor", "RSSMonitor"),
    # Government scrapers
    "stateofchildren": ("data.scrapers.government.stateofchildren", "StateOfChildrenScraper"),
    "punjab_police": ("data.scrapers.government.punjab_police", "PunjabPoliceScraper"),
    "sindh_police": ("data.scrapers.government.sindh_police", "SindhPoliceScraper"),
    "kpcpwc": ("data.scrapers.government.kpcpwc", "KPCPWCScraper"),
    "ssdo_checker": ("data.scrapers.government.ssdo_checker", "SSDOChecker"),
    "mohr_checker": ("data.scrapers.government.mohr_checker", "MoHRChecker"),
    # Court scrapers
    "scp": ("data.scrapers.courts.scp", "SCPScraper"),
    "lhc": ("data.scrapers.courts.lhc", "LHCScraper"),
    "shc": ("data.scrapers.courts.shc", "SHCScraper"),
    "phc": ("data.scrapers.courts.phc", "PHCScraper"),
    "bhc": ("data.scrapers.courts.bhc", "BHCScraper"),
    "ihc": ("data.scrapers.courts.ihc", "IHCScraper"),
    "commonlii": ("data.scrapers.courts.commonlii", "CommonLIIScraper"),
}


async def run_one(name: str) -> None:
    module_path, class_name = SCRAPERS[name]
    mod = __import__(module_path, fromlist=[class_name])
    cls = getattr(mod, class_name)
    scraper = cls()
    print(f"\n{'='*60}")
    print(f"  RUNNING: {name} ({class_name})")
    print(f"  URL: {scraper.source_url}")
    print(f"{'='*60}\n")
    results = await scraper.run()
    print(f"\n--- {name} RESULTS ---")
    print(f"  Records: {len(results)}")
    if results:
        print(f"  Sample keys: {list(results[0].keys())}")
        raw_dir = Path("data/raw") / scraper.name
        print(f"  Saved to: {raw_dir}/")
    print()


async def main():
    if len(sys.argv) < 2:
        print("Available scrapers:")
        for k in SCRAPERS:
            print(f"  {k}")
        print("\nUsage: python run_scraper.py <name>")
        print("       python run_scraper.py ALL")
        return

    name = sys.argv[1]
    if name == "ALL":
        for scraper_name in SCRAPERS:
            try:
                await run_one(scraper_name)
            except Exception as e:
                print(f"  ERROR: {scraper_name} failed: {e}")
    elif name in SCRAPERS:
        await run_one(name)
    else:
        print(f"Unknown scraper: {name}")
        print(f"Available: {', '.join(SCRAPERS.keys())}")


if __name__ == "__main__":
    asyncio.run(main())
