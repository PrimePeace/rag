from functools import lru_cache  # 缓存 settings，避免重复解析环境变量
from pathlib import Path  # 用于定位项目根目录下的 .env

from pydantic_settings import BaseSettings, SettingsConfigDict  # 从环境变量与 .env 加载配置

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # 定位到 backend 项目根目录


class Settings(BaseSettings):
    model_config = SettingsConfigDict(  # 统一配置读取规则
        env_file=PROJECT_ROOT / ".env",  # 从 backend/.env 读取本地密钥，不入库
        env_file_encoding="utf-8",  # 使用 UTF-8 解析 .env
        extra="ignore",  # 忽略未声明的额外环境变量
        case_sensitive=False,  # 环境变量名大小写不敏感
    )

    cos_secret_id: str = ""  # 腾讯云 COS SecretId，仅通过环境变量注入
    cos_secret_key: str = ""  # 腾讯云 COS SecretKey，仅通过环境变量注入
    cos_region: str = "ap-chengdu"  # COS 默认地域
    cos_bucket: str = ""  # COS 桶名，仅通过环境变量注入

    @property
    def cos_configured(self) -> bool:  # 判断 COS 必要配置是否齐全
        return bool(self.cos_secret_id and self.cos_secret_key and self.cos_bucket)  # 三项都有值才视为已配置

    cors_origins: str = "http://localhost:5173"  # 允许跨域的前端源，逗号分隔

    @property
    def cors_origin_list(self) -> list[str]:  # 将 CORS 配置拆成列表供中间件使用
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]  # 去掉空白并过滤空项

    app_name: str = "rag-knowledge-base"  # 应用名称
    log_level: str = "INFO"  # 默认日志级别

    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5432/rag_kb"  # 本地开发默认数据库连接


@lru_cache(maxsize=1)
def get_settings() -> Settings:  # 提供可缓存的 Settings 工厂
    return Settings()  # 实例化并读取当前环境配置


settings = get_settings()  # 模块级单例，供业务代码直接导入
