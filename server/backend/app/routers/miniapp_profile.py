"""微信小程序个人中心：收藏、预约、浏览记录。"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.base import ForestBase
from app.models.other import BaseAppointment, BaseBrowseHistory, Favorite
from app.models.user import User
from app.schemas.miniapp import (
    AppointmentCreate,
    AppointmentListOut,
    AppointmentOut,
    AppointmentStatusUpdate,
    FavoriteBaseListOut,
    FavoriteMutationOut,
    HistoryClearOut,
    MiniAppStats,
    ViewRecordedOut,
)

router = APIRouter(prefix="/api/miniapp", tags=["微信小程序个人中心"])

MAX_HISTORY = 50
MAX_PEOPLE_PER_SLOT = 20
STATUS_LABELS = {
    "pending": "待确认",
    "confirmed": "已确认",
    "cancelled": "已取消",
    "rejected": "未通过",
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
        status_note=item.status_note,
        created_at=item.created_at,
    )


def _can_manage_appointments(base: ForestBase, current_user: User) -> bool:
    return base.submit_by == current_user.id or current_user.user_type in ("local_admin", "platform_admin")


def _managed_base(base_id: int, current_user: User, db: Session) -> ForestBase:
    base = db.query(ForestBase).filter(ForestBase.id == base_id).first()
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    if not _can_manage_appointments(base, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权管理该基地预约")
    return base


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


@router.get("/me/favorites", response_model=FavoriteBaseListOut, summary="我的收藏列表")
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


@router.put("/me/favorites/{base_id}", response_model=FavoriteMutationOut, summary="收藏基地")
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
        try:
            db.commit()
        except IntegrityError:
            # 并发收藏同一对象时保持 PUT 的幂等语义。
            db.rollback()
    return {"favorited": True}


@router.delete("/me/favorites/{base_id}", response_model=FavoriteMutationOut, summary="取消收藏")
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


@router.get("/me/appointments", response_model=AppointmentListOut, summary="我的预约列表")
def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.query(BaseAppointment).filter(BaseAppointment.user_id == current_user.id).count()
    rows = (
        db.query(BaseAppointment)
        .options(selectinload(BaseAppointment.base).selectinload(ForestBase.media))
        .filter(BaseAppointment.user_id == current_user.id)
        .order_by(BaseAppointment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": [_appointment_out(item) for item in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/me/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED, summary="提交预约")
def create_appointment(
    req: AppointmentCreate,
    response: Response,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key", min_length=8, max_length=128),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _approved_base(req.base_id, db)
    if req.visit_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="参访日期不能早于今天",
        )
    if idempotency_key:
        replay = (
            db.query(BaseAppointment)
            .options(selectinload(BaseAppointment.base).selectinload(ForestBase.media))
            .filter(
                BaseAppointment.user_id == current_user.id,
                BaseAppointment.idempotency_key == idempotency_key,
            )
            .first()
        )
        if replay:
            response.status_code = status.HTTP_200_OK
            return _appointment_out(replay)

    duplicate = (
        db.query(BaseAppointment)
        .filter(
            BaseAppointment.user_id == current_user.id,
            BaseAppointment.base_id == req.base_id,
            BaseAppointment.visit_date == req.visit_date,
            BaseAppointment.time_slot == req.time_slot,
            BaseAppointment.status.in_(("pending", "confirmed")),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该时段已有有效预约")

    occupied = (
        db.query(func.coalesce(func.sum(BaseAppointment.people_count), 0))
        .filter(
            BaseAppointment.base_id == req.base_id,
            BaseAppointment.visit_date == req.visit_date,
            BaseAppointment.time_slot == req.time_slot,
            BaseAppointment.status.in_(("pending", "confirmed")),
        )
        .scalar()
    )
    if int(occupied or 0) + req.people_count > MAX_PEOPLE_PER_SLOT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该时段剩余名额不足")

    item = BaseAppointment(
        user_id=current_user.id,
        base_id=req.base_id,
        visit_date=req.visit_date,
        time_slot=req.time_slot,
        people_count=req.people_count,
        contact_name=req.contact_name.strip(),
        contact_phone=req.contact_phone.strip(),
        status="pending",
        idempotency_key=idempotency_key,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
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
    if str(item.status) in ("cancelled", "rejected"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前预约不可取消")
    if str(item.status) != "cancelled":
        item.status = "cancelled"
        item.status_note = "用户取消"
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


@router.delete("/me/history", response_model=HistoryClearOut, summary="清空浏览记录")
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


@router.post("/bases/{base_id}/view", response_model=ViewRecordedOut, summary="记录基地浏览")
def record_view(
    base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _approved_base(base_id, db)

    history_item = (
        db.query(BaseBrowseHistory)
        .filter(BaseBrowseHistory.user_id == current_user.id, BaseBrowseHistory.base_id == base_id)
        .first()
    )
    if history_item:
        history_item.viewed_at = datetime.now()
    else:
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


@router.get("/bases/{base_id}/appointments", response_model=AppointmentListOut, summary="基地预约管理列表")
def list_base_appointments(
    base_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _managed_base(base_id, current_user, db)
    query = db.query(BaseAppointment).filter(BaseAppointment.base_id == base_id)
    total = query.count()
    rows = (
        query.options(selectinload(BaseAppointment.base).selectinload(ForestBase.media))
        .order_by(BaseAppointment.visit_date.asc(), BaseAppointment.time_slot.asc(), BaseAppointment.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": [_appointment_out(item) for item in rows], "total": total, "page": page, "page_size": page_size}


@router.patch("/appointments/{appointment_id}", response_model=AppointmentOut, summary="处理基地预约")
def update_appointment_status(
    appointment_id: int,
    req: AppointmentStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(BaseAppointment)
        .options(selectinload(BaseAppointment.base).selectinload(ForestBase.media))
        .filter(BaseAppointment.id == appointment_id)
        .with_for_update()
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    _managed_base(item.base_id, current_user, db)
    if str(item.status) in ("cancelled", "rejected"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已结束的预约不可再次处理")
    if req.action == "reject" and not req.note:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="拒绝预约时必须说明原因")
    next_status = {"confirm": "confirmed", "reject": "rejected", "cancel": "cancelled"}[req.action]
    item.status = next_status
    item.status_note = req.note.strip() if req.note else None
    db.commit()
    db.refresh(item)
    return _appointment_out(item)
