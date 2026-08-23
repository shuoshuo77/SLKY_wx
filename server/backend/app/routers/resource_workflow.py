from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_reviewer, get_verified_user
from app.models.other import (
    AuditLog,
    Expert,
    IndustryData,
    NaturalResource,
    Notification,
    Policy,
)
from app.models.user import User
from app.schemas.other import ResourceReview
from app.utils.scope import ensure_province_scope, require_local_admin_province


router = APIRouter(prefix="/api/resource-workflows", tags=["资源审核"])

RESOURCE_MODELS = {
    "policy": Policy,
    "natural_resource": NaturalResource,
    "industry_data": IndustryData,
    "expert": Expert,
}


def _model_for(resource_type: str):
    model = RESOURCE_MODELS.get(resource_type)
    if model is None:
        raise HTTPException(status_code=404, detail="资源类型不存在")
    return model


def _ensure_review_scope(user: User, item) -> None:
    if user.user_type != "local_admin":
        return
    if not isinstance(item, NaturalResource):
        raise HTTPException(status_code=403, detail="地方管理员只能审核本省自然资源")
    ensure_province_scope(user, item.province)


def _item_summary(resource_type: str, item) -> dict:
    return {
        "resource_type": resource_type,
        "id": item.id,
        "title": getattr(item, "title", None) or getattr(item, "name", None),
        "province": getattr(item, "province", None),
        "status": item.status,
        "submit_by": item.submit_by,
        "created_at": item.created_at,
        "reject_reason": item.reject_reason,
    }


@router.post("/{resource_type}/{item_id:int}/submit")
def submit_resource(
    resource_type: str,
    item_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    model = _model_for(resource_type)
    item = db.query(model).filter(model.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="资源不存在")
    if item.submit_by != current_user.id:
        raise HTTPException(status_code=403, detail="只能提交本人创建的资源")
    if item.status not in ("draft", "rejected"):
        raise HTTPException(status_code=409, detail="当前状态不可提交")

    item.status = "pending"
    item.reviewed_by = None
    item.reviewed_at = None
    item.reject_reason = None
    db.add(AuditLog(
        target_type=resource_type,
        target_id=item.id,
        action="submit",
        reviewed_by=current_user.id,
    ))
    db.commit()
    return _item_summary(resource_type, item)


@router.get("/{resource_type}/pending")
def pending_resources(
    resource_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reviewer: User = Depends(get_reviewer),
    db: Session = Depends(get_db),
):
    model = _model_for(resource_type)
    query = db.query(model).filter(model.status == "pending")
    if reviewer.user_type == "local_admin":
        if model is not NaturalResource:
            raise HTTPException(status_code=403, detail="地方管理员只能审核本省自然资源")
        query = query.filter(model.province == require_local_admin_province(reviewer))
    total = query.count()
    items = query.order_by(model.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_item_summary(resource_type, item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{resource_type}/{item_id:int}/review")
def review_resource(
    resource_type: str,
    item_id: int,
    request: ResourceReview,
    reviewer: User = Depends(get_reviewer),
    db: Session = Depends(get_db),
):
    model = _model_for(resource_type)
    item = db.query(model).filter(model.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="资源不存在")
    _ensure_review_scope(reviewer, item)
    if item.status != "pending":
        raise HTTPException(status_code=409, detail="资源已被处理或尚未提交")
    if request.action == "reject" and not request.reject_reason:
        raise HTTPException(status_code=422, detail="拒绝时必须填写原因")

    item.status = "published" if request.action == "approve" else "rejected"
    item.reviewed_by = reviewer.id
    item.reviewed_at = datetime.now()
    item.reject_reason = request.reject_reason if request.action == "reject" else None
    db.add(AuditLog(
        target_type=resource_type,
        target_id=item.id,
        action=request.action,
        comment=request.reject_reason,
        reviewed_by=reviewer.id,
    ))
    db.add(Notification(
        user_id=item.submit_by,
        title="资源审核结果",
        content=f"您提交的资源审核结果：{request.action}",
        notif_type="resource_review",
    ))
    db.commit()
    return _item_summary(resource_type, item)


@router.post("/{resource_type}/{item_id:int}/archive")
def archive_resource(
    resource_type: str,
    item_id: int,
    reviewer: User = Depends(get_reviewer),
    db: Session = Depends(get_db),
):
    model = _model_for(resource_type)
    item = db.query(model).filter(model.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(status_code=404, detail="资源不存在")
    _ensure_review_scope(reviewer, item)
    if item.status != "published":
        raise HTTPException(status_code=409, detail="只有已发布资源可以归档")
    item.status = "archived"
    item.reviewed_by = reviewer.id
    item.reviewed_at = datetime.now()
    db.add(AuditLog(
        target_type=resource_type,
        target_id=item.id,
        action="archive",
        reviewed_by=reviewer.id,
    ))
    db.commit()
    return _item_summary(resource_type, item)
