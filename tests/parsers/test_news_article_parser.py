"""Tests for the news article NER parser."""

import pytest

from data.parsers.news_article_parser import NewsArticleParser, CRIME_KEYWORDS


class TestNewsArticleParser:
    def test_classify_crime_type_trafficking(self):
        parser = NewsArticleParser()
        crime_type, confidence = parser.classify_crime_type(
            "Police busted a child trafficking ring in Lahore"
        )
        assert crime_type == "child_trafficking"
        assert confidence > 0

    def test_classify_crime_type_kidnapping(self):
        parser = NewsArticleParser()
        crime_type, confidence = parser.classify_crime_type(
            "Three children kidnapped from school under section 366-A PPC"
        )
        assert crime_type == "kidnapping"

    def test_classify_crime_type_bonded_labor(self):
        parser = NewsArticleParser()
        crime_type, confidence = parser.classify_crime_type(
            "Children rescued from brick kiln, bonded labor conditions found"
        )
        assert crime_type == "bonded_labor"

    def test_classify_crime_type_unknown(self):
        parser = NewsArticleParser()
        crime_type, confidence = parser.classify_crime_type(
            "Weather forecast for Karachi this weekend"
        )
        assert crime_type == "other"
        assert confidence == 0.0

    def test_extract_victim_info_age(self):
        parser = NewsArticleParser()
        info = parser.extract_victim_info("A 12-year-old girl was rescued by police")
        assert info.get("victim_age") == 12
        assert info.get("victim_gender") == "female"

    def test_extract_victim_info_multiple(self):
        parser = NewsArticleParser()
        info = parser.extract_victim_info("5 children were recovered from the warehouse")
        assert info.get("victim_count") == 5

    def test_extract_perpetrator_info(self):
        parser = NewsArticleParser()
        info = parser.extract_perpetrator_info("The suspect was arrested by FIA officials")
        assert info.get("arrest_status") == "arrested"

    def test_extract_perpetrator_relationship(self):
        parser = NewsArticleParser()
        info = parser.extract_perpetrator_info("The uncle of the victim was arrested")
        assert info.get("relationship_to_victim") == "family"

    def test_parse_article(self):
        parser = NewsArticleParser()
        article = {
            "url": "https://example.com/article/1",
            "title": "Child trafficking ring busted in Lahore",
            "full_text": "LAHORE: Police arrested five suspects in connection with child trafficking. Three children aged 8-12 were recovered.",
            "published_date": "2026-03-20",
        }
        result = parser.parse_article(article)
        assert result["article_url"] == article["url"]
        assert result["crime_type"] == "child_trafficking"
        assert result["crime_confidence"] > 0
