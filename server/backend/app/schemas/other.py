"""
通用Schema：政策、自然资源、行业数据、专家、需求等
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal
from app.utils.html import sanitize_html


# ===================== 政策 =====================

class PolicyCreate(BaseModel):
    title: str = Field(..., max_length=300)
    policy_level: Optional[str] = Field(None, max_length=20)
    applicable_region: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    issuing_body: Optional[str] = Field(None, max_length=200)
    publish_date: Optional[date] = None
    effective_date: Optional[date] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=300)


class PolicyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    policy_level: Optional[str] = Field(None, max_length=20)
    applicable_region: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    issuing_body: Optional[str] = Field(None, max_length=200)
    publish_date: Optional[date] = None
    effective_date: Optional[date] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = Field(None, max_length=300)


class PolicyOut(BaseModel):
    id: int
    title: str
    policy_level: Optional[str]
    applicable_region: Optional[str]
    category: Optional[str]
    issuing_body: Optional[str]
    publish_date: Optional[date]
    summary: Optional[str]
    tags: Optional[str]
    status: str
    view_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PolicyDetailOut(PolicyOut):
    content: Optional[str]
    effective_date: Optional[date]
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("content")
    @classmethod
    def clean_content(cls, value):
        return sanitize_html(value)


class PaginatedPolicies(BaseModel):
    items: List[PolicyOut]
    total: int
    page: int
    page_size: int


# ===================== 自然资源 =====================

class ResourceCreateReq(BaseModel):
    name: str = Field(..., max_length=200)
    resource_type: Optional[str] = Field(None, max_length=50)
    province: str = Field(..., max_length=30)
    city: str = Field(..., max_length=30)
    district: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=300)
    longitude: Optional[Decimal] = None
    latitude: Optional[Decimal] = None
    area: Optional[Decimal] = None
    description: Optional[str] = None
    features: Optional[str] = None
    health_value: Optional[str] = None
    traffic_accessibility: Optional[str] = Field(None, max_length=300)
    development_status: Optional[str] = Field(None, max_length=50)
    resource_details: Optional[Any] = None
    source_url: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, max_length=500)


class ResourceUpdateReq(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    resource_type: Optional[str] = Field(None, max_length=50)
    province: Optional[str] = Field(None, max_length=30)
    city: Optional[str] = Field(None, max_length=30)
    district: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=300)
    longitude: Optional[Decimal] = None
    latitude: Optional[Decimal] = None
    area: Optional[Decimal] = None
    description: Optional[str] = None
    features: Optional[str] = None
    health_value: Optional[str] = None
    traffic_accessibility: Optional[str] = Field(None, max_length=300)
    development_status: Optional[str] = Field(None, max_length=50)
    resource_details: Optional[Any] = None
    source_url: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, max_length=500)


class NaturalResourceOut(BaseModel):
    id: int
    name: str
    resource_type: Optional[str]
    province: str
    city: str
    district: Optional[str]
    address: Optional[str]
    area: Optional[Decimal]
    description: Optional[str]
    features: Optional[str]
    health_value: Optional[str]
    traffic_accessibility: Optional[str]
    development_status: Optional[str]
    resource_details: Optional[Any]
    source_url: Optional[str]
    image_url: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResources(BaseModel):
    items: List[NaturalResourceOut]
    total: int
    page: int
    page_size: int


# ===================== 行业数据 =====================

class IndustryDataCreate(BaseModel):
    title: str = Field(..., max_length=300)
    data_type: Optional[str] = Field(None, max_length=50)
    metric_value: Optional[str] = Field(None, max_length=100)
    metric_unit: Optional[str] = Field(None, max_length=50)
    growth_rate: Optional[str] = Field(None, max_length=50)
    sort_order: int = 0
    content: Optional[str] = None
    data_period: Optional[str] = Field(None, max_length=50)
    data_source: Optional[str] = Field(None, max_length=300)
    tags: Optional[str] = Field(None, max_length=300)


class IndustryDataUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    data_type: Optional[str] = Field(None, max_length=50)
    metric_value: Optional[str] = Field(None, max_length=100)
    metric_unit: Optional[str] = Field(None, max_length=50)
    growth_rate: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = None
    content: Optional[str] = None
    data_period: Optional[str] = Field(None, max_length=50)
    data_source: Optional[str] = Field(None, max_length=300)
    tags: Optional[str] = Field(None, max_length=300)


class IndustryDataOut(BaseModel):
    id: int
    title: str
    data_type: Optional[str]
    metric_value: Optional[str]
    metric_unit: Optional[str]
    growth_rate: Optional[str]
    sort_order: int
    data_period: Optional[str]
    data_source: Optional[str]
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str]
    status: str
    view_count: int
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("content")
    @classmethod
    def clean_content(cls, value):
        return sanitize_html(value)


class PaginatedIndustry(BaseModel):
    items: List[IndustryDataOut]
    total: int
    page: int
    page_size: int


# ===================== 专家 =====================

class ExpertCreate(BaseModel):
    name: str = Field(..., max_length=50)
    expert_type: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    organization: Optional[str] = Field(None, max_length=200)
    specialty: Optional[str] = Field(None, max_length=300)
    years_experience: Optional[int] = Field(None, ge=0, le=100)
    research_desc: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    resume_url: Optional[str] = Field(None, max_length=500)
    profile_data: Optional[Any] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[str] = Field(None, max_length=100)
    is_public: bool = False


class ExpertUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    expert_type: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    organization: Optional[str] = Field(None, max_length=200)
    specialty: Optional[str] = Field(None, max_length=300)
    years_experience: Optional[int] = Field(None, ge=0, le=100)
    research_desc: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    resume_url: Optional[str] = Field(None, max_length=500)
    profile_data: Optional[Any] = None
    contact_phone: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[str] = Field(None, max_length=100)
    is_public: bool = False


class ExpertOut(BaseModel):
    id: int
    name: str
    expert_type: Optional[str]
    region: Optional[str]
    title: Optional[str]
    organization: Optional[str]
    specialty: Optional[str]
    years_experience: Optional[int]
    research_desc: Optional[str]
    avatar_url: Optional[str]
    resume_url: Optional[str]
    profile_data: Optional[Any]
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_public: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedExperts(BaseModel):
    items: List[ExpertOut]
    total: int
    page: int
    page_size: int


# ===================== 公众需求 =====================

class DemandCreate(BaseModel):
    budget_min: Optional[int] = None
    budget_max: Optional[int] = None
    preferred_city: Optional[str] = Field(None, max_length=100)
    preferred_type: Optional[str] = Field(None, max_length=200)
    stay_duration: Optional[int] = None
    feedback: Optional[str] = None
    survey_data: Optional[Any] = None


class DemandOut(BaseModel):
    id: int
    user_id: Optional[int]
    budget_min: Optional[int]
    budget_max: Optional[int]
    preferred_city: Optional[str]
    preferred_type: Optional[str]
    stay_duration: Optional[int]
    feedback: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedDemands(BaseModel):
    items: List[DemandOut]
    total: int
    page: int
    page_size: int


class ResourceReview(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reject_reason: Optional[str] = Field(None, max_length=500)


# ===================== 收藏 & 通知 =====================

class FavoriteCreate(BaseModel):
    fav_type: str = Field(..., description="base/policy/resource/expert")
    fav_id: int = Field(..., description="收藏对象ID")


class FavoriteOut(BaseModel):
    id: int
    fav_type: str
    fav_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: int
    title: str
    content: Optional[str]
    notif_type: Optional[str]
    is_read: bool
    link_url: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    items: List[NotificationOut]
    total: int
    unread_count: int
    page: int
    page_size: int
