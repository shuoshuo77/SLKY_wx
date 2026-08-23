"""
文章采集管理 API
=================
- 文章列表 / 详情 / 搜索 / 审核
- 数据源管理（增删改查）
- 关键词词库管理
- 爬取任务触发 / 状态查询
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func

from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user, get_reviewer
from app.models.user import User
from app.models.article import (
    CrawlSource, CrawlKeyword, CrawlArticle, CrawlArticleImage,
    CrawlTask, CrawlArticleBaseLink,
)
from app.schemas.article import (
    # Source
    SourceCreate, SourceUpdate, SourceOut, SourceListOut,
    # Keyword
    KeywordCreate, KeywordOut, KeywordListOut,
    # Article
    ArticleOut, ArticleListOut, ArticleDetailOut, ArticleReview,
    # Task
    TaskOut, TaskListOut,
)
from app.schemas.common import PaginationParams, PaginatedResponse
from app.utils.scope import ensure_province_scope, require_local_admin_province
from app.utils.html import sanitize_html

router = APIRouter(prefix="/api/articles", tags=["文章采集"])


# =====================================================================
# 数据源管理
# =====================================================================
@router.get("/sources", response_model=SourceListOut, summary="数据源列表")
def list_sources(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    query = db.query(CrawlSource)
    if category:
        query = query.filter(CrawlSource.category == category)
    if is_active is not None:
        query = query.filter(CrawlSource.is_active == is_active)

    sources = query.order_by(desc(CrawlSource.created_at)).all()
    return {
        "total": len(sources),
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "source_type": s.source_type,
                "category": s.category,
                "oa_name": s.oa_name,
                "base_url": s.base_url,
                "region": s.region,
                "org_name": s.org_name,
                "description": s.description,
                "is_active": s.is_active,
                "crawl_frequency": s.crawl_frequency,
                "last_crawl_at": s.last_crawl_at.isoformat() if s.last_crawl_at else None,
                "last_article_count": s.last_article_count,
                "total_articles": s.total_articles,
                "robots_txt_allowed": s.robots_txt_allowed,
            }
            for s in sources
        ],
    }


@router.post("/sources", summary="添加数据源")
def create_source(
    data: SourceCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    source = CrawlSource(
        name=data.name,
        source_type=data.source_type,
        category=data.category,
        oa_id=data.oa_id,
        oa_name=data.oa_name,
        base_url=data.base_url,
        region=data.region,
        org_name=data.org_name,
        description=data.description,
        crawl_frequency=data.crawl_frequency or "daily",
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return {"id": source.id, "message": "数据源添加成功"}


@router.put("/sources/{source_id}", summary="更新数据源")
def update_source(
    source_id: int,
    data: SourceUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "数据源不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(source, key, value)

    db.commit()
    return {"message": "更新成功"}


@router.delete("/sources/{source_id}", summary="删除数据源")
def delete_source(
    source_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "数据源不存在")

    # 软删除：设为不活跃
    source.is_active = False
    db.commit()
    return {"message": "数据源已停用"}


# =====================================================================
# 关键词管理
# =====================================================================
@router.get("/keywords", response_model=KeywordListOut, summary="关键词词库")
def list_keywords(
    keyword_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    query = db.query(CrawlKeyword)
    if keyword_type:
        query = query.filter(CrawlKeyword.keyword_type == keyword_type)

    keywords = query.order_by(desc(CrawlKeyword.weight)).all()
    return {
        "total": len(keywords),
        "items": [
            {
                "id": kw.id,
                "keyword": kw.keyword,
                "keyword_type": kw.keyword_type,
                "category": kw.category,
                "weight": kw.weight,
                "is_active": kw.is_active,
            }
            for kw in keywords
        ],
    }


@router.post("/keywords", summary="添加关键词")
def add_keyword(
    data: KeywordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    # 检查重复
    existing = db.query(CrawlKeyword).filter(
        CrawlKeyword.keyword == data.keyword,
        CrawlKeyword.keyword_type == data.keyword_type,
    ).first()
    if existing:
        raise HTTPException(409, "关键词已存在")

    kw = CrawlKeyword(
        keyword=data.keyword,
        keyword_type=data.keyword_type,
        category=data.category,
        weight=data.weight or (3 if data.keyword_type == "core" else 1),
    )
    db.add(kw)
    db.commit()
    return {"id": kw.id, "message": "关键词添加成功"}


@router.delete("/keywords/{keyword_id}", summary="删除关键词")
def delete_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    kw = db.query(CrawlKeyword).filter(CrawlKeyword.id == keyword_id).first()
    if not kw:
        raise HTTPException(404, "关键词不存在")
    db.delete(kw)
    db.commit()
    return {"message": "已删除"}


# =====================================================================
# 文章列表 / 详情 / 搜索
# =====================================================================
@router.get("/", response_model=ArticleListOut, summary="文章列表（分页+筛选）")
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    province: Optional[str] = None,
    keyword: Optional[str] = None,
    source_id: Optional[int] = None,
    is_low_quality: Optional[bool] = None,
    order_by: str = Query("publish_time", pattern="^(publish_time|quality_score|crawl_time|view_count)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(CrawlArticle)

    # 筛选
    if category:
        query = query.filter(CrawlArticle.article_category == category)
    is_reviewer = user.user_type in ("local_admin", "platform_admin")
    if is_reviewer and status:
        query = query.filter(CrawlArticle.status == status)
    elif is_reviewer:
        query = query.filter(CrawlArticle.status.in_(["approved", "published"]))
    if user.user_type == "local_admin" and status not in (None, "approved", "published"):
        query = query.filter(CrawlArticle.related_province == require_local_admin_province(user))
    else:
        if status and status not in ("approved", "published"):
            raise HTTPException(status_code=403, detail="无权查看未发布文章")
        if is_low_quality:
            raise HTTPException(status_code=403, detail="无权查看低质量文章")
        query = query.filter(CrawlArticle.status.in_(["approved", "published"]))
    if province:
        query = query.filter(CrawlArticle.related_province == province)
    if source_id:
        query = query.filter(CrawlArticle.source_id == source_id)
    if is_reviewer and is_low_quality is not None:
        query = query.filter(CrawlArticle.is_low_quality == is_low_quality)
    if keyword:
        query = query.filter(
            or_(
                CrawlArticle.title.contains(keyword),
                CrawlArticle.content_text.contains(keyword),
            )
        )

    # 非管理员只看非低质
    if not is_reviewer:
        query = query.filter(CrawlArticle.is_low_quality == False)

    total = query.count()

    # 排序
    order_col = getattr(CrawlArticle, order_by)
    query = query.order_by(desc(order_col))

    # 分页
    offset = (page - 1) * page_size
    articles = query.offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": a.id,
                "title": a.title,
                "source_name": a.source_name,
                "publish_time": a.publish_time.isoformat() if a.publish_time else None,
                "summary": a.summary,
                "cover_image": a.cover_image,
                "article_category": a.article_category,
                "quality_score": a.quality_score,
                "matched_keywords": a.matched_keywords,
                "related_province": a.related_province,
                "related_city": a.related_city,
                "image_count": a.image_count,
                "view_count": a.view_count,
                "status": a.status,
            }
            for a in articles
        ],
    }


@router.get("/{article_id:int}", response_model=ArticleDetailOut, summary="文章详情")
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    article = db.query(CrawlArticle).filter(CrawlArticle.id == article_id).first()
    if not article:
        raise HTTPException(404, "文章不存在")
    if user.user_type not in ("local_admin", "platform_admin") and (
        article.status not in ("approved", "published") or article.is_low_quality
    ):
        raise HTTPException(404, "文章不存在")
    if user.user_type == "local_admin" and article.status not in ("approved", "published"):
        ensure_province_scope(user, article.related_province)

    # 浏览量+1
    article.view_count += 1
    db.commit()

    # 获取配图
    images = db.query(CrawlArticleImage).filter(
        CrawlArticleImage.article_id == article_id
    ).order_by(CrawlArticleImage.sort_order).all()

    # 获取关联基地
    base_links = db.query(CrawlArticleBaseLink).filter(
        CrawlArticleBaseLink.article_id == article_id
    ).all()

    return {
        "id": article.id,
        "title": article.title,
        "author": article.author,
        "source_name": article.source_name,
        "publish_time": article.publish_time.isoformat() if article.publish_time else None,
        "crawl_time": article.crawl_time.isoformat() if article.crawl_time else None,
        "summary": article.summary,
        "content_html": sanitize_html(article.content_html),
        "content_text": article.content_text,
        "content_length": article.content_length,
        "original_url": article.original_url,
        "matched_keywords": article.matched_keywords,
        "article_category": article.article_category,
        "tags": article.tags,
        "quality_score": article.quality_score,
        "is_low_quality": article.is_low_quality,
        "related_province": article.related_province,
        "related_city": article.related_city,
        "image_count": article.image_count,
        "cover_image": article.cover_image,
        "view_count": article.view_count,
        "status": article.status,
        "images": [
            {
                "id": img.id,
                "image_url": img.image_url,
                "caption": img.caption,
                "is_cover": img.is_cover,
                "sort_order": img.sort_order,
            }
            for img in images
        ],
        "linked_bases": [
            {
                "base_id": link.base_id,
                "match_type": link.match_type,
                "confidence": link.confidence,
                "match_reason": link.match_reason,
            }
            for link in base_links
        ],
    }


# =====================================================================
# 文章审核
# =====================================================================
@router.post("/{article_id}/review", summary="审核文章")
def review_article(
    article_id: int,
    data: ArticleReview,
    db: Session = Depends(get_db),
    user: User = Depends(get_reviewer),
):
    # 只有管理员可以审核
    if user.user_type not in ("local_admin", "platform_admin"):
        raise HTTPException(403, "无审核权限")

    article = db.query(CrawlArticle).filter(CrawlArticle.id == article_id).first()
    if not article:
        raise HTTPException(404, "文章不存在")
    ensure_province_scope(user, article.related_province)
    if data.status == "rejected" and not data.reason:
        raise HTTPException(422, "拒绝文章时必须填写原因")

    article.status = data.status  # approved / rejected
    article.reviewed_by = user.id
    article.reviewed_at = datetime.now()
    if data.status == "rejected":
        article.reject_reason = data.reason
    elif data.status == "approved":
        article.status = "published"  # 审核通过直接发布

    db.commit()
    return {"message": "审核完成", "status": article.status}


# =====================================================================
# 爬取任务
# =====================================================================
@router.post("/crawl/{source_id}", summary="手动触发采集任务")
def trigger_crawl(
    source_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    # 只有管理员可以触发采集
    if user.user_type not in ("local_admin", "platform_admin"):
        raise HTTPException(403, "无操作权限")

    source = db.query(CrawlSource).filter(CrawlSource.id == source_id).first()
    if not source:
        raise HTTPException(404, "数据源不存在")
    if not source.is_active:
        raise HTTPException(400, "数据源已停用")

    # 创建任务记录（标记为pending，后台执行）
    task = CrawlTask(
        source_id=source.id,
        task_type="manual",
        status="pending",
        triggered_by=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "task_id": task.id,
        "message": f"采集任务已创建，数据源: {source.name}",
        "note": "任务将在后台执行，请稍后查看任务状态",
    }


@router.get("/tasks", response_model=TaskListOut, summary="采集任务列表")
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    query = db.query(CrawlTask)
    if status:
        query = query.filter(CrawlTask.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    tasks = query.order_by(desc(CrawlTask.created_at)).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": t.id,
                "source_id": t.source_id,
                "task_type": t.task_type,
                "status": t.status,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "finished_at": t.finished_at.isoformat() if t.finished_at else None,
                "urls_found": t.urls_found,
                "articles_new": t.articles_new,
                "articles_dup": t.articles_dup,
                "articles_low_quality": t.articles_low_quality,
                "errors": t.errors,
                "summary": t.summary,
            }
            for t in tasks
        ],
    }


@router.get("/stats/overview", summary="采集统计概览")
def crawl_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    """采集系统统计概览（管理后台首页用）"""
    total_articles = db.query(CrawlArticle).count()
    published = db.query(CrawlArticle).filter(CrawlArticle.status == "published").count()
    pending = db.query(CrawlArticle).filter(CrawlArticle.status == "pending").count()
    low_quality = db.query(CrawlArticle).filter(CrawlArticle.is_low_quality == True).count()

    total_sources = db.query(CrawlSource).count()
    active_sources = db.query(CrawlSource).filter(CrawlSource.is_active == True).count()

    total_keywords = db.query(CrawlKeyword).filter(CrawlKeyword.is_active == True).count()

    # 按分类统计
    category_stats = db.query(
        CrawlArticle.article_category,
        func.count(CrawlArticle.id),
    ).filter(
        CrawlArticle.status == "published"
    ).group_by(CrawlArticle.article_category).all()

    # 按省份统计
    province_stats = db.query(
        CrawlArticle.related_province,
        func.count(CrawlArticle.id),
    ).filter(
        CrawlArticle.related_province.isnot(None),
        CrawlArticle.status == "published",
    ).group_by(CrawlArticle.related_province).order_by(
        desc(func.count(CrawlArticle.id))
    ).limit(10).all()

    # 最近任务
    recent_tasks = db.query(CrawlTask).order_by(
        desc(CrawlTask.created_at)
    ).limit(5).all()

    return {
        "articles": {
            "total": total_articles,
            "published": published,
            "pending_review": pending,
            "low_quality": low_quality,
        },
        "sources": {
            "total": total_sources,
            "active": active_sources,
        },
        "keywords": total_keywords,
        "by_category": {cat: cnt for cat, cnt in category_stats if cat},
        "by_province": {prov: cnt for prov, cnt in province_stats if prov},
        "recent_tasks": [
            {
                "id": t.id,
                "status": t.status,
                "articles_new": t.articles_new,
                "summary": t.summary,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in recent_tasks
        ],
    }
