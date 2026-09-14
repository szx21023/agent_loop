"""共用依賴（FastAPI Depends 用）。"""
from app.config import Settings, get_settings


def settings_dependency() -> Settings:
    """以依賴注入方式取得設定；路由需要讀設定時用 Depends(settings_dependency)。"""
    return get_settings()
