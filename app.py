from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from core import save_report, stream_research

load_dotenv()

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Marketing Research Agent",
    page_icon="🧠",
    layout="wide",
)

# ── Styles ────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .stTextArea textarea { font-size: 1rem; }
    .report-box {
        background: #0e1117;
        border: 1px solid #2d2d2d;
        border-radius: 8px;
        padding: 1.5rem;
        font-size: 0.95rem;
        line-height: 1.7;
    }
    .example-btn { margin: 0.2rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────
EXAMPLES = [
    "애플스토어, 구글플레이 헬스케어 앱 시장 분석해줘",
    "Analyze the top fitness tracking apps and their marketing strategies",
    "내 명상 앱의 마케팅 ROI를 높일 수 있는 전략 알려줘",
    "2024-2025 모바일 앱 마케팅 트렌드와 성장 채널 분석해줘",
    "Subscription vs freemium: which is better for a productivity app?",
]

# ── Session state ─────────────────────────────────────────────
if "reports" not in st.session_state:
    st.session_state.reports = []  # list of {query, content, timestamp}
if "query_input" not in st.session_state:
    st.session_state.query_input = ""


# ── Helpers ───────────────────────────────────────────────────
def set_query(q: str):
    st.session_state.query_input = q


# ── Layout ────────────────────────────────────────────────────
st.title("🧠 AI Marketing Research Agent")
st.caption("실시간 웹 검색 기반 마케팅 리서치 자동화 • GPT-4o")

col_left, col_right = st.columns([2, 1])

with col_right:
    st.markdown("#### 💡 예시 쿼리")
    for ex in EXAMPLES:
        if st.button(ex[:45] + ("…" if len(ex) > 45 else ""), key=ex, use_container_width=True):
            set_query(ex)

with col_left:
    query = st.text_area(
        "리서치 쿼리",
        value=st.session_state.query_input,
        height=100,
        placeholder="예: 애플스토어 헬스케어 앱 시장 분석해줘",
        label_visibility="collapsed",
    )

    run_btn = st.button("🔍 리서치 시작", type="primary", use_container_width=True, disabled=not query.strip())

if run_btn and query.strip():
    st.divider()
    st.markdown(f"**🔍 분석 중:** `{query}`")

    status_placeholder = st.empty()
    output_placeholder = st.empty()

    collected = []

    with st.spinner("🌐 웹 검색 및 분석 중..."):
        for chunk in stream_research(query):
            if chunk["type"] == "text":
                collected.append(chunk["delta"])
                output_placeholder.markdown("".join(collected))

    status_placeholder.success(f"✅ 분석 완료")

    full_text = "".join(collected)
    report_path = save_report(query, full_text)

    st.session_state.reports.insert(0, {
        "query": query,
        "content": full_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "path": str(report_path),
    })

    st.download_button(
        "📥 리포트 다운로드 (.md)",
        data=full_text,
        file_name=report_path.name,
        mime="text/markdown",
    )

# ── Report History ────────────────────────────────────────────
if st.session_state.reports:
    st.divider()
    st.markdown("#### 📋 리서치 기록")
    for i, r in enumerate(st.session_state.reports):
        with st.expander(f"[{r['timestamp']}] {r['query'][:60]}"):
            st.markdown(r["content"])
            st.download_button(
                "📥 다운로드",
                data=r["content"],
                file_name=Path(r["path"]).name,
                mime="text/markdown",
                key=f"dl_{i}",
            )
