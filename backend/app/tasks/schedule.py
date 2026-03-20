"""Celery Beat schedule for all scraping and processing tasks."""

from celery.schedules import crontab

from app.tasks.celery_app import celery_app

# ---------------------------------------------------------------------------
# Schedule configuration
# ---------------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    # ── News (individual scrapers) ─────────────────────────────────
    "news_rss": {
        "task": "app.tasks.scraping_tasks.scrape_news_rss",
        "schedule": crontab(minute=0, hour="*/6"),  # every 6 hours
        "options": {"queue": "scraping"},
    },
    "news_dawn": {
        "task": "app.tasks.scraping_tasks.scrape_news_dawn",
        "schedule": crontab(minute=15, hour="*/6"),
        "options": {"queue": "scraping"},
    },
    "news_tribune": {
        "task": "app.tasks.scraping_tasks.scrape_news_tribune",
        "schedule": crontab(minute=30, hour="*/6"),
        "options": {"queue": "scraping"},
    },
    "news_the_news": {
        "task": "app.tasks.scraping_tasks.scrape_news_the_news",
        "schedule": crontab(minute=45, hour="*/6"),
        "options": {"queue": "scraping"},
    },
    "news_ary": {
        "task": "app.tasks.scraping_tasks.scrape_news_ary",
        "schedule": crontab(minute=0, hour="1,7,13,19"),
        "options": {"queue": "scraping"},
    },
    "news_geo": {
        "task": "app.tasks.scraping_tasks.scrape_news_geo",
        "schedule": crontab(minute=15, hour="1,7,13,19"),
        "options": {"queue": "scraping"},
    },
    "news_js": {
        "task": "app.tasks.scraping_tasks.scrape_news_js",
        "schedule": crontab(minute=30, hour=2),  # daily at 02:30
        "options": {"queue": "scraping"},
    },
    # ── Reports ───────────────────────────────────────────────────────
    "sahil_checker": {
        "task": "app.tasks.scraping_tasks.check_sahil_updates",
        "schedule": crontab(minute=0, hour=3, day_of_month=1),  # monthly
        "options": {"queue": "scraping"},
    },
    "tip_report": {
        "task": "app.tasks.scraping_tasks.scrape_tip_report",
        "schedule": crontab(minute=0, hour=4, day_of_month=1, month_of_year=7),  # annually (July)
        "options": {"queue": "scraping"},
    },
    "ctdc_updater": {
        "task": "app.tasks.scraping_tasks.update_ctdc",
        "schedule": crontab(minute=0, hour=5, day_of_month=1, month_of_year="1,4,7,10"),  # quarterly
        "options": {"queue": "scraping"},
    },
    # ── Courts ────────────────────────────────────────────────────────
    "court_scp": {
        "task": "app.tasks.scraping_tasks.scrape_courts",
        "schedule": crontab(minute=0, hour=1, day_of_week=0),  # weekly (Sunday)
        "args": ("scp",),
        "options": {"queue": "scraping"},
    },
    "court_lhc": {
        "task": "app.tasks.scraping_tasks.scrape_courts",
        "schedule": crontab(minute=15, hour=1, day_of_week=0),
        "args": ("lhc",),
        "options": {"queue": "scraping"},
    },
    "court_shc": {
        "task": "app.tasks.scraping_tasks.scrape_courts",
        "schedule": crontab(minute=30, hour=1, day_of_week=0),
        "args": ("shc",),
        "options": {"queue": "scraping"},
    },
    "court_phc": {
        "task": "app.tasks.scraping_tasks.scrape_courts",
        "schedule": crontab(minute=45, hour=1, day_of_week=0),
        "args": ("phc",),
        "options": {"queue": "scraping"},
    },
    "court_bhc": {
        "task": "app.tasks.scraping_tasks.scrape_courts",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),
        "args": ("bhc",),
        "options": {"queue": "scraping"},
    },
    "court_ihc": {
        "task": "app.tasks.scraping_tasks.scrape_courts",
        "schedule": crontab(minute=15, hour=2, day_of_week=0),
        "args": ("ihc",),
        "options": {"queue": "scraping"},
    },
    # ── Police & other gov ────────────────────────────────────────────
    "police_punjab": {
        "task": "app.tasks.scraping_tasks.scrape_police_data",
        "schedule": crontab(minute=0, hour=4, day_of_month=15),  # monthly (15th)
        "args": ("punjab",),
        "options": {"queue": "scraping"},
    },
    "police_sindh": {
        "task": "app.tasks.scraping_tasks.scrape_police_data",
        "schedule": crontab(minute=30, hour=4, day_of_month=15),
        "args": ("sindh",),
        "options": {"queue": "scraping"},
    },
    "police_kp": {
        "task": "app.tasks.scraping_tasks.scrape_police_data",
        "schedule": crontab(minute=0, hour=5, day_of_month=15),
        "args": ("kp",),
        "options": {"queue": "scraping"},
    },
    "police_balochistan": {
        "task": "app.tasks.scraping_tasks.scrape_police_data",
        "schedule": crontab(minute=30, hour=5, day_of_month=15),
        "args": ("balochistan",),
        "options": {"queue": "scraping"},
    },
    "stateofchildren": {
        "task": "app.tasks.scraping_tasks.scrape_stateofchildren",
        "schedule": crontab(minute=0, hour=6, day_of_month=1),  # monthly
        "options": {"queue": "scraping"},
    },
    # ── International data APIs ───────────────────────────────────────
    "worldbank_api": {
        "task": "app.tasks.scraping_tasks.scrape_worldbank_api",
        "schedule": crontab(minute=0, hour=7, day_of_month=1, month_of_year="1,4,7,10"),
        "options": {"queue": "scraping"},
    },
    "unhcr_api": {
        "task": "app.tasks.scraping_tasks.scrape_unhcr_api",
        "schedule": crontab(minute=30, hour=7, day_of_month=1, month_of_year="1,4,7,10"),
        "options": {"queue": "scraping"},
    },
    # ── Phase 1: CSA scrapers ─────────────────────────────────────────
    "sahil": {
        "task": "app.tasks.scraping_tasks.scrape_sahil",
        "schedule": crontab(minute=0, hour=3, day_of_month=1, month_of_year=1),  # annually Jan
        "options": {"queue": "scraping"},
    },
    "ecpat": {
        "task": "app.tasks.scraping_tasks.scrape_ecpat",
        "schedule": crontab(minute=30, hour=3, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    "pahchaan": {
        "task": "app.tasks.scraping_tasks.scrape_pahchaan",
        "schedule": crontab(minute=0, hour=4, day_of_month=1, month_of_year="1,4,7,10"),  # quarterly
        "options": {"queue": "scraping"},
    },
    "unicef_pakistan": {
        "task": "app.tasks.scraping_tasks.scrape_unicef_pakistan",
        "schedule": crontab(minute=30, hour=4, day_of_month=1, month_of_year="1,4,7,10"),  # quarterly
        "options": {"queue": "scraping"},
    },
    "ncrc": {
        "task": "app.tasks.scraping_tasks.scrape_ncrc",
        "schedule": crontab(minute=0, hour=5, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    "cpwb_punjab": {
        "task": "app.tasks.scraping_tasks.scrape_cpwb_punjab",
        "schedule": crontab(minute=30, hour=5, day_of_month=1, month_of_year="1,4,7,10"),  # quarterly
        "options": {"queue": "scraping"},
    },
    # ── Phase 2: Online Exploitation scrapers ──────────────────────────
    "ncmec": {
        "task": "app.tasks.scraping_tasks.scrape_ncmec",
        "schedule": crontab(minute=0, hour=6, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    "iwf_reports": {
        "task": "app.tasks.scraping_tasks.scrape_iwf_reports",
        "schedule": crontab(minute=30, hour=6, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    "meta_transparency": {
        "task": "app.tasks.scraping_tasks.scrape_meta_transparency",
        "schedule": crontab(minute=0, hour=7, day_of_month=1, month_of_year="1,7"),  # semi-annual
        "options": {"queue": "scraping"},
    },
    "google_transparency": {
        "task": "app.tasks.scraping_tasks.scrape_google_transparency",
        "schedule": crontab(minute=30, hour=7, day_of_month=1, month_of_year="1,7"),  # semi-annual
        "options": {"queue": "scraping"},
    },
    "drf_newsletters": {
        "task": "app.tasks.scraping_tasks.scrape_drf_newsletters",
        "schedule": crontab(minute=0, hour=8, day_of_month=1),  # monthly
        "options": {"queue": "scraping"},
    },
    "weprotect_gta": {
        "task": "app.tasks.scraping_tasks.scrape_weprotect_gta",
        "schedule": crontab(minute=30, hour=8, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    "bytes_for_all": {
        "task": "app.tasks.scraping_tasks.scrape_bytes_for_all",
        "schedule": crontab(minute=0, hour=9, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    # ── Phase 3: Child Labor scrapers ──────────────────────────────────
    "ilostat_api": {
        "task": "app.tasks.scraping_tasks.scrape_ilostat_api",
        "schedule": crontab(minute=0, hour=10, day_of_month=1, month_of_year="1,4,7,10"),  # quarterly
        "options": {"queue": "scraping"},
    },
    "dol_annual_report": {
        "task": "app.tasks.scraping_tasks.scrape_dol_annual_report",
        "schedule": crontab(minute=30, hour=10, day_of_month=1, month_of_year=10),  # annually Oct
        "options": {"queue": "scraping"},
    },
    "dol_tvpra": {
        "task": "app.tasks.scraping_tasks.scrape_dol_tvpra",
        "schedule": crontab(minute=0, hour=11, day_of_month=1, month_of_year=10),  # annually Oct
        "options": {"queue": "scraping"},
    },
    "labour_surveys": {
        "task": "app.tasks.scraping_tasks.scrape_labour_surveys",
        "schedule": crontab(minute=30, hour=11, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    "zenodo_kilns": {
        "task": "app.tasks.scraping_tasks.scrape_zenodo_kilns",
        "schedule": crontab(minute=0, hour=12, day_of_month=1, month_of_year=1),  # annually (one-time)
        "options": {"queue": "scraping"},
    },
    "bllf": {
        "task": "app.tasks.scraping_tasks.scrape_bllf",
        "schedule": crontab(minute=30, hour=12, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    "brick_kiln_dashboard": {
        "task": "app.tasks.scraping_tasks.scrape_brick_kiln_dashboard",
        "schedule": crontab(minute=0, hour=13, day_of_month=1, month_of_year="1,4,7,10"),  # quarterly
        "options": {"queue": "scraping"},
    },
    # ── Phase 4: Cross-border scrapers ─────────────────────────────────
    "ctdc_dataset": {
        "task": "app.tasks.scraping_tasks.scrape_ctdc_dataset",
        "schedule": crontab(minute=0, hour=14, day_of_month=1, month_of_year="1,4,7,10"),  # quarterly
        "options": {"queue": "scraping"},
    },
    "brookings_bride": {
        "task": "app.tasks.scraping_tasks.scrape_brookings_bride",
        "schedule": crontab(minute=30, hour=14, day_of_month=1, month_of_year=1),  # annually
        "options": {"queue": "scraping"},
    },
    # ── Phase 5: Urdu news scrapers (offset by 2h to avoid t2.small contention)
    "jang_urdu": {
        "task": "app.tasks.scraping_tasks.scrape_news_jang_urdu",
        "schedule": crontab(minute=0, hour="2,8,14,20"),
        "options": {"queue": "scraping"},
    },
    "express_urdu": {
        "task": "app.tasks.scraping_tasks.scrape_news_express_urdu",
        "schedule": crontab(minute=15, hour="2,8,14,20"),
        "options": {"queue": "scraping"},
    },
    "bbc_urdu": {
        "task": "app.tasks.scraping_tasks.scrape_news_bbc_urdu",
        "schedule": crontab(minute=30, hour="2,8,14,20"),
        "options": {"queue": "scraping"},
    },
    "geo_urdu": {
        "task": "app.tasks.scraping_tasks.scrape_news_geo_urdu",
        "schedule": crontab(minute=45, hour="2,8,14,20"),
        "options": {"queue": "scraping"},
    },
    # ── External data imports ────────────────────────────────────────
    "import_external_judgments": {
        "task": "app.tasks.import_tasks.import_external_judgments",
        "schedule": crontab(minute=0, hour=3, day_of_week=0),  # Sunday 03:00
        "options": {"queue": "processing"},
    },
    # ── Processing (periodic) ────────────────────────────────────────
    "geocode_incidents": {
        "task": "app.tasks.processing_tasks.geocode_incidents",
        "schedule": crontab(minute=0, hour="*/4"),  # every 4 hours
        "options": {"queue": "processing"},
    },
    "risk_scores": {
        "task": "app.tasks.processing_tasks.calculate_risk_scores",
        "schedule": crontab(minute=0, hour=8, day_of_week=1),  # weekly (Monday)
        "options": {"queue": "processing"},
    },
    "vulnerability_indicators": {
        "task": "app.tasks.processing_tasks.update_vulnerability_indicators",
        "schedule": crontab(minute=0, hour=9, day_of_month=1),  # monthly
        "options": {"queue": "processing"},
    },
}
