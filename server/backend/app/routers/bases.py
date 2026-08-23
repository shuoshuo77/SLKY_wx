"""
森林康养基地核心API路由 — CRUD + 审核 + 筛选查询
"""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, asc, func, select

from app.database import get_db
from app.dependencies.auth import get_current_user, get_reviewer, get_verified_user
from app.models.user import User
from app.models.other import AuditLog, Notification
from app.models.base import (
    ForestBase, BaseQualification, BaseResource, BaseBusiness,
    BaseOperation, BaseMedia, BaseContact,
)
from app.schemas.base import (
    BaseCreate, BaseUpdate, BaseListOut, BaseDetailOut, PublicBaseDetailOut, BaseReview,
    PaginatedBases, BaseQuery,
    QualificationCreate, ResourceCreate, BusinessCreate,
    OperationCreate, ContactCreate, MediaCreate,
)
from app.utils.scope import ensure_province_scope, require_local_admin_province

router = APIRouter(prefix="/api/bases", tags=["康养基地"])

SORT_COLUMNS = {
    "created_at": ForestBase.created_at,
    "updated_at": ForestBase.updated_at,
    "view_count": ForestBase.view_count,
    "forest_coverage": ForestBase.forest_coverage,
    "name": ForestBase.name,
}


def _base_load_options():
    return (
        selectinload(ForestBase.qualifications),
        selectinload(ForestBase.resources),
        selectinload(ForestBase.business),
        selectinload(ForestBase.operations),
        selectinload(ForestBase.media),
        selectinload(ForestBase.contacts),
    )


def _attach_relations(base: ForestBase, db: Session):
    """Relationships are loaded in batches by the caller."""
    return base


def _get_primary_image(base: ForestBase) -> str | None:
    """Return the primary image without issuing another query."""
    ordered_media = sorted(base.media, key=lambda item: item.sort_order)
    primary = next((item for item in ordered_media if item.is_primary), None)
    fallback = next((item for item in ordered_media if item.media_type == "image"), None)
    media = primary or fallback
    return media.file_url if media else None


def _ensure_reviewer_scope(base: ForestBase, reviewer: User) -> None:
    ensure_province_scope(reviewer, base.province)


def _public_detail(base: ForestBase) -> PublicBaseDetailOut:
    """Build a visitor-safe response without ownership, review, or contact PII."""
    return PublicBaseDetailOut(
        id=base.id,
        name=base.name,
        province=base.province,
        city=base.city,
        district=base.district,
        address=base.address,
        longitude=base.longitude,
        latitude=base.latitude,
        established_date=base.established_date,
        total_area=base.total_area,
        forest_coverage=base.forest_coverage,
        description=base.description,
        tags=base.tags,
        view_count=base.view_count or 0,
        updated_at=base.updated_at,
        qualifications=[
            {
                "qual_level": item.qual_level,
                "qual_name": item.qual_name,
                "issuing_authority": item.issuing_authority,
                "issue_date": item.issue_date,
                "valid_until": item.valid_until,
            }
            for item in base.qualifications
        ],
        resources=base.resources,
        business=base.business,
        operations=base.operations,
        media=[item for item in base.media if item.media_type in ("image", "video")],
    )


def _prepare_base_for_edit(base: ForestBase) -> None:
    if base.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="待审核基地不可修改，请等待审核结果",
        )
    if base.status == "approved":
        base.status = "draft"
        base.reviewed_by = None
        base.reviewed_at = None
        base.reject_reason = None

# ===================== 公开接口 =====================

