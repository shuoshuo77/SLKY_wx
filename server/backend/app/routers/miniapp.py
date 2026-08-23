"""微信小程序首页、推荐、地图与智能体接口。"""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from time import sleep
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.base import ForestBase
from app.models.other import Expert, NaturalResource, Policy
from app.models.user import User
from app.routers.bases import get_base, list_bases
from app.schemas.base import PaginatedBases
from app.schemas.miniapp import (
    MapBasesOut,
    MiniAppChatRequest,
    MiniAppChatResponse,
    MiniAppHomeOut,
    RecommendationOut,
)
from app.utils.rate_limit import client_ip, rate_limiter

router = APIRouter(prefix="/api", tags=["微信小程序"])
settings = get_settings()

_QUICK_QUESTIONS = [
    "推荐适合避暑的森林康养基地",
    "森林康养有哪些常见方式？",
    "如何根据所在城市筛选基地？",
]

_SYSTEM_PROMPT = (
    "You are the assistant for a forest wellness mini program. "
    "Answer in concise Chinese. Help with base recommendations, platform usage, "
    "general wellness information, and remind users to consult a medical professional "
    "for diagnosis or treatment."
)


def _primary_image(base: ForestBase) -> str | None:
    media = sorted(base.media, key=lambda item: item.sort_order)
    primary = next((item for item in media if item.is_primary), None)
    return (primary or next((item for item in media if item.media_type == "image"), None)).file_url \
        if primary or any(item.media_type == "image" for item in media) else None


