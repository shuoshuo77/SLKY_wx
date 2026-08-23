"""
文章采集相关数据模型
- 数据源管理（公众号/网站）
- 关键词词库
- 文章存储
- 文章配图
- 爬取任务日志
- 文章-基地关联
"""
from sqlalchemy import (
    Column, String, Enum, Boolean, DateTime, Text, JSON,
    Integer, Float, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import mysql
from datetime import datetime
from app.database import Base, ID_TYPE


LONG_TEXT = Text().with_variant(mysql.LONGTEXT(), "mysql")


# =====================================================================
# 1. 数据源管理表 — 管理待采集的公众号 / 网站
# =====================================================================
class CrawlSource(Base):
    """采集数据源（公众号 / 政务网站 / 行业门户）"""
    __tablename__ = "crawl_sources"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="数据源名称，如'林业康养'公众号")
    source_type = Column(
        Enum("wechat_oa", "gov_website", "industry_portal", "news_site"),
        nullable=False,
        default="wechat_oa",
        comment="数据源类型：公众号/政务网站/行业门户/新闻站",
    )
    category = Column(
        Enum("official", "industry", "policy"),
        nullable=False,
        default="official",
        comment="分类：官方类/行业类/政策类",
    )
    # 公众号特有字段
    oa_id = Column(String(100), nullable=True, comment="公众号微信号/biz")
    oa_name = Column(String(200), nullable=True, comment="公众号显示名称")
    # 通用字段
    base_url = Column(String(500), nullable=True, comment="网站首页URL（非公众号时使用）")
    region = Column(String(100), nullable=True, comment="覆盖地区，如'广东省'、'全国'")
    org_name = Column(String(200), nullable=True, comment="主管/运营单位")
    description = Column(Text, nullable=True, comment="数据源简介")

    # 采集控制
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用采集")
    crawl_frequency = Column(
        String(20), nullable=False, default="daily",
        comment="采集频率：hourly/daily/weekly/manual",
    )
    last_crawl_at = Column(DateTime, nullable=True, comment="最近一次采集时间")
    last_article_count = Column(Integer, nullable=False, default=0, comment="上次采集新增文章数")
    total_articles = Column(Integer, nullable=False, default=0, comment="累计采集文章数")

    # 合规
    robots_txt_checked = Column(Boolean, nullable=False, default=False, comment="是否已检查robots.txt")
    robots_txt_allowed = Column(Boolean, nullable=False, default=True, comment="robots.txt是否允许采集")
    respect_note = Column(Text, nullable=True, comment="合规备注（版权声明、采集许可等）")

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    articles = relationship("CrawlArticle", back_populates="source")
    tasks = relationship("CrawlTask", back_populates="source")

    __table_args__ = (
        Index("idx_source_type_cat", "source_type", "category"),
        Index("idx_source_active", "is_active"),
    )


# =====================================================================
# 2. 关键词词库表
# =====================================================================
class CrawlKeyword(Base):
    """采集关键词词库"""
    __tablename__ = "crawl_keywords"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    keyword = Column(String(100), nullable=False, comment="关键词文本")
    keyword_type = Column(
        Enum("core", "extended", "exclude"),
        nullable=False,
        default="core",
        comment="类型：核心词/拓展词/排除词",
    )
    category = Column(
        String(50), nullable=True,
        comment="子分类，如'康养模式'、'政策法规'、'基地建设'、'产业规划'",
    )
    weight = Column(Integer, nullable=False, default=1, comment="权重（核心词=3，拓展词=1）")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("keyword", "keyword_type", name="uq_keyword_type"),
        Index("idx_keyword_type", "keyword_type", "is_active"),
    )


