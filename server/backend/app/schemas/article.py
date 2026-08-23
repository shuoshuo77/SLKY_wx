"""
文章采集相关 Pydantic Schema
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ---- 通用分页 ----
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Any]


# ---- 数据源 ----
class SourceCreate(BaseModel):
    name: str = Field(..., max_length=200, description="数据源名称")
    source_type: str = Field("wechat_oa", description="类型: wechat_oa/gov_website/industry_portal/news_site")
    category: str = Field("official", description="分类: official/industry/policy")
    oa_id: Optional[str] = None
    oa_name: Optional[str] = None
    base_url: Optional[str] = None
    region: Optional[str] = None
    org_name: Optional[str] = None
    description: Optional[str] = None
    crawl_frequency: Optional[str] = Field("daily", description="频率: hourly/daily/weekly/manual")


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    crawl_frequency: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = None
    org_name: Optional[str] = None
    robots_txt_checked: Optional[bool] = None
    robots_txt_allowed: Optional[bool] = None
    respect_note: Optional[str] = None


class SourceOut(BaseModel):
    id: int
    name: str
    source_type: str
    category: str
    oa_name: Optional[str]
    base_url: Optional[str]
    region: Optional[str]
    is_active: bool
    crawl_frequency: str
    last_crawl_at: Optional[datetime]
    last_article_count: int
    total_articles: int

    class Config:
        from_attributes = True


class SourceListOut(BaseModel):
    total: int
    items: List[SourceOut]


# ---- 关键词 ----
class KeywordCreate(BaseModel):
    keyword: str = Field(..., max_length=100)
    keyword_type: str = Field("extended", description="类型: core/extended/exclude")
    category: Optional[str] = None
    weight: Optional[int] = None


class KeywordOut(BaseModel):
    id: int
    keyword: str
    keyword_type: str
    category: Optional[str]
    weight: int
    is_active: bool

    class Config:
        from_attributes = True


class KeywordListOut(BaseModel):
    total: int
    items: List[KeywordOut]


# ---- 文章 ----
class ArticleOut(BaseModel):
    id: int
    title: str
    source_name: Optional[str]
    publish_time: Optional[datetime]
    summary: Optional[str]
    cover_image: Optional[str]
    article_category: Optional[str]
    quality_score: Optional[float]
    matched_keywords: Optional[List[str]]
    related_province: Optional[str]
    related_city: Optional[str]
    image_count: int
    view_count: int
    status: str

    class Config:
        from_attributes = True


class ArticleListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ArticleOut]


class ArticleDetailOut(BaseModel):
    id: int
    title: str
    author: Optional[str]
    source_name: Optional[str]
    publish_time: Optional[datetime]
    crawl_time: Optional[datetime]
    summary: Optional[str]
    content_html: Optional[str]
    content_text: Optional[str]
    content_length: Optional[int]
    original_url: str
    matched_keywords: Optional[List[str]]
    article_category: Optional[str]
    tags: Optional[List[str]]
    quality_score: Optional[float]
    is_low_quality: bool
    related_province: Optional[str]
    related_city: Optional[str]
    image_count: int
    cover_image: Optional[str]
    view_count: int
    status: str
    images: List[dict]
    linked_bases: List[dict]

    class Config:
        from_attributes = True


class ArticleReview(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$", description="审核结果: approved/rejected")
    reason: Optional[str] = Field(None, max_length=500, description="拒绝原因")


# ---- 任务 ----
class TaskOut(BaseModel):
    id: int
    source_id: Optional[int]
    task_type: str
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    urls_found: int
    articles_new: int
    articles_dup: int
    articles_low_quality: int
    errors: int
    summary: Optional[str]

    class Config:
        from_attributes = True


class TaskListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TaskOut]
