"""Pydantic schemas for legal / court judgment endpoints."""

from datetime import date

from pydantic import BaseModel, Field


class JudgmentSearchParams(BaseModel):
    """Query parameters for searching court judgments."""

    model_config = {"frozen": True, "populate_by_name": True}

    court: str | None = None
    year_from: int | None = Field(default=None, alias="yearFrom")
    year_to: int | None = Field(default=None, alias="yearTo")
    ppc_section: str | None = Field(default=None, alias="ppcSection")
    verdict: str | None = None
    district: str | None = None


class JudgmentResponse(BaseModel):
    """Court judgment search result."""

    model_config = {"frozen": True, "populate_by_name": True}

    id: int
    court_name: str | None = Field(default=None, alias="courtName")
    case_number: str | None = Field(default=None, alias="caseNumber")
    judgment_date: date | None = Field(default=None, alias="date")
    ppc_sections: list[str] = Field(default_factory=list, alias="ppcSections")
    verdict: str | None = None
    sentence_years: float | None = Field(default=None, alias="sentenceYears")
    district: str | None = None


class ConvictionRateResponse(BaseModel):
    """Conviction rate aggregation row."""

    model_config = {"frozen": True}

    district: str | None = None
    court: str | None = None
    year: int | None = None
    investigations: int = 0
    convictions: int = 0
    rate: float = 0.0
