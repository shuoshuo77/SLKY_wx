"""
所有数据模型统一导出
必须在所有 ORM 类定义完毕后导入，确保 relationship 字符串能正确解析。
"""
from app.models.user import User, UserVerification
from app.models.base import (
    ForestBase,
    BaseQualification,
    BaseResource,
    BaseBusiness,
    BaseOperation,
    BaseMedia,
    BaseContact,
)
from app.models.other import (
    Policy,
    PolicyAttachment,
    NaturalResource,
    IndustryData,
    Expert,
    PublicDemand,
    AuditLog,
    Favorite,
    BaseAppointment,
    BaseBrowseHistory,
    Notification,
    SysLog,
)
from app.models.article import (
    CrawlSource,
    CrawlKeyword,
    CrawlArticle,
    CrawlArticleImage,
    CrawlTask,
    CrawlArticleBaseLink,
)
from app.models.home import Banner, FeaturedService

__all__ = [
    "User", "UserVerification",
    "ForestBase",
    "BaseQualification", "BaseResource", "BaseBusiness",
    "BaseOperation", "BaseMedia", "BaseContact",
    "Policy", "PolicyAttachment",
    "NaturalResource", "IndustryData", "Expert",
    "PublicDemand", "AuditLog", "Favorite",
    "BaseAppointment", "BaseBrowseHistory",
    "Notification", "SysLog",
    "CrawlSource", "CrawlKeyword", "CrawlArticle",
    "CrawlArticleImage", "CrawlTask", "CrawlArticleBaseLink",
    "Banner", "FeaturedService",
]