# =====================================================================
# 3. 文章主表
# =====================================================================
class CrawlArticle(Base):
    """采集到的文章"""
    __tablename__ = "crawl_articles"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    source_id = Column(ID_TYPE, ForeignKey("crawl_sources.id"), nullable=False, comment="来源数据源")

    # 文章基本信息
    title = Column(String(500), nullable=False, comment="文章标题")
    author = Column(String(200), nullable=True, comment="作者")
    source_name = Column(String(200), nullable=True, comment="来源公众号/网站名称")
    publish_time = Column(DateTime, nullable=True, comment="文章发布时间")
    crawl_time = Column(DateTime, nullable=False, default=datetime.now, comment="采集时间")

    # 内容
    summary = Column(Text, nullable=True, comment="文章摘要（自动生成，前200字）")
    content_html = Column(LONG_TEXT, nullable=True, comment="正文HTML（原始）")
    content_text = Column(LONG_TEXT, nullable=True, comment="正文纯文本")
    content_length = Column(Integer, nullable=True, comment="正文字数")

    # 原文链接
    original_url = Column(String(1000), nullable=False, comment="原文URL")
    url_hash = Column(String(64), nullable=False, unique=True, comment="URL的MD5哈希，用于去重")

    # 关键词与分类
    matched_keywords = Column(JSON, nullable=True, comment="命中的关键词列表，如['森林康养','生态疗愈']")
    article_category = Column(
        Enum(
            "policy",        # 政策法规
            "industry_news", # 行业动态
            "base_info",     # 基地介绍
            "research",      # 学术研究
            "experience",    # 体验分享
            "announcement",  # 通知公告
            "other",         # 其他
        ),
        nullable=True,
        default="other",
        comment="文章分类",
    )
    tags = Column(JSON, nullable=True, comment="自动标签，如['康养政策','广东省']")

    # 内容质量
    quality_score = Column(Float, nullable=True, comment="质量评分0-100（综合字数/关键词密度/结构等）")
    is_low_quality = Column(Boolean, nullable=False, default=False, comment="是否低质内容（广告/转载/短视频）")
    low_quality_reason = Column(String(300), nullable=True, comment="低质判定原因")

    # 关联基地
    related_province = Column(String(30), nullable=True, comment="文章涉及的省份")
    related_city = Column(String(30), nullable=True, comment="文章涉及的城市")

    # 配图
    image_count = Column(Integer, nullable=False, default=0, comment="配图数量")
    cover_image = Column(String(1000), nullable=True, comment="封面图URL")

    # 审核状态
    status = Column(
        Enum("pending", "approved", "rejected", "published"),
        nullable=False,
        default="pending",
        comment="审核状态：待审核/通过/拒绝/已发布",
    )
    reviewed_by = Column(ID_TYPE, nullable=True, comment="审核人ID")
    reviewed_at = Column(DateTime, nullable=True)
    reject_reason = Column(String(500), nullable=True)

    # 统计
    view_count = Column(Integer, nullable=False, default=0, comment="平台内浏览量")
    like_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系
    source = relationship("CrawlSource", back_populates="articles")
    images = relationship("CrawlArticleImage", back_populates="article", cascade="all, delete-orphan")
    base_links = relationship("CrawlArticleBaseLink", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_article_source", "source_id", "publish_time"),
        Index("idx_article_status", "status", "publish_time"),
        Index("idx_article_category", "article_category", "publish_time"),
        Index("idx_article_quality", "is_low_quality", "quality_score"),
        Index("idx_article_region", "related_province", "related_city"),
    )


# =====================================================================
# 4. 文章配图表
# =====================================================================
class CrawlArticleImage(Base):
    """文章配图"""
    __tablename__ = "crawl_article_images"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    article_id = Column(ID_TYPE, ForeignKey("crawl_articles.id"), nullable=False)
    image_url = Column(String(1000), nullable=False, comment="图片原始URL")
    local_path = Column(String(500), nullable=True, comment="本地保存路径（已下载时）")
    caption = Column(String(500), nullable=True, comment="图片说明/alt文字")
    sort_order = Column(Integer, nullable=False, default=0)
    is_cover = Column(Boolean, nullable=False, default=False, comment="是否封面图")
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    article = relationship("CrawlArticle", back_populates="images")

    __table_args__ = (
        Index("idx_image_article", "article_id", "sort_order"),
    )


# =====================================================================
# 5. 爬取任务日志表
# =====================================================================
class CrawlTask(Base):
    """爬取任务执行记录"""
    __tablename__ = "crawl_tasks"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    source_id = Column(ID_TYPE, ForeignKey("crawl_sources.id"), nullable=True, comment="数据源ID（null=全量任务）")
    task_type = Column(
        Enum("full", "incremental", "manual", "scheduled"),
        nullable=False,
        default="scheduled",
        comment="任务类型：全量/增量/手动/定时",
    )
    status = Column(
        Enum("pending", "running", "success", "failed", "cancelled"),
        nullable=False,
        default="pending",
    )
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # 统计
    urls_found = Column(Integer, nullable=False, default=0, comment="发现的文章URL数")
    articles_new = Column(Integer, nullable=False, default=0, comment="新增文章数")
    articles_dup = Column(Integer, nullable=False, default=0, comment="重复跳过数")
    articles_low_quality = Column(Integer, nullable=False, default=0, comment="低质过滤数")
    errors = Column(Integer, nullable=False, default=0, comment="错误数")

    # 日志
    error_log = Column(Text, nullable=True, comment="错误日志")
    summary = Column(Text, nullable=True, comment="任务摘要")

    triggered_by = Column(ID_TYPE, nullable=True, comment="触发用户ID（手动任务时）")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    source = relationship("CrawlSource", back_populates="tasks")

    __table_args__ = (
        Index("idx_task_status", "status", "created_at"),
        Index("idx_task_source", "source_id", "created_at"),
    )


# =====================================================================
# 6. 文章-基地关联表（文章提及的基地）
# =====================================================================
class CrawlArticleBaseLink(Base):
    """文章与基地的关联（自动匹配 + 人工标注）"""
    __tablename__ = "crawl_article_base_links"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    article_id = Column(ID_TYPE, ForeignKey("crawl_articles.id"), nullable=False, comment="文章ID")
    base_id = Column(ID_TYPE, nullable=False, comment="基地ID（逻辑外键，无物理FK约束）")
    match_type = Column(
        Enum("auto", "manual"),
        nullable=False,
        default="auto",
        comment="匹配方式：自动/人工",
    )
    confidence = Column(Float, nullable=True, comment="自动匹配置信度0-1")
    match_reason = Column(String(300), nullable=True, comment="匹配原因，如'标题包含基地名称'")
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    article = relationship("CrawlArticle", back_populates="base_links", foreign_keys=[article_id])

    __table_args__ = (
        UniqueConstraint("article_id", "base_id", name="uq_article_base"),
        Index("idx_link_base", "base_id"),
    )
