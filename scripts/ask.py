"""CLI: ask the agent a question. Usage: python -m scripts.ask "your question" """
import sys

from app.core.tools import register_tools
from app.modules.chat.service import run_agent

register_tools()  # 確保工具已註冊到 REGISTRY


def main() -> None:
    question = " ".join(sys.argv[1:]) or "A 專案之前有沒有 API timeout 問題？"
    resp = run_agent(question)
    print(f"\nQ: {question}\n")
    print(f"A: {resp.answer}\n")
    print(f"(steps: {resp.steps})")
    if resp.sources:
        print("sources:")
        for s in resp.sources:
            print(f"  - [{s.tool}] {s.ref}: {s.snippet[:60]}")


if __name__ == "__main__":
    main()
