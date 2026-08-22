"""Homepage content shared by the web client and mini-program."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.database import Base, ID_TYPE


class Banner(Base):
    __tablename__ = "banners"
    __table_args__ = (
        Index("idx_banners_active_sort", "is_active", "sort_order"),
        Index("idx_banners_schedule", "starts_at", "ends_at"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=False)
    link_type = Column(String(30), nullable=False, default="none")
    link_id = Column(ID_TYPE, nullable=True)
    link_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_by = Column(ID_TYPE, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class FeaturedService(Base):
    __tablename__ = "featured_services"
    __table_args__ = (
        Index("idx_featured_services_active_sort", "is_active", "sort_order"),
        Index("idx_featured_services_category", "category"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    link_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(ID_TYPE, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
