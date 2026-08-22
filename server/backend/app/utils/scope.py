from fastapi import HTTPException, status

from app.models.user import User


def require_local_admin_province(user: User) -> str | None:
    if user.user_type != "local_admin":
        return None
    if not user.province:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="地方管理员未配置所属省份",
        )
    return user.province


def ensure_province_scope(user: User, province: str | None) -> None:
    local_province = require_local_admin_province(user)
    if local_province is not None and province != local_province:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="地方管理员只能操作所属省份的数据",
        )
