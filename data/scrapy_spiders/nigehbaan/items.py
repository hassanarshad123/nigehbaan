"""Scrapy items matching Nigehbaan database models."""

import scrapy


class CourtJudgmentItem(scrapy.Item):
    """Maps to the court_judgments table."""

    court_name = scrapy.Field()
    court_bench = scrapy.Field()
    case_number = scrapy.Field()
    judgment_date = scrapy.Field()
    judge_names = scrapy.Field()
    appellant = scrapy.Field()
    respondent = scrapy.Field()
    ppc_sections = scrapy.Field()
    statutes = scrapy.Field()
    is_trafficking_related = scrapy.Field()
    trafficking_type = scrapy.Field()
    verdict = scrapy.Field()
    sentence = scrapy.Field()
    sentence_years = scrapy.Field()
    judgment_text = scrapy.Field()
    pdf_url = scrapy.Field()
    source_url = scrapy.Field()
    nlp_confidence = scrapy.Field()


class StatisticalReportItem(scrapy.Item):
    """Maps to the statistical_reports table."""

    source_name = scrapy.Field()
    report_year = scrapy.Field()
    report_title = scrapy.Field()
    indicator = scrapy.Field()
    value = scrapy.Field()
    unit = scrapy.Field()
    geographic_scope = scrapy.Field()
    district_pcode = scrapy.Field()
    extraction_method = scrapy.Field()
    extraction_confidence = scrapy.Field()
    raw_table_data = scrapy.Field()
