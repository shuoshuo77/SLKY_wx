"""
通用资源路由：政策、自然资源、行业数据、专家、公众需求
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_admin, get_optional_user, get_verified_user
from app.models.user import User
from app.models.other import (
    Policy, PolicyAttachment, NaturalResource, IndustryData,
    Expert, PublicDemand,
)
from app.schemas.other import (
    PolicyCreate, PolicyUpdate, PolicyOut, PolicyDetailOut, PaginatedPolicies,
    ResourceCreateReq, ResourceUpdateReq, NaturalResourceOut, PaginatedResources,
    IndustryDataCreate, IndustryDataUpdate, IndustryDataOut, PaginatedIndustry,
    ExpertCreate, ExpertUpdate, ExpertOut, PaginatedExperts,
    DemandCreate, DemandOut, PaginatedDemands,
)
from app.utils.scope import ensure_province_scope
from app.utils.html import sanitize_html

router = APIRouter(prefix="/api", tags=["通用资源"])

def _can_view_unpublished(item, user: User | None) -> bool:
    if not user:
        return False
    if item.submit_by == user.id or user.user_type == "platform_admin":
        return True
    if user.user_type == "local_admin" and hasattr(item, "province"):
        return bool(user.province and user.province == item.province)
    return False


def _prepare_resource_for_edit(item) -> None:
    if item.status == "pending":
        raise HTTPException(status_code=409, detail="待审核资源不可修改")
    if item.status == "archived":
        raise HTTPException(status_code=409, detail="已归档资源不可修改")
    if item.status == "published":
        item.status = "draft"
        item.reviewed_by = None
        item.reviewed_at = None
        item.reject_reason = None


# ===================== 政策标准 =====================

@router.get("/policies", response_model=PaginatedPolicies, summary="政策列表")
def list_policies(
    keyword: str = Query(None),
    policy_level: str = Query(None),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Policy).filter(Policy.status == "published")
    if keyword:
        q = q.filter(or_(Policy.title.contains(keyword), Policy.summary.contains(keyword)))
    if policy_level:
        q = q.filter(Policy.policy_level == policy_level)
    if category:
        q = q.filter(Policy.category == category)

    total = q.count()
    items = q.order_by(desc(Policy.publish_date)).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedPolicies(
        items=[PolicyOut.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/policies/{policy_id:int}", response_model=PolicyDetailOut, summary="政策详情")
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    p = db.query(Policy).filter(Policy.id == policy_id).first()
    if not p or (p.status != "published" and not _can_view_unpublished(p, current_user)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="政策不存在")
    p.view_count = (p.view_count or 0) + 1
    db.commit()
    return PolicyDetailOut.model_validate(p)


@router.post("/policies", response_model=PolicyDetailOut, status_code=201, summary="创建政策")
def create_policy(
    req: PolicyCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    data = req.model_dump(exclude_unset=True)
    data["content"] = sanitize_html(data.get("content"))
    policy = Policy(submit_by=current_user.id, **data)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return PolicyDetailOut.model_validate(policy)


@router.put("/policies/{policy_id:int}", response_model=PolicyDetailOut, summary="更新政策")
def update_policy(
    policy_id: int,
    req: PolicyUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    p = db.query(Policy).filter(Policy.id == policy_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="政策不存在")
    if p.submit_by != current_user.id and current_user.user_type != "platform_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改")
    _prepare_resource_for_edit(p)

    for field, value in req.model_dump(exclude_unset=True).items():
        if field == "content":
            value = sanitize_html(value)
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return PolicyDetailOut.model_validate(p)


@router.delete("/policies/{policy_id:int}", summary="删除政策")
def delete_policy(
    policy_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    p = db.query(Policy).filter(Policy.id == policy_id).first()
    if not p or (p.submit_by != current_user.id and current_user.user_type != "platform_admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="政策不存在或无权限")
    db.delete(p)
    db.commit()
    return {"message": "政策已删除"}


# ===================== 自然资源 =====================

@router.get("/resources", response_model=PaginatedResources, summary="自然资源列表")
def list_resources(
    keyword: str = Query(None),
    resource_type: str = Query(None),
    province: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(NaturalResource).filter(NaturalResource.status == "published")
    if keyword:
        q = q.filter(NaturalResource.name.contains(keyword))
    if resource_type:
        q = q.filter(NaturalResource.resource_type == resource_type)
    if province:
        q = q.filter(NaturalResource.province == province)

    total = q.count()
    items = q.order_by(desc(NaturalResource.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResources(
        items=[NaturalResourceOut.model_validate(r) for r in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/resources/{res_id:int}", response_model=NaturalResourceOut, summary="自然资源详情")
def get_resource(
    res_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    r = db.query(NaturalResource).filter(NaturalResource.id == res_id).first()
    if not r or (r.status != "published" and not _can_view_unpublished(r, current_user)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资源不存在")
    return NaturalResourceOut.model_validate(r)


@router.post("/resources", response_model=NaturalResourceOut, status_code=201, summary="创建自然资源")
def create_resource(
    req: ResourceCreateReq,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    ensure_province_scope(current_user, req.province)
    res = NaturalResource(submit_by=current_user.id, **req.model_dump(exclude_unset=True))
    db.add(res)
    db.commit()
    db.refresh(res)
    return NaturalResourceOut.model_validate(res)


@router.put("/resources/{res_id:int}", response_model=NaturalResourceOut, summary="更新自然资源")
def update_resource(
    res_id: int,
    req: ResourceUpdateReq,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    resource = db.query(NaturalResource).filter(NaturalResource.id == res_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="资源不存在")
    if resource.submit_by != current_user.id and current_user.user_type not in ("local_admin", "platform_admin"):
        raise HTTPException(status_code=403, detail="无权修改")
    ensure_province_scope(current_user, resource.province)
    values = req.model_dump(exclude_unset=True)
    target_province = values.get("province", resource.province)
    ensure_province_scope(current_user, target_province)
    _prepare_resource_for_edit(resource)
    for field, value in values.items():
        setattr(resource, field, value)
    db.commit()
    db.refresh(resource)
    return NaturalResourceOut.model_validate(resource)


# ===================== 行业数据 =====================

@router.get("/industry", response_model=PaginatedIndustry, summary="行业数据列表")
def list_industry(
    keyword: str = Query(None),
    data_type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(IndustryData).filter(IndustryData.status == "published")
    if keyword:
        q = q.filter(IndustryData.title.contains(keyword))
    if data_type:
        q = q.filter(IndustryData.data_type == data_type)

    total = q.count()
    items = q.order_by(desc(IndustryData.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedIndustry(
        items=[IndustryDataOut.model_validate(d) for d in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/industry/{data_id:int}", response_model=IndustryDataOut, summary="行业数据详情")
def get_industry(
    data_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    d = db.query(IndustryData).filter(IndustryData.id == data_id).first()
    if not d or (d.status != "published" and not _can_view_unpublished(d, current_user)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据不存在")
    d.view_count = (d.view_count or 0) + 1
    db.commit()
    return IndustryDataOut.model_validate(d)


@router.post("/industry", response_model=IndustryDataOut, status_code=201, summary="创建行业数据")
def create_industry(
    req: IndustryDataCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    values = req.model_dump(exclude_unset=True)
    values["content"] = sanitize_html(values.get("content"))
    data = IndustryData(submit_by=current_user.id, **values)
    db.add(data)
    db.commit()
    db.refresh(data)
    return IndustryDataOut.model_validate(data)


@router.put("/industry/{data_id:int}", response_model=IndustryDataOut, summary="更新行业数据")
def update_industry(
    data_id: int,
    req: IndustryDataUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    data = db.query(IndustryData).filter(IndustryData.id == data_id).first()
    if not data:
        raise HTTPException(status_code=404, detail="行业数据不存在")
    if data.submit_by != current_user.id and current_user.user_type != "platform_admin":
        raise HTTPException(status_code=403, detail="无权修改")
    _prepare_resource_for_edit(data)
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(data, field, sanitize_html(value) if field == "content" else value)
    db.commit()
    db.refresh(data)
    return IndustryDataOut.model_validate(data)


# ===================== 专家人才 =====================

@router.get("/experts", response_model=PaginatedExperts, summary="专家列表")
def list_experts(
    keyword: str = Query(None),
    specialty: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Expert).filter(Expert.status == "published")
    if keyword:
        q = q.filter(or_(Expert.name.contains(keyword), Expert.specialty.contains(keyword)))
    if specialty:
        q = q.filter(Expert.specialty.contains(specialty))

    total = q.count()
    items = q.order_by(desc(Expert.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    results = []
    for e in items:
        d = ExpertOut.model_validate(e)
        # 非公开联系方式的脱敏
        if not e.is_public:
            d.contact_phone = None
            d.contact_email = None
        results.append(d)

    return PaginatedExperts(items=results, total=total, page=page, page_size=page_size)


@router.get("/experts/{expert_id:int}", response_model=ExpertOut, summary="专家详情")
def get_expert(
    expert_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    e = db.query(Expert).filter(Expert.id == expert_id).first()
    if not e or (e.status != "published" and not _can_view_unpublished(e, current_user)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专家不存在")
    d = ExpertOut.model_validate(e)
    if not e.is_public:
        d.contact_phone = None
        d.contact_email = None
    return d


@router.post("/experts", response_model=ExpertOut, status_code=201, summary="创建专家")
def create_expert(
    req: ExpertCreate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    expert = Expert(submit_by=current_user.id, **req.model_dump(exclude_unset=True))
    db.add(expert)
    db.commit()
    db.refresh(expert)
    return ExpertOut.model_validate(expert)


@router.put("/experts/{expert_id:int}", response_model=ExpertOut, summary="更新专家")
def update_expert(
    expert_id: int,
    req: ExpertUpdate,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db),
):
    e = db.query(Expert).filter(Expert.id == expert_id).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="专家不存在")
    if e.submit_by != current_user.id and current_user.user_type != "platform_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改")
    _prepare_resource_for_edit(e)

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(e, field, value)
    db.commit()
    db.refresh(e)
    return ExpertOut.model_validate(e)


# ===================== 公众需求 =====================

@router.post("/demands", status_code=201, summary="提交需求")
def submit_demand(
    req: DemandCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    demand = PublicDemand(user_id=current_user.id, **req.model_dump(exclude_unset=True))
    db.add(demand)
    db.commit()
    return {"message": "需求已提交", "id": demand.id}


@router.get("/demands", response_model=PaginatedDemands, summary="需求列表(管理员)")
def list_demands(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(PublicDemand)
    total = q.count()
    items = q.order_by(desc(PublicDemand.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedDemands(
        items=[DemandOut.model_validate(d) for d in items],
        total=total, page=page, page_size=page_size,
    )
