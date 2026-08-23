"""
森林康养基地相关数据模型
"""
from sqlalchemy import (
    Column, String, Enum, Boolean, DateTime, Text, JSON,
    Integer, Float, DECIMAL, Date, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base, ID_TYPE


class ForestBase(Base):
    __tablename__ = "forest_bases"
    __table_args__ = (
        Index("idx_forest_bases_status_created", "status", "created_at"),
        Index("idx_status", "status"),
        Index("idx_province_city", "province", "city"),
        Index("idx_forest_coverage", "forest_coverage"),
        Index("idx_submit_by", "submit_by"),
        Index("ft_name_desc", "name", "description", mysql_prefix="FULLTEXT"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    province = Column(String(30), nullable=False)
    city = Column(String(30), nullable=False)
    district = Column(String(50), nullable=True)
    address = Column(String(300), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    established_date = Column(Date, nullable=True)
    total_area = Column(DECIMAL(10, 2), nullable=True)
    forest_coverage = Column(DECIMAL(5, 2), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)

    status = Column(
        Enum("draft", "pending", "approved", "rejected", "archived"),
        nullable=False,
        default="draft",
    )
    submit_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    reviewed_by = Column(ID_TYPE, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reject_reason = Column(String(500), nullable=True)

    view_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    submitter = relationship("User", foreign_keys=[submit_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    qualifications = relationship("BaseQualification", back_populates="base", cascade="all, delete-orphan")
    resources = relationship("BaseResource", back_populates="base", uselist=False, cascade="all, delete-orphan")
    business = relationship("BaseBusiness", back_populates="base", uselist=False, cascade="all, delete-orphan")
    operations = relationship("BaseOperation", back_populates="base", uselist=False, cascade="all, delete-orphan")
    media = relationship("BaseMedia", back_populates="base", cascade="all, delete-orphan")
    contacts = relationship("BaseContact", back_populates="base", cascade="all, delete-orphan")


class BaseQualification(Base):
    __tablename__ = "base_qualifications"
    __table_args__ = (Index("idx_base_id", "base_id"),)

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False)

    qual_level = Column(String(50), nullable=True)
    qual_name = Column(String(200), nullable=True)
    qual_number = Column(String(100), nullable=True)
    issuing_authority = Column(String(200), nullable=True)
    issue_date = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    qual_file = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    base = relationship("ForestBase", back_populates="qualifications")


class BaseResource(Base):
    __tablename__ = "base_resources"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False, unique=True)

    negative_oxygen_ions = Column(Integer, nullable=True)
    average_temperature = Column(DECIMAL(5, 2), nullable=True)
    altitude_min = Column(Integer, nullable=True)
    altitude_max = Column(Integer, nullable=True)
    vegetation_types = Column(String(500), nullable=True)
    water_source = Column(String(200), nullable=True)
    water_quality = Column(String(50), nullable=True)
    eco_features = Column(Text, nullable=True)
    surroundings = Column(Text, nullable=True)
    hot_spring = Column(Boolean, default=False)
    medicinal_herbs = Column(Text, nullable=True)
    cultural_features = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    base = relationship("ForestBase", back_populates="resources")


class BaseBusiness(Base):
    __tablename__ = "base_business"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False, unique=True)

    product_types = Column(JSON, nullable=True)
    has_accommodation = Column(Boolean, default=False)
    accommodation_desc = Column(Text, nullable=True)
    has_dining = Column(Boolean, default=False)
    dining_desc = Column(Text, nullable=True)
    has_medical = Column(Boolean, default=False)
    medical_desc = Column(Text, nullable=True)
    has_parking = Column(Boolean, default=False)
    parking_capacity = Column(Integer, nullable=True)
    recreation_projects = Column(JSON, nullable=True)
    pricing_info = Column(JSON, nullable=True)
    partner_institutions = Column(Text, nullable=True)
    investment_needs = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    base = relationship("ForestBase", back_populates="business")


class BaseOperation(Base):
    __tablename__ = "base_operations"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False, unique=True)

    annual_visitors = Column(Integer, nullable=True)
    business_season = Column(String(100), nullable=True)
    business_hours = Column(String(200), nullable=True)
    team_size = Column(Integer, nullable=True)
    has_emergency_plan = Column(Boolean, default=False)
    certifications = Column(JSON, nullable=True)
    official_website = Column(String(300), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    base = relationship("ForestBase", back_populates="operations")


class BaseMedia(Base):
    __tablename__ = "base_media"
    __table_args__ = (Index("idx_media_base_id", "base_id"),)

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False)

    media_type = Column(Enum("image", "video", "document"), nullable=False, default="image")
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=True)
    description = Column(String(500), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    base = relationship("ForestBase", back_populates="media")


class BaseContact(Base):
    __tablename__ = "base_contacts"
    __table_args__ = (Index("idx_contact_base_id", "base_id"),)

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False)

    contact_name = Column(String(50), nullable=False)
    contact_phone = Column(String(30), nullable=True)
    contact_email = Column(String(100), nullable=True)
    position = Column(String(50), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    base = relationship("ForestBase", back_populates="contacts")
