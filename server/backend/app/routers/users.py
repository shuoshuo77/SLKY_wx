"""
用户管理路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserVerification
from app.models.other import AuditLog, Notification
from app.schemas.user import (
    UserUpdate, ChangePassword, UserInfo, UserSimple,
    VerificationSubmit, VerificationReview, VerificationInfo,
    PaginatedUsers,
)
from app.dependencies.auth import get_current_user, get_current_admin, get_reviewer
from app.utils.security import hash_password, verify_password
from app.utils.scope import ensure_province_scope
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo.model_validate(current_user)


@router.put("/me", response_model=UserInfo, summary="更新当前用户信息")
def update_me(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return UserInfo.model_validate(current_user)


@router.put("/me/password", summary="修改密码")
def change_password(
    req: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")
    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "密码修改成功"}


@router.post("/me/verify", summary="提交认证申请")
def submit_verification(
    req: VerificationSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.verify_status in ("pending", "approved"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法重复提交认证")

    # 创建或更新认证记录
    v = db.query(UserVerification).filter(UserVerification.user_id == current_user.id).first()
    if v:
        v.org_name = req.org_name
        v.org_code = req.org_code
    else:
        v = UserVerification(user_id=current_user.id, org_name=req.org_name, org_code=req.org_code)
        db.add(v)

    current_user.verify_status = "pending"
    db.commit()
    return {"message": "认证申请已提交"}


@router.get("/me/verify", response_model=VerificationInfo, summary="查询认证状态")
def get_verification_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = db.query(UserVerification).filter(UserVerification.user_id == current_user.id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未提交认证")
    return VerificationInfo(
        id=v.id, user_id=v.user_id, org_name=v.org_name, org_code=v.org_code,
        verify_status=current_user.verify_status,
        verified_at=v.verified_at, reject_reason=v.reject_reason,
        created_at=v.created_at,
    )


# ===================== 管理员接口 =====================

@router.get("/", response_model=PaginatedUsers, summary="用户列表(管理员)")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None, description="用户名/姓名搜索"),
    verify_status: str = Query(None),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if keyword:
        q = q.filter(
            (User.username.contains(keyword)) | (User.real_name.contains(keyword))
        )
    if verify_status:
        q = q.filter(User.verify_status == verify_status)

    total = q.count()
    items = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedUsers(
        items=[UserSimple.model_validate(u) for u in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserInfo, summary="用户详情(管理员)")
def get_user(user_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return UserInfo.model_validate(user)


@router.put("/{user_id}/disable", summary="禁用用户(管理员)")
def disable_user(user_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.is_active = False
    db.commit()
    return {"message": "用户已禁用"}


@router.put("/{user_id}/enable", summary="启用用户(管理员)")
def enable_user(user_id: int, _: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    user.is_active = True
    db.commit()
    return {"message": "用户已启用"}


@router.post("/verify/{user_id}", summary="审核认证(管理员)")
def review_verification(
    user_id: int,
    req: VerificationReview,
    reviewer: User = Depends(get_reviewer),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    ensure_province_scope(reviewer, user.province)

    v = db.query(UserVerification).filter(UserVerification.user_id == user_id).first()
    if not v or user.verify_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户没有待审核的认证申请",
        )
    if req.action == "reject" and not req.reject_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="拒绝认证时必须填写原因",
        )

    if req.action == "approve":
        user.verify_status = "approved"
        user.user_type = "verified"
        v.reject_reason = None
    else:
        user.verify_status = "rejected"
        user.user_type = "regular"
        v.reject_reason = req.reject_reason

    v.verified_by = reviewer.id
    v.verified_at = datetime.now()
    db.add(AuditLog(
        target_type="user_verification",
        target_id=v.id,
        action=req.action,
        comment=req.reject_reason,
        reviewed_by=reviewer.id,
    ))
    db.add(Notification(
        user_id=user.id,
        title="认证审核结果",
        content=f"您的机构认证申请审核结果：{req.action}",
        notif_type="verification_review",
        link_url="/user/verification",
    ))

    db.commit()
    return {"message": f"认证{'通过' if req.action == 'approve' else '已拒绝'}"}
