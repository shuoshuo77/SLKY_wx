"""
应用配置管理
"""
from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # ---------- 数据库 ----------
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root"
    DB_NAME: str = "forest_wellness"
    DATABASE_URL_OVERRIDE: str | None = None
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_RECYCLE_SECONDS: int = 1800

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return URL.create(
            drivername="mysql+pymysql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query={"charset": "utf8mb4"},
        ).render_as_string(hide_password=False)

    # ---------- JWT ----------
    SECRET_KEY: str = "change-this-to-a-random-secret-key-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # ---------- 认证限流 ----------
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    RATE_LIMIT_FAIL_OPEN: bool = False
    LOGIN_RATE_LIMIT: int = 5
    LOGIN_RATE_WINDOW_SECONDS: int = 300
    REGISTER_RATE_LIMIT: int = 10
    REGISTER_RATE_WINDOW_SECONDS: int = 3600

    # ---------- 文件上传 ----------
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: str = ".jpg,.jpeg,.png,.webp,.pdf"
    ALLOWED_UPLOAD_MIME_TYPES: str = "image/jpeg,image/png,image/webp,application/pdf"

    # ---------- 应用 ----------
    APP_NAME: str = "森林康养信息收集平台"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = False
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174,http://localhost:5174"

    # ---------- 小程序智能体（DeepSeek OpenAI 兼容接口） ----------
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_TIMEOUT_SECONDS: int = 30

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.CORS_ORIGINS.split(",") if value.strip()]

    @property
    def allowed_upload_extensions(self) -> set[str]:
        return {value.strip().lower() for value in self.ALLOWED_UPLOAD_EXTENSIONS.split(",") if value.strip()}

    @property
    def allowed_upload_mime_types(self) -> set[str]:
        return {value.strip().lower() for value in self.ALLOWED_UPLOAD_MIME_TYPES.split(",") if value.strip()}

    @model_validator(mode="after")
    def validate_production_security(self):
        default_secret = "change-this-to-a-random-secret-key-min-32-chars"
        if not self.APP_DEBUG and self.SECRET_KEY == default_secret:
            raise ValueError("SECRET_KEY must be changed when APP_DEBUG is disabled")
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
