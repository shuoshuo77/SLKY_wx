"""
收藏、通知、文件上传 路由
"""
import asyncio
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.other import Favorite, Notification
from app.schemas.other import (
    FavoriteCreate, FavoriteOut, NotificationOut, PaginatedNotifications,
)
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api", tags=["通用功能"])


# ===================== 收藏 =====================

@router.get("/favorites", response_model=list[FavoriteOut], summary="我的收藏")
def list_favorites(
    fav_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Favorite).filter(Favorite.user_id == current_user.id)
    if fav_type:
        q = q.filter(Favorite.fav_type == fav_type)
    return [FavoriteOut.model_validate(f) for f in q.order_by(desc(Favorite.created_at)).all()]


@router.post("/favorites", status_code=201, summary="添加收藏")
def add_favorite(
    req: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.fav_type == req.fav_type,
        Favorite.fav_id == req.fav_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="已收藏")

    fav = Favorite(user_id=current_user.id, fav_type=req.fav_type, fav_id=req.fav_id)
    db.add(fav)
    db.commit()
    return {"message": "收藏成功", "id": fav.id}


@router.post("/favorites/{fav_id}/toggle", summary="切换收藏(收藏/取消)")
def toggle_favorite(
    fav_id: int,
    req: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.fav_type == req.fav_type,
        Favorite.fav_id == req.fav_id,
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "已取消收藏", "favorited": False}
    else:
        fav = Favorite(user_id=current_user.id, fav_type=req.fav_type, fav_id=req.fav_id)
        db.add(fav)
        db.commit()
        return {"message": "收藏成功", "favorited": True}


# ===================== 通知 =====================

@router.get("/notifications", response_model=PaginatedNotifications, summary="我的通知")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Notification).filter(Notification.user_id == current_user.id)
    total = q.count()
    unread = q.filter(Notification.is_read == False).count()
    items = q.order_by(desc(Notification.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedNotifications(
        items=[NotificationOut.model_validate(n) for n in items],
        total=total, unread_count=unread, page=page, page_size=page_size,
    )


@router.put("/notifications/read-all", summary="全部标记已读")
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "已全部标记为已读"}


@router.put("/notifications/{notif_id}/read", summary="标记已读")
def read_notification(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id, Notification.user_id == current_user.id
    ).first()
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    n.is_read = True
    db.commit()
    return {"message": "已标记已读"}


# ===================== 文件上传 =====================

@router.post("/upload", summary="文件上传")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    content_type = (file.content_type or "").lower()
    if ext not in settings.allowed_upload_extensions:
        raise HTTPException(status_code=415, detail="不支持的文件扩展名")
    if content_type not in settings.allowed_upload_mime_types:
        raise HTTPException(status_code=415, detail="不支持的文件类型")

    header = await file.read(16)
    signatures = {
        ".jpg": (b"\xff\xd8\xff",),
        ".jpeg": (b"\xff\xd8\xff",),
        ".png": (b"\x89PNG\r\n\x1a\n",),
        ".webp": (b"RIFF",),
        ".pdf": (b"%PDF-",),
    }
    valid_signature = any(header.startswith(prefix) for prefix in signatures[ext])
    if ext == ".webp":
        valid_signature = header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    if not valid_signature:
        raise HTTPException(status_code=415, detail="文件内容与声明类型不符")
    await file.seek(0)

    new_name = f"{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, new_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    size = 0
    try:
        with open(save_path, "wb") as output:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE:
                    raise HTTPException(status_code=413, detail="文件大小超出限制")
                await asyncio.to_thread(output.write, chunk)
    except Exception:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise

    if size == 0:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=400, detail="文件不能为空")

    return {
        "url": f"/uploads/{new_name}",
        "filename": file.filename,
        "size": size,
    }