def _base_card(base: ForestBase, *, reason: str | None = None, distance_km: float | None = None) -> dict:
    display_tags = (
        [tag.strip() for tag in base.tags.split(",") if tag.strip()]
        if base.tags
        else [q.qual_level for q in base.qualifications if q.qual_level]
    )
    return {
        "id": base.id,
        "name": base.name,
        "province": base.province,
        "city": base.city,
        "district": base.district,
        "address": base.address,
        "forest_coverage": float(base.forest_coverage) if base.forest_coverage is not None else None,
        "primary_image": _primary_image(base),
        "view_count": base.view_count or 0,
        "tags": display_tags[:3],
        "reason": reason,
        "distance_km": distance_km,
    }


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance; coordinates are only used for this request."""
    earth_radius_km = 6371.0088
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2
    return earth_radius_km * 2 * asin(sqrt(a))


def _coze_base_url() -> str:
    api_url = settings.COZE_API_URL.rstrip("/")
    if api_url.endswith("/v3/chat"):
        return api_url[:-8]
    if api_url.endswith("/v3"):
        return api_url[:-3]
    return api_url


def _coze_request(url: str, *, method: str = "GET", json: dict | None = None) -> dict:
    response = requests.request(
        method,
        url,
        headers={
            "Authorization": f"Bearer {settings.COZE_API_TOKEN}",
            "Content-Type": "application/json",
        },
        json=json,
        timeout=settings.DEEPSEEK_TIMEOUT_SECONDS,
    )
    data = response.json() if response.content else {}
    if not response.ok or data.get("code") not in (None, 0):
        message = data.get("msg") or data.get("message") or data.get("error") or f"Coze request failed ({response.status_code})"
        raise requests.RequestException(message)
    return data


def _coze_answer_from_messages(data: dict) -> str:
    messages = data.get("data") if isinstance(data.get("data"), list) else []
    answer = next((item for item in messages if item.get("role") == "assistant" and item.get("type") == "answer"), None)
    if not answer:
        answer = next((item for item in messages if item.get("role") == "assistant"), None)
    return (answer or {}).get("content", "").strip()


def _local_chat_reply(message: str) -> str:
    normalized = "".join(message.split())
    if "预约" in normalized or "参访" in normalized:
        return "可以预约参访。进入基地详情页后，点击“预约参访”，选择日期、时间段、人数并填写联系人信息即可提交。"
    if "避暑" in normalized or "夏季" in normalized:
        return "夏季避暑可以优先查看森林覆盖率高、海拔较高或靠近山地水系的基地。你可以在基地列表里按地区筛选，再进入详情查看环境与服务信息。"
    if "广东" in normalized:
        return "你可以先在基地列表里选择广东相关地区，再结合基地标签、浏览热度和详情页介绍筛选适合的康养基地。"
    if "推荐" in normalized or "基地" in normalized:
        return "可以从首页热门推荐和基地列表开始筛选，重点看地区、森林覆盖率、服务项目和用户关注度。进入详情页后还能收藏或预约参访。"
    return "在线智能咨询暂时不可用，我先提供平台内置答复：你可以查看首页推荐、基地列表、地图找基地、环境监测、收藏和预约参访等功能。"


def _chat_with_coze(req: MiniAppChatRequest, session_id: str) -> str:
    if not settings.COZE_API_TOKEN or not settings.COZE_BOT_ID:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="智能咨询服务尚未配置")

    create_data = _coze_request(
        settings.COZE_API_URL,
        method="POST",
        json={
            "bot_id": settings.COZE_BOT_ID,
            "user_id": settings.COZE_USER_ID,
            "stream": False,
            "auto_save_history": True,
            "conversation_id": req.session_id or None,
            "additional_messages": [
                {
                    "role": "user",
                    "content": f"{_SYSTEM_PROMPT}\n\n用户问题：{req.message}",
                    "content_type": "text",
                }
            ],
        },
    )
    chat = create_data.get("data") or create_data
    chat_id = chat.get("id") or chat.get("chat_id")
    conversation_id = chat.get("conversation_id") or req.session_id or session_id
    status_text = chat.get("status") or ""
    base_url = _coze_base_url()

    for _ in range(settings.COZE_MAX_POLLS):
        if not chat_id or not conversation_id or status_text in {"completed", "failed", "requires_action"}:
            break
        sleep(settings.COZE_POLL_INTERVAL_SECONDS)
        retrieve_data = _coze_request(
            f"{base_url}/v3/chat/retrieve?conversation_id={conversation_id}&chat_id={chat_id}"
        )
        status_text = (retrieve_data.get("data") or {}).get("status") or retrieve_data.get("status") or status_text

    if status_text == "failed":
        raise requests.RequestException("Coze chat failed")

    message_data = _coze_request(
        f"{base_url}/v3/chat/message/list?conversation_id={conversation_id}&chat_id={chat_id}"
    )
    return _coze_answer_from_messages(message_data) or "智能助手暂时没有返回内容。"


def _chat_with_deepseek(req: MiniAppChatRequest) -> str:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        *[message.model_dump() for message in req.history[-20:]],
        {"role": "user", "content": req.message},
    ]
    response = requests.post(
        f"{settings.DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
        json={
            "model": settings.DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": settings.CHAT_MAX_OUTPUT_TOKENS,
        },
        timeout=settings.DEEPSEEK_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def _approved_bases(db: Session):
    return (
        db.query(ForestBase)
        .options(selectinload(ForestBase.media), selectinload(ForestBase.qualifications))
        .filter(ForestBase.status == "approved")
    )


@router.get("/miniapp/home", response_model=MiniAppHomeOut, summary="小程序首页聚合数据")
def miniapp_home(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """返回小程序首页所需的轮播、热门基地、功能入口及公开统计。"""
    hot_bases = _approved_bases(db).order_by(desc(ForestBase.view_count), desc(ForestBase.created_at)).limit(limit).all()
    banners = [
        {
            "id": f"base-{base.id}",
            "title": base.name,
            "subtitle": f"{base.province}{base.city} · 森林康养推荐",
            "image_url": _primary_image(base),
            "target_type": "base",
            "target_id": base.id,
            "target_url": f"/pages/base-detail/index?id={base.id}",
        }
        for base in hot_bases[:3]
    ]
    return {
        "banners": banners,
        "hot_bases": [_base_card(base, reason="热门浏览") for base in hot_bases],
        "feature_entries": [
            {"key": "recommend", "title": "基地推荐", "path": "/pages/recommend/index"},
            {"key": "map", "title": "地图导览", "path": "/pages/map/index"},
            {"key": "chat", "title": "智能咨询", "path": "/pages/chat/index"},
            {"key": "policies", "title": "康养资讯", "path": "/pages/articles/index"},
        ],
        "stats": {
            "bases_total": _approved_bases(db).count(),
            "policies_total": db.query(Policy).filter(Policy.status == "published").count(),
            "resources_total": db.query(NaturalResource).filter(NaturalResource.status == "published").count(),
            "experts_total": db.query(Expert).filter(Expert.status == "published").count(),
        },
    }


@router.get("/recommend", include_in_schema=False, deprecated=True)
@router.get("/miniapp/recommendations", response_model=RecommendationOut, summary="小程序基地推荐")
def recommend_bases(
    province: str | None = Query(None),
    city: str | None = Query(None),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius_km: float = Query(100, gt=0, le=1000, description="附近推荐半径（公里）"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """推荐按附近位置优先，否则按省市偏好和热度排序。

    不持久化用户定位数据；缺少经纬度时自然降级为热门推荐。
    """
    if (latitude is None) != (longitude is None):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="经纬度必须同时提供")

    query = _approved_bases(db)
    if province:
        query = query.filter(ForestBase.province == province)
    if city:
        query = query.filter(ForestBase.city == city)
    nearby = latitude is not None and longitude is not None
    cards: list[dict] = []
    if nearby:
        # 不能先按热度截断再计算距离，否则会漏掉真正最近的基地。
        bases = query.filter(
            ForestBase.latitude.is_not(None),
            ForestBase.longitude.is_not(None),
        ).all()
        for base in bases:
            distance = round(_distance_km(latitude, longitude, float(base.latitude), float(base.longitude)), 2)
            if distance <= radius_km:
                cards.append(_base_card(base, reason="附近推荐", distance_km=distance))
        cards.sort(key=lambda item: (item["distance_km"], -item["view_count"]))
    else:
        bases = query.order_by(desc(ForestBase.view_count), desc(ForestBase.created_at)).limit(limit).all()
        reason = "所在地推荐" if province or city else "热门推荐"
        cards = [_base_card(base, reason=reason) for base in bases]

    return {
        "items": cards[:limit],
        "recommendation_mode": "nearby" if nearby else ("location" if province or city else "popular"),
        "location_used": nearby,
        "radius_km": radius_km if nearby else None,
    }


@router.get("/map/bases", include_in_schema=False, deprecated=True)
@router.get("/miniapp/map/bases", response_model=MapBasesOut, summary="地图基地标记")
def map_bases(
    province: str | None = Query(None),
    city: str | None = Query(None),
    min_latitude: float | None = Query(None, ge=-90, le=90),
    max_latitude: float | None = Query(None, ge=-90, le=90),
    min_longitude: float | None = Query(None, ge=-180, le=180),
    max_longitude: float | None = Query(None, ge=-180, le=180),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = _approved_bases(db).filter(ForestBase.latitude.is_not(None), ForestBase.longitude.is_not(None))
    if province:
        query = query.filter(ForestBase.province == province)
    if city:
        query = query.filter(ForestBase.city == city)
    bounds = (min_latitude, max_latitude, min_longitude, max_longitude)
    if any(value is not None for value in bounds):
        if any(value is None for value in bounds):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="地图范围必须同时提供四个边界坐标")
        if min_latitude > max_latitude or min_longitude > max_longitude:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="地图范围坐标无效")
        query = query.filter(
            ForestBase.latitude.between(min_latitude, max_latitude),
            ForestBase.longitude.between(min_longitude, max_longitude),
        )
    total = query.count()
    bases = query.order_by(desc(ForestBase.view_count)).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [
            {
                "id": base.id,
                "name": base.name,
                "latitude": float(base.latitude),
                "longitude": float(base.longitude),
                "province": base.province,
                "city": base.city,
                "address": base.address,
                "primary_image": _primary_image(base),
            }
            for base in bases
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/chat", include_in_schema=False, deprecated=True)
@router.post("/miniapp/chat", response_model=MiniAppChatResponse, summary="小程序智能体对话")
def miniapp_chat(
    req: MiniAppChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """调用 DeepSeek 兼容接口，并按用户和来源限制成本暴露。"""
    rate_limiter.check(
        f"chat:{current_user.id}:{client_ip(request)}",
        settings.CHAT_RATE_LIMIT,
        settings.CHAT_RATE_WINDOW_SECONDS,
    )
    session_id = req.session_id or uuid4().hex
    if not settings.DEEPSEEK_API_KEY and settings.COZE_API_TOKEN:
        provider = "coze"
        try:
            reply = _chat_with_coze(req, session_id)
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
            reply = _local_chat_reply(req.message)
            provider = "local"

        return {
            "session_id": session_id,
            "reply": reply,
            "provider": provider,
            "suggestions": _QUICK_QUESTIONS,
            "disclaimer": "健康建议仅供参考，不替代医生诊断或治疗。",
        }
    if not settings.DEEPSEEK_API_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="智能咨询服务尚未配置")

    messages = [
        {
            "role": "system",
            "content": "你是森林康养平台助手。只提供一般性康养、基地筛选和平台使用建议；健康问题请提示用户咨询专业医生。回答简洁、友好，使用中文。",
        },
        *[message.model_dump() for message in req.history[-20:]],
        {"role": "user", "content": req.message},
    ]
    try:
        response = requests.post(
            f"{settings.DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            json={
                "model": settings.DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": settings.CHAT_MAX_OUTPUT_TOKENS,
            },
            timeout=settings.DEEPSEEK_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="智能咨询暂时不可用，请稍后重试") from exc

    return {
        "session_id": session_id,
        "reply": reply,
        "provider": "deepseek",
        "suggestions": _QUICK_QUESTIONS,
        "disclaimer": "健康建议仅供参考，不替代医生诊断或治疗。",
    }


@router.get("/bases/list", response_model=PaginatedBases, include_in_schema=False)
def legacy_miniapp_base_list(
    keyword: str | None = Query(None),
    province: str | None = Query(None),
    city: str | None = Query(None),
    district: str | None = Query(None),
    qual_level: str | None = Query(None),
    min_coverage: float | None = Query(None),
    max_coverage: float | None = Query(None),
    product_type: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """兼容设计文档 V1.0 中的 ``/api/bases/list`` 调用。"""
    return list_bases(keyword, province, city, district, qual_level, min_coverage, max_coverage, product_type, sort_by, sort_order, page, page_size, db)


@router.get("/bases/detail", include_in_schema=False)
def legacy_miniapp_base_detail(base_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    """兼容设计文档 V1.0 中的 ``/api/bases/detail?id=`` 调用。"""
    return get_base(base_id, db)
