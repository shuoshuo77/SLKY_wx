"""
用户相关数据模型
"""
from sqlalchemy import (
    Column, String, Enum, Boolean, DateTime, Text, JSON, Integer, Float,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base, ID_TYPE


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_type", "user_type"),
        Index("idx_verify_status", "verify_status"),
        Index("idx_user_province_city", "province", "city"),
    )

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    real_name = Column(String(50), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    user_type = Column(
        Enum("regular", "verified", "local_admin", "platform_admin"),
        nullable=False,
        default="regular",
    )
    province = Column(String(30), nullable=True)
    city = Column(String(30), nullable=True)
    verify_status = Column(
        Enum("none", "pending", "approved", "rejected"),
        nullable=False,
        default="none",
    )
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    verification = relationship(
        "UserVerification",
        back_populates="user",
        uselist=False,
        foreign_keys="UserVerification.user_id",
    )
    # submitted_bases / reviewed_bases 不在此定义，避免多外键歧义。
    # 需要时用查询：
    #   db.query(ForestBase).filter(ForestBase.submit_by == user.id).all()


class UserVerification(Base):
    __tablename__ = "user_verifications"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    id_card_front = Column(String(500), nullable=True)
    id_card_back = Column(String(500), nullable=True)
    business_license = Column(String(500), nullable=True)
    org_name = Column(String(200), nullable=True)
    org_code = Column(String(100), nullable=True)
    qualification_files = Column(JSON, nullable=True)

    verified_by = Column(ID_TYPE, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    reject_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    user = relationship("User", back_populates="verification", foreign_keys=[user_id])
