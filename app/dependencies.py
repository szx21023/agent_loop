"""共用依賴（FastAPI Depends 用）。

目前設定以 config 的 `settings` / `get_settings()` 單例存取，尚無共用依賴；
之後有分頁、目前使用者等跨路由依賴時放這裡。
"""
