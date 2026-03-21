"""Scrapy settings for Nigehbaan court judgment crawling."""

BOT_NAME = "nigehbaan"

SPIDER_MODULES = ["nigehbaan.spiders"]
NEWSPIDER_MODULE = "nigehbaan.spiders"

# Obey robots.txt
ROBOTSTXT_OBEY = False

# Rate limiting
CONCURRENT_REQUESTS = 5
DOWNLOAD_DELAY = 2.0
CONCURRENT_REQUESTS_PER_DOMAIN = 3

# User-Agent rotation
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# Retry
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Timeouts
DOWNLOAD_TIMEOUT = 60

# Pipelines
ITEM_PIPELINES = {
    "nigehbaan.pipelines.CourtJudgmentPipeline": 300,
}

# Logging
LOG_LEVEL = "INFO"

# Request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
