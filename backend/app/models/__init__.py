"""Re-export all models so Alembic and other tooling can discover them."""

from app.models.base import Base
from app.models.boundaries import Boundary, DistrictNameVariant
from app.models.incidents import Incident
from app.models.brick_kilns import BrickKiln
from app.models.border_crossings import BorderCrossing
from app.models.trafficking_routes import TraffickingRoute
from app.models.court_judgments import CourtJudgment
from app.models.vulnerability import VulnerabilityIndicator
from app.models.tip_report import TipReportAnnual
from app.models.public_reports import PublicReport
from app.models.news_articles import NewsArticle, DataSource
from app.models.statistical_reports import StatisticalReport
from app.models.transparency_reports import TransparencyReport

__all__ = [
    "Base",
    "Boundary",
    "DistrictNameVariant",
    "Incident",
    "BrickKiln",
    "BorderCrossing",
    "TraffickingRoute",
    "CourtJudgment",
    "VulnerabilityIndicator",
    "TipReportAnnual",
    "PublicReport",
    "NewsArticle",
    "DataSource",
    "StatisticalReport",
    "TransparencyReport",
]
