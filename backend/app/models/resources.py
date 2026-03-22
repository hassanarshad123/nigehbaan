"""Resources model for helplines, legal aid, shelters, and NGOs."""

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.models.base import Base


class Resource(Base):
    """A helpline, shelter, legal aid provider, or NGO contact."""

    __tablename__ = "resources"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    category: str = Column(String(50), nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    description: str | None = Column(Text, nullable=True)
    contact: str | None = Column(String(255), nullable=True)
    url: str | None = Column(Text, nullable=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    sort_order: int = Column(Integer, default=0, nullable=False)
