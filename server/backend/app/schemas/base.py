"""
康养基地相关 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class BaseStatusEnum(str, Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


# ---------- 资质 ----------

class QualificationCreate(BaseModel):
    qual_level: Optional[str] = Field(None, max_length=50, description="等级")
    qual_name: Optional[str] = Field(None, max_length=200, description="资质名称")
    qual_number: Optional[str] = Field(None, max_length=100, description="资质编号")
    issuing_authority: Optional[str] = Field(None, max_length=200, description="颁发机构")
    issue_date: Optional[date] = Field(None, description="颁发日期")
    valid_until: Optional[date] = Field(None, description="有效期")
    qual_file: Optional[str] = Field(None, max_length=500, description="资质文件URL")


class QualificationOut(BaseModel):
    id: int
    qual_level: Optional[str]
    qual_name: Optional[str]
    qual_number: Optional[str]
    issuing_authority: Optional[str]
    issue_date: Optional[date]
    valid_until: Optional[date]
    qual_file: Optional[str]

    model_config = {"from_attributes": True}


# ---------- 自然资源 ----------

class ResourceCreate(BaseModel):
    negative_oxygen_ions: Optional[int] = Field(None, description="负氧离子浓度")
    altitude_min: Optional[int] = Field(None, description="最低海拔")
    altitude_max: Optional[int] = Field(None, description="最高海拔")
    vegetation_types: Optional[str] = Field(None, max_length=500, description="植被类型")
    water_source: Optional[str] = Field(None, max_length=200, description="水源")
    water_quality: Optional[str] = Field(None, max_length=50, description="水质等级")
    eco_features: Optional[str] = Field(None, description="生态景观")
    surroundings: Optional[str] = Field(None, description="周边环境")
    hot_spring: bool = False
    medicinal_herbs: Optional[str] = Field(None, description="药材资源")
    cultural_features: Optional[str] = Field(None, description="文化资源")


class ResourceOut(BaseModel):
    negative_oxygen_ions: Optional[int]
    average_temperature: Optional[Decimal]
    altitude_min: Optional[int]
    altitude_max: Optional[int]
    vegetation_types: Optional[str]
    water_source: Optional[str]
    water_quality: Optional[str]
    eco_features: Optional[str]
    surroundings: Optional[str]
    hot_spring: bool
    medicinal_herbs: Optional[str]
    cultural_features: Optional[str]

    model_config = {"from_attributes": True}


# ---------- 业态 ----------

class BusinessCreate(BaseModel):
    product_types: Optional[Any] = Field(None, description="产品类型列表JSON")
    has_accommodation: bool = False
    accommodation_desc: Optional[str] = None
    has_dining: bool = False
    dining_desc: Optional[str] = None
    has_medical: bool = False
    medical_desc: Optional[str] = None
    has_parking: bool = False
    parking_capacity: Optional[int] = None
    recreation_projects: Optional[Any] = None
    pricing_info: Optional[Any] = None


class BusinessOut(BaseModel):
    product_types: Optional[Any]
    has_accommodation: bool
    accommodation_desc: Optional[str]
    has_dining: bool
    dining_desc: Optional[str]
    has_medical: bool
    medical_desc: Optional[str]
    has_parking: bool
    parking_capacity: Optional[int]
    recreation_projects: Optional[Any]
    pricing_info: Optional[Any]

    model_config = {"from_attributes": True}


# ---------- 经营 ----------

class OperationCreate(BaseModel):
    annual_visitors: Optional[int] = Field(None, description="年接待人次")
    business_season: Optional[str] = Field(None, max_length=100, description="营业季节")
    business_hours: Optional[str] = Field(None, max_length=200, description="营业时间")
    team_size: Optional[int] = Field(None, description="团队规模")
    has_emergency_plan: bool = False
    certifications: Optional[Any] = None
    official_website: Optional[str] = Field(None, max_length=300)


class OperationOut(BaseModel):
    annual_visitors: Optional[int]
    business_season: Optional[str]
    business_hours: Optional[str]
    team_size: Optional[int]
    has_emergency_plan: bool
    certifications: Optional[Any]
    official_website: Optional[str]

    model_config = {"from_attributes": True}


# ---------- 多媒体 ----------

class MediaCreate(BaseModel):
    media_type: str = Field("image", description="image/video/document")
    file_url: str = Field(..., max_length=500)
    file_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_primary: bool = False
    sort_order: int = 0


class MediaOut(BaseModel):
    id: int
    media_type: str
    file_url: str
    file_name: Optional[str]
    description: Optional[str]
    is_primary: bool
    sort_order: int

    model_config = {"from_attributes": True}


# ---------- 联系方式 ----------

class ContactCreate(BaseModel):
    contact_name: str = Field(..., max_length=50)
    contact_phone: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=50)
    is_primary: bool = False


class ContactOut(BaseModel):
    id: int
    contact_name: str
    contact_phone: Optional[str]
    contact_email: Optional[str]
    position: Optional[str]
    is_primary: bool

    model_config = {"from_attributes": True}


# ---------- 基地主表 ----------

class BaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="基地名称")
    province: str = Field(..., max_length=30)
    city: str = Field(..., max_length=30)
    district: Optional[str] = Field(None, max_length=50)
    address: str = Field(..., max_length=300)
    longitude: Optional[Decimal] = Field(None, description="经度")
    latitude: Optional[Decimal] = Field(None, description="纬度")
    established_date: Optional[date] = None
    total_area: Optional[Decimal] = Field(None, description="占地面积(亩)")
    forest_coverage: Optional[Decimal] = Field(None, description="森林覆盖率(%)")
    description: Optional[str] = None

    # 可一并提交的子表
    qualifications: Optional[List[QualificationCreate]] = None
    resources: Optional[ResourceCreate] = None
    business: Optional[BusinessCreate] = None
    operations: Optional[OperationCreate] = None
    contacts: Optional[List[ContactCreate]] = None


class BaseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    province: Optional[str] = Field(None, max_length=30)
    city: Optional[str] = Field(None, max_length=30)
    district: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=300)
    longitude: Optional[Decimal] = None
    latitude: Optional[Decimal] = None
    established_date: Optional[date] = None
    total_area: Optional[Decimal] = None
    forest_coverage: Optional[Decimal] = None
    description: Optional[str] = None


class BaseListOut(BaseModel):
    """列表展示"""
    id: int
    name: str
    province: str
    city: str
    district: Optional[str]
    address: Optional[str]
    forest_coverage: Optional[Decimal]
    description: Optional[str]
    tags: Optional[str] = None
    status: str
    view_count: int
    primary_image: Optional[str] = Field(None, description="主图URL")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BaseDetailOut(BaseModel):
    """详情展示"""
    id: int
    name: str
    province: str
    city: str
    district: Optional[str]
    address: str
    longitude: Optional[Decimal]
    latitude: Optional[Decimal]
    established_date: Optional[date]
    total_area: Optional[Decimal]
    forest_coverage: Optional[Decimal]
    description: Optional[str]
    tags: Optional[str] = None
    status: str
    view_count: int
    submit_by: int
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    reject_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    # 子表
    qualifications: List[QualificationOut] = Field(default_factory=list)
    resources: Optional[ResourceOut] = None
    business: Optional[BusinessOut] = None
    operations: Optional[OperationOut] = None
    media: List[MediaOut] = Field(default_factory=list)
    contacts: List[ContactOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class BaseReview(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|archive)$")
    reject_reason: Optional[str] = Field(None, max_length=500)


class PaginatedBases(BaseModel):
    items: List[BaseListOut]
    total: int
    page: int
    page_size: int


class BaseQuery(BaseModel):
    """查询筛选条件"""
    keyword: Optional[str] = Field(None, description="关键词搜索")
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    status: Optional[str] = Field("approved", description="状态筛选")
    qual_level: Optional[str] = None
    min_coverage: Optional[float] = Field(None, description="最低森林覆盖率")
    max_coverage: Optional[float] = Field(None, description="最高森林覆盖率")
    product_type: Optional[str] = Field(None, description="康养产品类型")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="asc/desc")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
