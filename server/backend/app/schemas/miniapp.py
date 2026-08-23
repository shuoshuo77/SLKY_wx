"""微信小程序专用请求模型。"""
from typing import Literal
from datetime import date, datetime

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=1200)


class MiniAppChatRequest(BaseModel):
    """小程序智能体对话请求。

    ``history`` 由小程序在当前会话内维护；服务端只转发最近若干轮，
    避免未配置数据库时误把对话内容当作持久化数据。
    """

    message: str = Field(..., min_length=1, max_length=1200)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    session_id: str | None = Field(None, max_length=100)


class MiniAppChatResponse(BaseModel):
    session_id: str
    reply: str
    provider: Literal["deepseek", "coze", "local"]
    suggestions: list[str]
    disclaimer: str


class BaseCardOut(BaseModel):
    id: int
    name: str
    province: str
    city: str
    district: str | None
    address: str
    forest_coverage: float | None
    primary_image: str | None
    view_count: int
    tags: list[str]
    reason: str | None = None
    distance_km: float | None = None


class HomeBannerOut(BaseModel):
    id: str
    title: str
    subtitle: str
    image_url: str | None
    target_type: Literal["base"]
    target_id: int
    target_url: str


class FeatureEntryOut(BaseModel):
    key: str
    title: str
    path: str


class MiniAppHomeOut(BaseModel):
    banners: list[HomeBannerOut]
    hot_bases: list[BaseCardOut]
    feature_entries: list[FeatureEntryOut]
    stats: dict[str, int]


class RecommendationOut(BaseModel):
    items: list[BaseCardOut]
    recommendation_mode: Literal["nearby", "location", "popular"]
    location_used: bool
    radius_km: float | None = None


class MapBaseOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    province: str
    city: str
    address: str
    primary_image: str | None


class MapBasesOut(BaseModel):
    items: list[MapBaseOut]
    total: int
    page: int
    page_size: int


class AppointmentCreate(BaseModel):
    """小程序预约提交参数。"""

    base_id: int = Field(..., ge=1)
    visit_date: date
    time_slot: Literal["09:00-10:00", "10:30-11:30", "14:00-15:00", "15:30-16:30"]
    people_count: int = Field(1, ge=1, le=20)
    contact_name: str = Field(..., min_length=1, max_length=50)
    contact_phone: str = Field(..., min_length=5, max_length=30)


class AppointmentOut(BaseModel):
    id: int
    base_id: int
    base_name: str
    base_image: str | None = None
    visit_date: date
    time_slot: str
    people_count: int
    contact_name: str
    contact_phone: str
    status: str
    status_label: str
    status_note: str | None = None
    created_at: datetime


class AppointmentListOut(BaseModel):
    items: list[AppointmentOut]
    total: int
    page: int
    page_size: int


class AppointmentStatusUpdate(BaseModel):
    action: Literal["confirm", "reject", "cancel"]
    note: str | None = Field(None, max_length=500)


class FavoriteBaseOut(BaseModel):
    base_id: int
    base_name: str
    base_image: str | None = None
    area: str
    province: str
    city: str
    district: str | None = None
    tags: list[str]
    view_count: int
    created_at: datetime


class FavoriteBaseListOut(BaseModel):
    items: list[FavoriteBaseOut]


class FavoriteMutationOut(BaseModel):
    favorited: bool


class HistoryClearOut(BaseModel):
    cleared: int


class ViewRecordedOut(BaseModel):
    recorded: bool


class ActionOut(BaseModel):
    message: str


class MiniAppStats(BaseModel):
    favorites: int
    appointments: int
    history: int
