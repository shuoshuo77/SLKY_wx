"""
全国森林康养信息收集平台 — FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.database import engine

# 必须在注册路由之前导入所有模型，否则 SQLAlchemy 无法解析
# relationship 中的字符串类名（如 "ForestBase"）
from app import models  # noqa: F401

from app.routers import (
    auth,
    users,
    bases,
    resources,
    resource_workflow,
    common,
    articles,
    health,
    home,
    miniapp,
    miniapp_profile,
)
from app.middleware import request_context_middleware

settings = get_settings()

# 确保上传目录在挂载静态文件前存在（StaticFiles 要求目录必须存在）
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # Schema upgrades are applied by Alembic before the server starts.
    yield
    # 关闭时：清理资源
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="全国森林康养基地信息全面采集、规范录入、智能管理与可视化共享平台",
    lifespan=lifespan,
)
app.middleware("http")(request_context_middleware)

# CORS 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件（上传目录）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(bases.router)
app.include_router(resources.router)
app.include_router(resource_workflow.router)
app.include_router(common.router)
app.include_router(articles.router)
app.include_router(health.router)
app.include_router(home.router)
app.include_router(miniapp.router)
app.include_router(miniapp_profile.router)


@app.get("/", tags=["系统"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/api/stats", tags=["系统"], summary="平台统计概览")
def platform_stats():
    """返回平台基础统计（用于首页数据概览）"""
    from sqlalchemy import func
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models.base import ForestBase
    from app.models.other import Policy, NaturalResource, Expert
    from app.models.user import User

    db: Session = SessionLocal()
    try:
        return {
            "bases_total": db.query(func.count(ForestBase.id)).filter(ForestBase.status == "approved").scalar(),
            "policies_total": db.query(func.count(Policy.id)).filter(Policy.status == "published").scalar(),
            "resources_total": db.query(func.count(NaturalResource.id)).filter(NaturalResource.status == "published").scalar(),
            "experts_total": db.query(func.count(Expert.id)).filter(Expert.status == "published").scalar(),
            "users_total": db.query(func.count(User.id)).scalar(),
            "bases_by_province": [
                {"province": r[0], "count": r[1]}
                for r in db.query(ForestBase.province, func.count(ForestBase.id))
                .filter(ForestBase.status == "approved")
                .group_by(ForestBase.province)
                .all()
            ],
        }
    finally:
        db.close()