@router.get("", response_model=PaginatedBases, include_in_schema=False)
@router.get("/", response_model=PaginatedBases, summary="基地列表(公开)")
def list_bases(
    keyword: str = Query(None, description="名称/地址搜索"),
    province: str = Query(None),
    city: str = Query(None),
    district: str = Query(None),
    qual_level: str = Query(None, description="资质等级: 国家级/省级/市级"),
    min_coverage: float = Query(None, description="最低森林覆盖率"),
    max_coverage: float = Query(None, description="最高森林覆盖率"),
    product_type: str = Query(None, description="康养产品类型"),
    sort_by: Literal["created_at", "updated_at", "view_count", "forest_coverage", "name"] = Query("created_at"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # 基础筛选：只展示已发布
    q = db.query(ForestBase).options(selectinload(ForestBase.media)).filter(ForestBase.status == "approved")

    # 关键词搜索
    if keyword:
        q = q.filter(
            or_(
                ForestBase.name.contains(keyword),
                ForestBase.address.contains(keyword),
                ForestBase.description.contains(keyword),
            )
        )

    if province:
        q = q.filter(ForestBase.province == province)
    if city:
        q = q.filter(ForestBase.city == city)
    if district:
        q = q.filter(ForestBase.district == district)

    if min_coverage is not None:
        q = q.filter(ForestBase.forest_coverage >= min_coverage)
    if max_coverage is not None:
        q = q.filter(ForestBase.forest_coverage <= max_coverage)

    # 按资质等级筛选（联表）
    needs_distinct = False
    if qual_level:
        q = q.join(BaseQualification).filter(BaseQualification.qual_level == qual_level)
        needs_distinct = True

    # 按产品类型筛选（JSON查询，仅MySQL 5.7+支持）
    if product_type:
        q = q.join(BaseBusiness)
        if db.bind.dialect.name == "sqlite":
            product_values = func.json_each(BaseBusiness.product_types).table_valued("value").alias("product_values")
            q = q.filter(
                select(1)
                .select_from(product_values)
                .where(product_values.c.value == product_type)
                .exists()
            )
        else:
            q = q.filter(func.json_contains(BaseBusiness.product_types, f'"{product_type}"'))
        needs_distinct = True

    if needs_distinct:
        q = q.distinct()

    # 排序
    sort_col = SORT_COLUMNS[sort_by]
    q = q.order_by(desc(sort_col) if sort_order == "desc" else asc(sort_col))

    total = q.count()
    bases = q.offset((page - 1) * page_size).limit(page_size).all()

    # 构造列表响应（带主图）
    items = []
    for b in bases:
        entry = BaseListOut.model_validate(b)
        entry.primary_image = _get_primary_image(b)
        items.append(entry)

    return PaginatedBases(items=items, total=total, page=page, page_size=page_size)


@router.get("/provinces", summary="省份列表")
def list_provinces(db: Session = Depends(get_db)):
    rows = (
        db.query(ForestBase.province, func.count(ForestBase.id))
        .filter(ForestBase.status == "approved")
        .group_by(ForestBase.province)
        .order_by(ForestBase.province)
        .all()
    )
    return [{"province": r[0], "count": r[1]} for r in rows]


@router.get("/cities", summary="城市列表")
def list_cities(
    province: str = Query(..., min_length=1, description="省份名称"),
    db: Session = Depends(get_db),
):
    """返回指定省份中已有已发布基地的去重城市列表。"""
    rows = (
        db.query(ForestBase.city, func.count(ForestBase.id))
        .filter(
            ForestBase.status == "approved",
            ForestBase.province == province,
        )
        .group_by(ForestBase.city)
        .order_by(ForestBase.city)
        .all()
    )
    return [{"city": row[0], "count": row[1]} for row in rows]


@router.get("/{base_id:int}", response_model=PublicBaseDetailOut, summary="基地详情（公开）")
def get_base(base_id: int, db: Session = Depends(get_db)):
    base = db.query(ForestBase).options(*_base_load_options()).filter(ForestBase.id == base_id).first()
    if not base or base.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")

    # GET 必须保持无副作用；浏览量由 /api/miniapp/bases/{id}/view 显式记录。
    return _public_detail(base)


@router.get("/{base_id:int}/manage", response_model=BaseDetailOut, summary="基地详情（管理）")
def get_manage_base(
    base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = db.query(ForestBase).options(*_base_load_options()).filter(ForestBase.id == base_id).first()
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    if base.submit_by != current_user.id and current_user.user_type not in ("local_admin", "platform_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看管理详情")
    ensure_province_scope(current_user, base.province)
    return BaseDetailOut.model_validate(base)


# ===================== 认证用户接口 =====================

@router.post("/", response_model=BaseDetailOut, status_code=status.HTTP_201_CREATED, summary="创建基地")
def create_base(
    req: BaseCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    base = ForestBase(
        name=req.name,
        province=req.province,
        city=req.city,
        district=req.district,
        address=req.address,
        longitude=req.longitude,
        latitude=req.latitude,
        established_date=req.established_date,
        total_area=req.total_area,
        forest_coverage=req.forest_coverage,
        description=req.description,
        submit_by=current_user.id,
        status="draft",
    )
    db.add(base)
    db.flush()  # 获取 base.id

    # 创建子表
    if req.qualifications:
        for q in req.qualifications:
            db.add(BaseQualification(base_id=base.id, **q.model_dump(exclude_unset=True)))
    if req.resources:
        db.add(BaseResource(base_id=base.id, **req.resources.model_dump(exclude_unset=True)))
    if req.business:
        db.add(BaseBusiness(base_id=base.id, **req.business.model_dump(exclude_unset=True)))
    if req.operations:
        db.add(BaseOperation(base_id=base.id, **req.operations.model_dump(exclude_unset=True)))
    if req.contacts:
        for c in req.contacts:
            db.add(BaseContact(base_id=base.id, **c.model_dump(exclude_unset=True)))

    db.commit()
    db.refresh(base)
    return BaseDetailOut.model_validate(_attach_relations(base, db))


@router.put("/{base_id:int}", response_model=BaseDetailOut, summary="更新基地")
def update_base(
    base_id: int,
    req: BaseUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    base = db.query(ForestBase).options(*_base_load_options()).filter(ForestBase.id == base_id).first()
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    if base.submit_by != current_user.id and current_user.user_type not in ("local_admin", "platform_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改")
    ensure_province_scope(current_user, base.province)

    _prepare_base_for_edit(base)

    nested_fields = {"qualifications", "resources", "business", "operations", "contacts"}
    for field, value in req.model_dump(exclude_unset=True, exclude=nested_fields).items():
        setattr(base, field, value)

    # 嵌套字段采用“传入即整体替换、未传即保留”的明确契约，避免编辑页静默丢失数据。
    if "qualifications" in req.model_fields_set:
        base.qualifications[:] = []
        for item in req.qualifications or []:
            base.qualifications.append(BaseQualification(**item.model_dump(exclude_unset=True)))
    if "resources" in req.model_fields_set:
        base.resources = BaseResource(**req.resources.model_dump(exclude_unset=True)) if req.resources else None
    if "business" in req.model_fields_set:
        base.business = BaseBusiness(**req.business.model_dump(exclude_unset=True)) if req.business else None
    if "operations" in req.model_fields_set:
        base.operations = BaseOperation(**req.operations.model_dump(exclude_unset=True)) if req.operations else None
    if "contacts" in req.model_fields_set:
        base.contacts[:] = []
        for item in req.contacts or []:
            base.contacts.append(BaseContact(**item.model_dump(exclude_unset=True)))

    db.commit()
    db.refresh(base)
    return BaseDetailOut.model_validate(_attach_relations(base, db))


@router.delete("/{base_id:int}", summary="删除基地")
def delete_base(
    base_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    base = db.query(ForestBase).options(*_base_load_options()).filter(ForestBase.id == base_id).first()
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    if base.submit_by != current_user.id and current_user.user_type not in ("local_admin", "platform_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除")
    ensure_province_scope(current_user, base.province)

    db.delete(base)
    db.commit()
    return {"message": "基地已删除"}


@router.post("/{base_id:int}/submit", summary="提交审核")
def submit_for_review(
    base_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    base = db.query(ForestBase).options(*_base_load_options()).filter(ForestBase.id == base_id).first()
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    if base.submit_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")
    if base.status not in ("draft", "rejected"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可提交")

    base.status = "pending"
    db.add(AuditLog(
        target_type="base",
        target_id=base.id,
        action="submit",
        comment=None,
        reviewed_by=current_user.id,
    ))
    db.commit()
    return {"message": "已提交审核"}


@router.get("/my/list", response_model=PaginatedBases, summary="我提交的基地")
def my_bases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    q = db.query(ForestBase).options(selectinload(ForestBase.media)).filter(ForestBase.submit_by == current_user.id)
    if status:
        q = q.filter(ForestBase.status == status)

    total = q.count()
    bases = q.order_by(ForestBase.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for b in bases:
        entry = BaseListOut.model_validate(b)
        entry.primary_image = _get_primary_image(b)
        items.append(entry)

    return PaginatedBases(items=items, total=total, page=page, page_size=page_size)


# ===================== 审核接口 =====================

@router.get("/review/list", response_model=PaginatedBases, summary="待审核列表")
def review_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    reviewer: User = Depends(get_reviewer),
    db: Session = Depends(get_db),
):
    q = db.query(ForestBase).options(selectinload(ForestBase.media)).filter(ForestBase.status == "pending")
    if reviewer.user_type == "local_admin":
        q = q.filter(ForestBase.province == require_local_admin_province(reviewer))
    total = q.count()
    bases = q.order_by(ForestBase.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for b in bases:
        entry = BaseListOut.model_validate(b)
        entry.primary_image = _get_primary_image(b)
        items.append(entry)

    return PaginatedBases(items=items, total=total, page=page, page_size=page_size)


@router.post("/{base_id:int}/review", summary="审核基地")
def review_base(
    base_id: int,
    req: BaseReview,
    reviewer: User = Depends(get_reviewer),
    db: Session = Depends(get_db),
):
    base = (
        db.query(ForestBase)
        .options(*_base_load_options())
        .filter(ForestBase.id == base_id)
        .with_for_update()
        .first()
    )
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    if base.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可审核")
    _ensure_reviewer_scope(base, reviewer)
    if req.action == "reject" and not req.reject_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="拒绝基地时必须填写原因",
        )

    if req.action == "approve":
        base.status = "approved"
        base.reject_reason = None
    elif req.action == "reject":
        base.status = "rejected"
        base.reject_reason = req.reject_reason
    elif req.action == "archive":
        base.status = "archived"

    base.reviewed_by = reviewer.id
    base.reviewed_at = datetime.now()
    db.add(AuditLog(
        target_type="base",
        target_id=base.id,
        action=req.action,
        comment=req.reject_reason,
        reviewed_by=reviewer.id,
    ))
    db.add(Notification(
        user_id=base.submit_by,
        title="基地审核结果",
        content=f"您提交的基地“{base.name}”审核结果：{req.action}",
        notif_type="base_review",
        link_url=f"/bases/{base.id}",
    ))
    db.commit()

    return {"message": f"审核完成: {req.action}"}


# ===================== 子表管理 =====================

@router.post("/{base_id:int}/media", summary="添加素材")
def add_media(
    base_id: int,
    req: MediaCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    base = db.query(ForestBase).options(*_base_load_options()).filter(ForestBase.id == base_id).first()
    if not base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="基地不存在")
    if base.submit_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    _prepare_base_for_edit(base)

    media = BaseMedia(base_id=base_id, **req.model_dump(exclude_unset=True))
    db.add(media)
    db.commit()
    return {"message": "素材已添加", "id": media.id}


@router.delete("/{base_id:int}/media/{media_id:int}", summary="删除素材")
def delete_media(
    base_id: int,
    media_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    media = db.query(BaseMedia).filter(
        BaseMedia.id == media_id, BaseMedia.base_id == base_id
    ).first()
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="素材不存在")

    base = db.query(ForestBase).options(*_base_load_options()).filter(ForestBase.id == base_id).first()
    if base.submit_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    _prepare_base_for_edit(base)

    db.delete(media)
    db.commit()
    return {"message": "素材已删除"}
