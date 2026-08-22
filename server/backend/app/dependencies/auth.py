"""
依赖注入：认证与权限
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.security import decode_access_token
from app.models.user import User

security_scheme = HTTPBearer()
optional_security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
        )

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式无效",
        )

    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌格式无效",
        )

    user = db.query(User).filter(User.id == parsed_user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return the active user when a valid bearer token is supplied."""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub") if payload else None
    if user_id is None:
        return None
    try:
        return db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    except (TypeError, ValueError):
        return None

def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求平台管理员权限"""
    if current_user.user_type != "platform_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要平台管理员权限",
        )
    return current_user


def get_reviewer(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求审核权限（地方管理员或平台管理员）"""
    if current_user.user_type not in ("local_admin", "platform_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要审核权限",
        )
    return current_user


def get_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求认证用户权限"""
    is_verified = (
        current_user.user_type == "verified"
        and current_user.verify_status == "approved"
    )
    is_admin = current_user.user_type in ("local_admin", "platform_admin")
    if not (is_verified or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要完成机构认证",
        )
    return current_user
