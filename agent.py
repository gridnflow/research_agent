from datetime import datetime

from rich.console import Console
from rich.panel import Panel

from core import save_report, stream_research

console = Console()


class MarketingResearchAgent:
    def research(self, query: str) -> str:
        console.print(Panel(
            f"[bold]{query}[/bold]",
            title="[yellow]🔍 리서치 시작[/yellow]",
            border_style="yellow",
        ))
        console.print()

        full_text = ""
        start_time = datetime.now()

        for chunk in stream_research(query):
            if chunk["type"] == "gather":
                console.print("[dim cyan]📡 Reddit·앱스토어 데이터 수집 중...[/dim cyan]", end="\r")
            elif chunk["type"] == "gather_done":
                console.print(" " * 40, end="\r")
                if chunk.get("found"):
                    console.print("[dim green]✓ 실제 외부 데이터 수집됨[/dim green]")
            elif chunk["type"] == "search":
                console.print("[dim cyan]🌐 웹 검색 중...[/dim cyan]", end="\r")
            elif chunk["type"] == "search_done":
                console.print(" " * 30, end="\r")
            elif chunk["type"] == "text":
                full_text += chunk["delta"]
                console.print(chunk["delta"], end="")

        elapsed = (datetime.now() - start_time).seconds
        console.print()
        console.print(f"\n[bold green]✅ 분석 완료 ({elapsed}초)[/bold green]")

        report_path = save_report(query, full_text)
        console.print(f"[dim]📄 리포트 저장: {report_path}[/dim]\n")

        return full_text
