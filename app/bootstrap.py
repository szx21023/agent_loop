"""應用組裝層（composition root）：把功能模組的工具註冊進 REGISTRY。

放在 app 根層而非 core，因為「組裝各 feature」是組裝層的責任；core 必須保持
feature-agnostic（CLAUDE.md：core 不可反向 import modules）。entrypoints
（main.py / scripts/ask.py）於啟動時各呼叫一次 register_tools()。
"""


def register_tools() -> None:
    """Import feature tool modules for their register() side effects.

    Idempotent: Python caches modules, so repeated calls import once and the
    register() calls run only on first import.
    """
    import app.modules.knowledge.service  # noqa: F401  (registers knowledge/action tools)
