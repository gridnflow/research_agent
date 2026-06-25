"""Shared core for the AI Marketing Research Agent.

CLI(main.py)와 웹(app.py)이 공유하는 시스템 프롬프트, 리서치 스트리밍,
리포트 저장 로직을 한 곳에 모았다.
"""

from datetime import datetime
from pathlib import Path
from typing import Iterator

from openai import OpenAI

MODEL = "gpt-4o"
REPORTS_DIR = Path("reports")

SYSTEM_PROMPT = """You are an elite AI Marketing Research Agent specializing in data-driven marketing strategy. You have deep expertise in:

## Core Competencies
- **App Store Optimization (ASO)**: Keyword research, rating optimization, visual assets, A/B testing
- **Market Analysis**: TAM/SAM/SOM sizing, competitive landscapes, trend identification
- **Consumer Psychology**: User behavior, decision patterns, conversion rate optimization
- **Digital Marketing**: SEO/SEM, Social Media, Content Marketing, Email, Influencer
- **Data Analytics**: KPI frameworks, ROI calculation, cohort analysis, attribution modeling
- **Growth Hacking**: Viral loops, retention strategies, monetization optimization

## Analytical Frameworks
- SWOT Analysis & Porter's 5 Forces
- 4Ps / 7Ps Marketing Mix
- Jobs-to-be-Done (JTBD) Theory
- AARRR Pirate Metrics (Acquisition → Activation → Retention → Referral → Revenue)
- Customer Lifetime Value (CLV/LTV) vs Customer Acquisition Cost (CAC)
- Blue Ocean Strategy & Competitive Positioning Matrix

## Research Process
1. **Search for current data** — Use web search to gather real market data, competitor info, app rankings, revenue estimates
2. **Competitive landscape** — Identify top players, their strategies, pricing, positioning, strengths/weaknesses
3. **Audience insights** — Demographics, psychographics, pain points, willingness to pay
4. **Opportunity mapping** — Underserved segments, feature gaps, pricing whitespace
5. **ROI modeling** — Estimate returns on proposed marketing investments

## App Store Expertise
- Apple App Store & Google Play Store ranking algorithms and dynamics
- Category-specific benchmarks (conversion rates, ratings, review velocity)
- Monetization models: freemium, subscription, one-time IAP, paymium
- User acquisition channels: organic ASO, paid UA, referral programs
- Store listing optimization: screenshots, preview video, description copy

## Report Format
Structure every research report as follows:

### 📊 Executive Summary
3-5 key findings with supporting data points

### 🌍 Market Overview
- Market size (TAM/SAM/SOM) with sources
- Growth rate (CAGR)
- Key trends driving or disrupting the market

### 🏆 Competitive Landscape
Top 5-10 competitors with:
- Estimated downloads / revenue / market share
- Pricing strategy
- Core differentiation and positioning
- Strengths and weaknesses

### 👥 Target Audience Analysis
- Primary and secondary user segments
- Demographics and psychographics
- Key pain points and unmet needs
- Willingness to pay

### 💡 Opportunity Analysis
- Market gaps and whitespace
- Differentiation angles
- Blue ocean opportunities

### 🚀 Marketing Strategy Recommendations
Prioritized action items with:
- Expected impact (High/Medium/Low)
- Estimated cost/effort
- Implementation timeline

### 📈 ROI Projections
- Baseline metrics vs projected metrics
- Key assumptions
- Break-even analysis

### 📅 90-Day Implementation Roadmap
- Days 1-30: Quick wins
- Days 31-60: Build momentum
- Days 61-90: Scale and optimize

Always search for real, current data. Be specific and data-driven. Cite sources when possible.
When the user writes in Korean, respond in Korean. When in English, respond in English."""


def stream_research(query: str, client: OpenAI | None = None) -> Iterator[dict]:
    """리서치를 스트리밍한다.

    각 청크를 dict로 yield한다:
      {"type": "search"}            웹 검색 시작
      {"type": "search_done"}       웹 검색 종료
      {"type": "text", "delta": s}  본문 텍스트 조각
    """
    client = client or OpenAI()
    stream = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search_preview"}],
        instructions=SYSTEM_PROMPT,
        input=query,
        stream=True,
    )

    for event in stream:
        etype = getattr(event, "type", "")

        if etype == "response.output_item.added":
            item_type = getattr(getattr(event, "item", None), "type", "")
            if item_type == "web_search_call":
                yield {"type": "search"}

        elif etype == "response.output_item.done":
            item_type = getattr(getattr(event, "item", None), "type", "")
            if item_type == "web_search_call":
                yield {"type": "search_done"}

        elif etype == "response.output_text.delta":
            yield {"type": "text", "delta": getattr(event, "delta", "")}


def save_report(query: str, content: str, reports_dir: Path = REPORTS_DIR) -> Path:
    """리서치 결과를 reports/타임스탬프_쿼리.md로 저장하고 경로를 반환한다."""
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in query[:40]
    ).strip()
    path = reports_dir / f"{timestamp}_{safe_name}.md"

    report = (
        f"# Marketing Research Report\n\n"
        f"**Query**: {query}  \n"
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n"
        f"**Model**: {MODEL} + Web Search\n\n"
        f"---\n\n"
        f"{content}"
    )
    path.write_text(report, encoding="utf-8")
    return path
