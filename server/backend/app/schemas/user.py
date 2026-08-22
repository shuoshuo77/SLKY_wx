"""
用户相关 Pydantic Schema
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserTypeEnum(str, Enum):
    regular = "regular"
    verified = "verified"
    local_admin = "local_admin"
    platform_admin = "platform_admin"


class VerifyStatusEnum(str, Enum):
    none = "none"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# ---------- 请求 ----------

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=10, max_length=100, description="密码")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    real_name: Optional[str] = Field(None, max_length=50, description="真实姓名")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("密码必须同时包含字母和数字")
        return value


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserUpdate(BaseModel):
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    real_name: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=500)
    province: Optional[str] = Field(None, max_length=30)
    city: Optional[str] = Field(None, max_length=30)


class ChangePassword(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=10, max_length=100, description="新密码")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("密码必须同时包含字母和数字")
        return value


class VerificationSubmit(BaseModel):
    org_name: Optional[str] = Field(None, max_length=200, description="机构名称")
    org_code: Optional[str] = Field(None, max_length=100, description="统一社会信用代码")


class VerificationReview(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$", description="操作: approve/reject")
    reject_reason: Optional[str] = Field(None, max_length=500, description="拒绝原因")


# ---------- 响应 ----------

class UserInfo(BaseModel):
    id: int
    username: str
    phone: Optional[str]
    email: Optional[str]
    real_name: Optional[str]
    avatar_url: Optional[str]
    user_type: str
    province: Optional[str]
    city: Optional[str]
    verify_status: str
    is_active: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserSimple(BaseModel):
    """列表展示用，脱敏信息"""
    id: int
    username: str
    user_type: str
    province: Optional[str]
    city: Optional[str]
    verify_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class VerificationInfo(BaseModel):
    id: int
    user_id: int
    org_name: Optional[str]
    org_code: Optional[str]
    verify_status: str = "pending"
    verified_at: Optional[datetime]
    reject_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedUsers(BaseModel):
    items: List[UserSimple]
    total: int
    page: int
    page_size: int
