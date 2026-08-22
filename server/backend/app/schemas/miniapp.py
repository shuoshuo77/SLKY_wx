"""微信小程序专用请求模型。"""
from typing import Literal
from datetime import date, datetime

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class MiniAppChatRequest(BaseModel):
    """小程序智能体对话请求。

    ``history`` 由小程序在当前会话内维护；服务端只转发最近若干轮，
    避免未配置数据库时误把对话内容当作持久化数据。
    """

    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    session_id: str | None = Field(None, max_length=100)


class AppointmentCreate(BaseModel):
    """小程序预约提交参数。"""

    base_id: int = Field(..., ge=1)
    visit_date: date
    time_slot: str = Field(..., min_length=1, max_length=30)
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
    created_at: datetime


class MiniAppStats(BaseModel):
    favorites: int
    appointments: int
    history: int
