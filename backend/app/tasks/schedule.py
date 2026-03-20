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
