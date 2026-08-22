"""微信小程序个人中心：收藏、预约、浏览记录。"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.base import ForestBase
from app.models.other import BaseAppointment, BaseBrowseHistory, Favorite
from app.models.user import User
from app.schemas.miniapp import AppointmentCreate, AppointmentOut, MiniAppStats

router = APIRouter(prefix="/api/miniapp", tags=["微信小程序个人中心"])

MAX_HISTORY = 50
STATUS_LABELS = {
    "pending": "待确认",
    "confirmed": "已确认",
    "cancelled": "已取消",
}


def _primary_image(base: ForestBase) -> str | None:
    ordered = sorted(base.media, key=lambda item: item.sort_order)
    primary = next((item for item in ordered if item.is_primary), None)
    fallback = next((item for item in ordered if item.media_type == "image"), None)
    media = primary or fallback
    return media.file_url if media else None


def _base_summary(base: ForestBase) -> dict:
    return {
        "base_id": base.id,
        "base_name": base.name,
        "base_image": _primary_image(base),
        "area": "".join(filter(None, [base.province, base.city, base.district])),
        "province": base.province,
        "city": base.city,
        "district": base.district,
        "tags": [q.qual_level for q in base.qualifications if q.qual_level][:3],
        "view_count": base.view_count or 0,
    }


def _approved_base(base_id: int, db: Session) -> ForestBase:
    base = (
        db.query(ForestBase)
        .options(selectinload(ForestBase.media), selectinload(ForestBase.qualifications))
        .filter(ForestBase.id == base_id, ForestBase.status == "approved")
        .first()
    )
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    return base


def _appointment_out(item: BaseAppointment) -> AppointmentOut:
    return AppointmentOut(
        id=item.id,
        base_id=item.base_id,
        base_name=item.base.name,
        base_image=_primary_image(item.base),
        visit_date=item.visit_date,
        time_slot=item.time_slot,
        people_count=item.people_count,
        contact_name=item.contact_name,
        contact_phone=item.contact_phone,
        status=str(item.status),
        status_label=STATUS_LABELS.get(str(item.status), str(item.status)),
        created_at=item.created_at,
    )


@router.get("/me/stats", response_model=MiniAppStats, summary="个人中心统计")
def miniapp_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.fav_type == "base")
        .count()
    )
    appointments = (
        db.query(BaseAppointment)
        .filter(BaseAppointment.user_id == current_user.id, BaseAppointment.status != "cancelled")
        .count()
    )
    history = db.query(BaseBrowseHistory).filter(BaseBrowseHistory.user_id == current_user.id).count()
    return MiniAppStats(favorites=favorites, appointments=appointments, history=history)


@router.get("/me/favorites", summary="我的收藏列表")
def list_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Favorite, ForestBase)
        .join(ForestBase, ForestBase.id == Favorite.fav_id)
        .options(selectinload(ForestBase.media), selectinload(ForestBase.qualifications))
        .filter(Favorite.user_id == current_user.id, Favorite.fav_type == "base")
        .order_by(Favorite.created_at.desc())
        .all()
    )
    items = []
    for fav, base in rows:
        summary = _base_summary(base)
        summary["created_at"] = fav.created_at
        items.append(summary)
    return {"items": items}


@router.put("/me/favorites/{base_id}", summary="收藏基地")
def add_favorite(
    base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _approved_base(base_id, db)
    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == current_user.id,
            Favorite.fav_type == "base",
            Favorite.fav_id == base_id,
        )
        .first()
    )
    if not existing:
        db.add(Favorite(user_id=current_user.id, fav_type="base", fav_id=base_id))
        db.commit()
    return {"favorited": True}


@router.delete("/me/favorites/{base_id}", summary="取消收藏")
def remove_favorite(
    base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.fav_type == "base",
        Favorite.fav_id == base_id,
    ).delete(synchronize_session=False)
    db.commit()
    return {"favorited": False}


@router.get("/me/appointments", summary="我的预约列表")
def list_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(BaseAppointment)
        .options(selectinload(BaseAppointment.base).selectinload(ForestBase.media))
        .filter(BaseAppointment.user_id == current_user.id)
        .order_by(BaseAppointment.created_at.desc())
        .all()
    )
    return {"items": [_appointment_out(item) for item in rows]}


@router.post("/me/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED, summary="提交预约")
def create_appointment(
    req: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = _approved_base(req.base_id, db)
    if req.visit_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="参访日期不能早于今天",
        )
    item = BaseAppointment(
        user_id=current_user.id,
        base_id=req.base_id,
        visit_date=req.visit_date,
        time_slot=req.time_slot,
        people_count=req.people_count,
        contact_name=req.contact_name.strip(),
        contact_phone=req.contact_phone.strip(),
        status="pending",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    item.base = base
    return _appointment_out(item)


@router.post("/me/appointments/{appointment_id}/cancel", response_model=AppointmentOut, summary="取消预约")
def cancel_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(BaseAppointment)
        .options(selectinload(BaseAppointment.base).selectinload(ForestBase.media))
        .filter(
            BaseAppointment.id == appointment_id,
            BaseAppointment.user_id == current_user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    if str(item.status) != "cancelled":
        item.status = "cancelled"
        db.commit()
        db.refresh(item)
    return _appointment_out(item)


@router.get("/me/history", summary="浏览记录")
def list_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(BaseBrowseHistory)
        .options(selectinload(BaseBrowseHistory.base).selectinload(ForestBase.media))
        .filter(BaseBrowseHistory.user_id == current_user.id)
        .order_by(BaseBrowseHistory.viewed_at.desc())
        .limit(MAX_HISTORY)
        .all()
    )
    items = []
    for item in rows:
        summary = _base_summary(item.base)
        summary["viewed_at"] = item.viewed_at
        items.append(summary)
    return {"items": items}


@router.delete("/me/history", summary="清空浏览记录")
def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(BaseBrowseHistory)
        .filter(BaseBrowseHistory.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"cleared": deleted}


@router.post("/bases/{base_id}/view", summary="记录基地浏览")
def record_view(
    base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _approved_base(base_id, db)

    db.query(BaseBrowseHistory).filter(
        BaseBrowseHistory.user_id == current_user.id,
        BaseBrowseHistory.base_id == base_id,
    ).delete(synchronize_session=False)
    db.add(BaseBrowseHistory(user_id=current_user.id, base_id=base_id, viewed_at=datetime.now()))

    db.query(ForestBase).filter(ForestBase.id == base_id).update(
        {ForestBase.view_count: ForestBase.view_count + 1}
    )

    stale = (
        db.query(BaseBrowseHistory.id)
        .filter(BaseBrowseHistory.user_id == current_user.id)
        .order_by(BaseBrowseHistory.viewed_at.desc())
        .offset(MAX_HISTORY)
        .all()
    )
    if stale:
        db.query(BaseBrowseHistory).filter(
            BaseBrowseHistory.id.in_([row[0] for row in stale])
        ).delete(synchronize_session=False)

    db.commit()
    return {"recorded": True}
