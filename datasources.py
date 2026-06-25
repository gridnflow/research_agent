"""External data sources for the research agent.

질문을 받으면 실제 데이터를 수집해 GPT 프롬프트에 주입할 컨텍스트 문자열로
정리한다. 현재 지원 소스:
  - Reddit (공식 OAuth API)        → 관련 서브레딧/검색 결과의 인기 글·토론
  - Apple App Store (iTunes Search) → 앱 검색 결과(평점/장르/가격)
  - Google Play (google-play-scraper, 선택적) → 앱 검색 결과

키가 없거나 호출이 실패해도 리서치가 멈추지 않도록, 모든 수집 함수는
예외를 흡수하고 빈 결과/안내 문자열을 반환한다.
"""

import os
from typing import List, Optional

import requests

USER_AGENT = "research_agent/0.1 (marketing research tool)"
_TIMEOUT = 15


# ── Reddit ────────────────────────────────────────────────────
def _reddit_token() -> Optional[str]:
    """client_credentials 플로우로 앱 전용 액세스 토큰을 발급받는다."""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    try:
        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(client_id, client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": USER_AGENT},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("access_token")
    except Exception:
        return None


def fetch_reddit(query: str, limit: int = 8) -> str:
    """질문과 관련된 Reddit 글을 검색해 컨텍스트 문자열로 반환한다."""
    token = _reddit_token()
    if not token:
        return ""  # 키 없음 → 조용히 스킵

    try:
        resp = requests.get(
            "https://oauth.reddit.com/search",
            params={"q": query, "limit": limit, "sort": "relevance", "t": "year"},
            headers={"Authorization": f"bearer {token}", "User-Agent": USER_AGENT},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
    except Exception as e:
        return f"(Reddit 데이터 수집 실패: {e})"

    if not children:
        return ""

    lines: List[str] = []
    for c in children:
        d = c.get("data", {})
        title = d.get("title", "").strip()
        sub = d.get("subreddit_name_prefixed", "")
        ups = d.get("ups", 0)
        comments = d.get("num_comments", 0)
        body = (d.get("selftext", "") or "").strip().replace("\n", " ")
        if len(body) > 300:
            body = body[:300] + "…"
        line = f"- [{sub}] {title} (▲{ups}, 💬{comments})"
        if body:
            line += f"\n    {body}"
        lines.append(line)

    return "### Reddit 실제 토론 데이터\n" + "\n".join(lines)


# ── Apple App Store (iTunes Search API, 키 불필요) ────────────
def fetch_app_store(query: str, limit: int = 8, country: str = "us") -> str:
    """Apple App Store에서 앱을 검색해 컨텍스트 문자열로 반환한다."""
    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": query,
                "country": country,
                "media": "software",
                "limit": limit,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as e:
        return f"(App Store 데이터 수집 실패: {e})"

    if not results:
        return ""

    lines: List[str] = []
    for r in results:
        name = r.get("trackName", "")
        genre = r.get("primaryGenreName", "")
        rating = r.get("averageUserRating")
        count = r.get("userRatingCount", 0)
        price = r.get("formattedPrice", "")
        seller = r.get("sellerName", "")
        rating_str = f"⭐{rating:.1f} ({count:,})" if rating else "평점 없음"
        lines.append(
            f"- {name} — {genre}, {rating_str}, {price or 'N/A'} · {seller}"
        )

    return f"### Apple App Store 실제 데이터 (국가: {country})\n" + "\n".join(lines)


# ── Google Play (선택적, google-play-scraper 있을 때만) ───────
def fetch_play_store(query: str, limit: int = 8, country: str = "us") -> str:
    """Google Play에서 앱을 검색한다. 라이브러리 미설치 시 조용히 스킵."""
    try:
        from google_play_scraper import search
    except ImportError:
        return ""

    try:
        results = search(query, lang="en", country=country, n_hits=limit)
    except Exception as e:
        return f"(Google Play 데이터 수집 실패: {e})"

    if not results:
        return ""

    lines: List[str] = []
    for r in results:
        title = r.get("title", "")
        dev = r.get("developer", "")
        score = r.get("score")
        score_str = f"⭐{score:.1f}" if score else "평점 없음"
        lines.append(f"- {title} — {dev}, {score_str}")

    return f"### Google Play 실제 데이터 (국가: {country})\n" + "\n".join(lines)


# ── Aggregator ────────────────────────────────────────────────
def gather_context(query: str) -> str:
    """모든 소스에서 데이터를 수집해 하나의 컨텍스트 블록으로 합친다.

    수집된 데이터가 하나도 없으면 빈 문자열을 반환한다.
    """
    blocks = [
        fetch_reddit(query),
        fetch_app_store(query),
        fetch_play_store(query),
    ]
    blocks = [b for b in blocks if b.strip()]
    if not blocks:
        return ""

    return (
        "다음은 실시간으로 수집한 실제 외부 데이터다. "
        "리서치 보고서 작성 시 이 데이터를 우선 근거로 활용하라:\n\n"
        + "\n\n".join(blocks)
    )
