"""
认证路由：注册、登录
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserInfo
from app.utils.security import hash_password, verify_password, create_access_token
from app.config import get_settings
from app.utils.rate_limit import client_ip, rate_limiter

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse, summary="用户注册")
def register(request: Request, req: UserRegister, db: Session = Depends(get_db)):
    settings = get_settings()
    rate_limiter.check(
        f"register:{client_ip(request)}",
        settings.REGISTER_RATE_LIMIT,
        settings.REGISTER_RATE_WINDOW_SECONDS,
    )
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已被注册")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        phone=req.phone,
        email=req.email,
        real_name=req.real_name,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已被注册",
        )
    db.refresh(user)

    # 使用security.py中的create_access_token，sub传入字符串
    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(request: Request, req: UserLogin, db: Session = Depends(get_db)):
    settings = get_settings()
    rate_limiter.check(
        f"login:{client_ip(request)}:{req.username.casefold()}",
        settings.LOGIN_RATE_LIMIT,
        settings.LOGIN_RATE_WINDOW_SECONDS,
    )
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    from datetime import datetime
    user.last_login_at = datetime.now()
    db.commit()

    # 使用security.py中的create_access_token，sub传入字符串
    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))
