"""Schemas for shared homepage content."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


LINK_TYPE_PATTERN = "^(none|url|base|policy|resource|expert)$"


class BannerCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    image_url: str = Field(..., min_length=1, max_length=500)
    link_type: str = Field("none", pattern=LINK_TYPE_PATTERN)
    link_id: Optional[int] = Field(None, ge=1)
    link_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = 0
    is_active: bool = True
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class BannerUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, min_length=1, max_length=500)
    link_type: Optional[str] = Field(None, pattern=LINK_TYPE_PATTERN)
    link_id: Optional[int] = Field(None, ge=1)
    link_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class BannerOut(BaseModel):
    id: int
    title: str
    subtitle: Optional[str]
    image_url: str
    link_type: str
    link_id: Optional[int]
    link_url: Optional[str]
    sort_order: int
    is_active: bool
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]

    model_config = {"from_attributes": True}


class FeaturedServiceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    link_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = 0
    is_active: bool = True


class FeaturedServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    link_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class FeaturedServiceOut(BaseModel):
    id: int
    name: str
    icon: Optional[str]
    description: Optional[str]
    category: Optional[str]
    link_url: Optional[str]
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class HomeMetricOut(BaseModel):
    id: int
    title: str
    metric_value: Optional[str]
    metric_unit: Optional[str]
    growth_rate: Optional[str]
    sort_order: int

    model_config = {"from_attributes": True}


class HomePageOut(BaseModel):
    banners: list[BannerOut]
    featured_services: list[FeaturedServiceOut]
    industry_metrics: list[HomeMetricOut]
