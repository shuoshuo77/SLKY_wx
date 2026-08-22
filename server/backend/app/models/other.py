"""
其他数据模型：政策、自然资源、行业数据、专家、需求、审核、收藏、通知、日志
"""
from sqlalchemy import (
    Column, String, Enum, Boolean, DateTime, Text, JSON,
    Integer, Date, ForeignKey, DECIMAL, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import mysql
from datetime import datetime
from app.database import Base, ID_TYPE


LONG_TEXT = Text().with_variant(mysql.LONGTEXT(), "mysql")


class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (
        Index("idx_level_cat", "policy_level", "category"),
        Index("ft_title_content", "title", "content", mysql_prefix="FULLTEXT"),
        Index("idx_policies_status_created", "status", "created_at"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    policy_level = Column(String(20), nullable=True)
    applicable_region = Column(String(200), nullable=True)
    category = Column(String(50), nullable=True)
    issuing_body = Column(String(200), nullable=True)
    publish_date = Column(Date, nullable=True)
    effective_date = Column(Date, nullable=True)
    content = Column(LONG_TEXT, nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(String(300), nullable=True)
    submit_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    status = Column(Enum("draft", "pending", "published", "rejected", "archived"), nullable=False, default="draft")
    reviewed_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reject_reason = Column(Text, nullable=True)
    view_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    attachments = relationship("PolicyAttachment", back_populates="policy", cascade="all, delete-orphan")


class PolicyAttachment(Base):
    __tablename__ = "policy_attachments"
    __table_args__ = (Index("idx_policy_id", "policy_id"),)

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    policy_id = Column(ID_TYPE, ForeignKey("policies.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    policy = relationship("Policy", back_populates="attachments")


class NaturalResource(Base):
    __tablename__ = "natural_resources"
    __table_args__ = (
        Index("idx_type_province", "resource_type", "province"),
        Index("idx_natural_resources_status_created", "status", "created_at"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    resource_type = Column(String(50), nullable=True)
    province = Column(String(30), nullable=False)
    city = Column(String(30), nullable=False)
    district = Column(String(50), nullable=True)
    address = Column(String(300), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    area = Column(DECIMAL(12, 2), nullable=True)
    description = Column(Text, nullable=True)
    features = Column(Text, nullable=True)
    health_value = Column(Text, nullable=True)
    traffic_accessibility = Column(String(300), nullable=True)
    development_status = Column(String(50), nullable=True)
    resource_details = Column(JSON, nullable=True)
    source_url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    submit_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    status = Column(Enum("draft", "pending", "published", "rejected", "archived"), nullable=False, default="draft")
    reviewed_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reject_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class IndustryData(Base):
    __tablename__ = "industry_data"
    __table_args__ = (
        Index("idx_type", "data_type"),
        Index("idx_industry_data_status_created", "status", "created_at"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    title = Column(String(300), nullable=False)
    data_type = Column(String(50), nullable=True)
    metric_value = Column(String(100), nullable=True)
    metric_unit = Column(String(50), nullable=True)
    growth_rate = Column(String(50), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    content = Column(LONG_TEXT, nullable=True)
    data_period = Column(String(50), nullable=True)
    data_source = Column(String(300), nullable=True)
    tags = Column(String(300), nullable=True)
    submit_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    status = Column(Enum("draft", "pending", "published", "rejected", "archived"), nullable=False, default="draft")
    reviewed_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reject_reason = Column(Text, nullable=True)
    view_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    @property
    def summary(self) -> str | None:
        return self.content[:200] if self.content else None


class Expert(Base):
    __tablename__ = "experts"
    __table_args__ = (
        Index("idx_specialty", "specialty"),
        Index("idx_experts_status_created", "status", "created_at"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    expert_type = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    title = Column(String(100), nullable=True)
    organization = Column(String(200), nullable=True)
    specialty = Column(String(300), nullable=True)
    years_experience = Column(Integer, nullable=True)
    research_desc = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    resume_url = Column(String(500), nullable=True)
    profile_data = Column(JSON, nullable=True)
    contact_phone = Column(String(30), nullable=True)
    contact_email = Column(String(100), nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)
    submit_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    status = Column(Enum("draft", "pending", "published", "rejected", "archived"), nullable=False, default="draft")
    reviewed_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reject_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class PublicDemand(Base):
    __tablename__ = "public_demands"
    __table_args__ = (
        Index("idx_pubdemand_user_id", "user_id"),
        Index("idx_city", "preferred_city"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    budget_min = Column(Integer, nullable=True)
    budget_max = Column(Integer, nullable=True)
    preferred_city = Column(String(100), nullable=True)
    preferred_type = Column(String(200), nullable=True)
    stay_duration = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    survey_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_target", "target_type", "target_id"),
        Index("idx_reviewed", "reviewed_by"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    target_type = Column(String(50), nullable=False)
    target_id = Column(ID_TYPE, nullable=False)
    action = Column(Enum("submit", "approve", "reject", "archive", "delete"), nullable=False)
    comment = Column(Text, nullable=True)
    reviewed_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "fav_type", "fav_id", name="uk_user_fav"),
        Index("idx_fav_user_id", "user_id"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fav_type = Column(String(30), nullable=False)
    fav_id = Column(ID_TYPE, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class BaseAppointment(Base):
    """用户对康养基地的预约。"""

    __tablename__ = "base_appointments"
    __table_args__ = (
        Index("idx_appt_user_status_date", "user_id", "status", "visit_date"),
        Index("idx_appt_base_id", "base_id"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False)
    visit_date = Column(Date, nullable=False)
    time_slot = Column(String(30), nullable=False)
    people_count = Column(Integer, nullable=False, default=1)
    contact_name = Column(String(50), nullable=False)
    contact_phone = Column(String(30), nullable=False)
    status = Column(
        Enum("pending", "confirmed", "cancelled"),
        nullable=False,
        default="pending",
    )
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    base = relationship("ForestBase")


class BaseBrowseHistory(Base):
    """用户浏览基地的历史记录，同一基地只保留最新一条。"""

    __tablename__ = "base_browse_history"
    __table_args__ = (
        Index("idx_browse_user_viewed", "user_id", "viewed_at"),
        Index("idx_browse_base_id", "base_id"),
        UniqueConstraint("user_id", "base_id", name="uk_user_base_browse"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    base_id = Column(ID_TYPE, ForeignKey("forest_bases.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime, nullable=False, default=datetime.now)

    base = relationship("ForestBase")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("idx_user_unread", "user_id", "is_read"),)

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    notif_type = Column(String(30), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    link_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class SysLog(Base):
    __tablename__ = "sys_logs"
    __table_args__ = (
        Index("idx_syslog_user_id", "user_id"),
        Index("idx_created", "created_at"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    module = Column(String(50), nullable=True)
    target_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    detail = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
