"""微信小程序首页、推荐、地图与智能体接口。"""
from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.database import get_db
from app.models.base import ForestBase
from app.models.other import Expert, NaturalResource, Policy
from app.routers.bases import get_base, list_bases
from app.schemas.base import PaginatedBases
from app.schemas.miniapp import MiniAppChatRequest

router = APIRouter(prefix="/api", tags=["微信小程序"])
settings = get_settings()

_QUICK_QUESTIONS = [
    "推荐适合避暑的森林康养基地",
    "森林康养有哪些常见方式？",
    "如何根据所在城市筛选基地？",
]


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


def _approved_bases(db: Session):
    return (
        db.query(ForestBase)
        .options(selectinload(ForestBase.media), selectinload(ForestBase.qualifications))
        .filter(ForestBase.status == "approved")
    )


@router.get("/miniapp/home", summary="小程序首页聚合数据")
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


@router.get("/recommend", summary="小程序基地推荐")
def recommend_bases(
    province: str | None = Query(None),
    city: str | None = Query(None),
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """推荐按附近位置优先，否则按省市偏好和热度排序。

    不持久化用户定位数据；缺少经纬度时自然降级为热门推荐。
    """
    query = _approved_bases(db)
    if province:
        query = query.filter(ForestBase.province == province)
    if city:
        query = query.filter(ForestBase.city == city)
    bases = query.order_by(desc(ForestBase.view_count), desc(ForestBase.created_at)).limit(limit * 4).all()

    nearby = latitude is not None and longitude is not None
    cards: list[dict] = []
    for base in bases:
        distance = None
        if nearby and base.latitude is not None and base.longitude is not None:
            distance = round(_distance_km(latitude, longitude, float(base.latitude), float(base.longitude)), 2)
        reason = "附近推荐" if distance is not None else ("所在地推荐" if province or city else "热门推荐")
        cards.append(_base_card(base, reason=reason, distance_km=distance))
    if nearby:
        cards.sort(key=lambda item: (item["distance_km"] is None, item["distance_km"] or float("inf"), -item["view_count"]))

    return {
        "items": cards[:limit],
        "recommendation_mode": "nearby" if nearby else ("location" if province or city else "popular"),
        "location_used": nearby,
    }


@router.get("/map/bases", summary="地图基地标记")
def map_bases(
    province: str | None = Query(None),
    city: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = _approved_bases(db).filter(ForestBase.latitude.is_not(None), ForestBase.longitude.is_not(None))
    if province:
        query = query.filter(ForestBase.province == province)
    if city:
        query = query.filter(ForestBase.city == city)
    bases = query.order_by(desc(ForestBase.view_count)).limit(limit).all()
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
        ]
    }


@router.post("/chat", summary="小程序智能体对话")
def miniapp_chat(req: MiniAppChatRequest):
    """调用 DeepSeek 兼容接口；未配置密钥时返回可用的引导回复。"""
    session_id = req.session_id or uuid4().hex
    if not settings.DEEPSEEK_API_KEY:
        return {
            "session_id": session_id,
            "reply": "智能咨询服务尚未配置。你可以先使用基地查询、地图导览和热门推荐功能查找合适的森林康养基地。",
            "provider": "fallback",
            "suggestions": _QUICK_QUESTIONS,
            "disclaimer": "健康建议仅供参考，不替代医生诊断或治疗。",
        }

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
            json={"model": settings.DEEPSEEK_MODEL, "messages": messages, "temperature": 0.7},
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
