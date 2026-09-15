"""自訂例外基底 + 統一 exception handler。

業務錯誤拋 AppError（或其子類），由 register_exception_handlers 掛上的 handler
轉成一致的 JSON 回應。注意：工具內部的失敗回 ToolResultSchema(is_ok=False)，不要在這裡
拋例外，以免中斷 agent loop。
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """所有業務例外的基底。status_code 決定對外 HTTP 狀態碼。"""

    status_code: int = 500
    code: str = "app_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.__class__.__name__)
        self.message = message or self.__class__.__name__


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
