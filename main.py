#!/usr/bin/env python3
"""AI Marketing Research Agent - 마케팅 리서치 자동화"""

import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

load_dotenv()

from agent import MarketingResearchAgent

console = Console()

EXAMPLES = [
    ("앱 시장 분석", "애플스토어, 구글플레이 헬스케어 앱 시장 분석해줘"),
    ("경쟁 분석", "Analyze the top fitness tracking apps and their marketing strategies"),
    ("ROI 전략", "내 명상 앱의 마케팅 ROI를 높일 수 있는 전략 알려줘"),
    ("트렌드 리서치", "2024-2025 모바일 앱 마케팅 트렌드와 성장 채널 분석해줘"),
    ("수익화 전략", "Subscription vs freemium monetization: which is better for a productivity app?"),
]


def show_welcome():
    console.print(Panel.fit(
        "[bold green]🧠 AI Marketing Research Agent[/bold green]\n\n"
        "[dim]마케팅 리서치 자동화 에이전트[/dim]\n"
        "[dim]웹 데이터 수집 → 분석 → 구조화된 보고서 생성[/dim]",
        border_style="green",
        padding=(1, 4),
    ))

    table = Table(title="예시 쿼리", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("유형", style="cyan", width=12)
    table.add_column("쿼리", style="white")

    for i, (label, query) in enumerate(EXAMPLES, 1):
        table.add_row(str(i), label, query)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]번호를 입력하면 예시 쿼리를 사용합니다. 'exit'으로 종료.[/dim]\n")


def get_query() -> Optional[str]:
    raw = Prompt.ask("[bold cyan]리서치 쿼리[/bold cyan]").strip()

    if not raw:
        return None
    if raw.lower() in ("exit", "quit", "종료", "q"):
        return ""

    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(EXAMPLES):
            _, query = EXAMPLES[idx]
            console.print(f"[dim]→ {query}[/dim]\n")
            return query
        console.print("[red]잘못된 번호입니다.[/red]")
        return None

    return raw


def main():
    show_welcome()
    agent = MarketingResearchAgent()

    while True:
        query = get_query()

        if query is None:
            continue
        if query == "":
            console.print("[green]종료합니다. 생성된 리포트는 reports/ 폴더에서 확인하세요.[/green]")
            break

        try:
            agent.research(query)
        except KeyboardInterrupt:
            console.print("\n[yellow]리서치가 중단되었습니다.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]오류 발생: {e}[/red]")

        console.print("─" * 70 + "\n")


if __name__ == "__main__":
    main()
