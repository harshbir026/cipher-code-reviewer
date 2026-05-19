"""
AI Code Review Agent — Streamlit Dashboard
Surgical Intelligence Terminal aesthetic.
"""

import logging

import pandas as pd
import streamlit as st

from pipeline.ingestion import RepositoryIngestor
from pipeline.parser import ASTParser
from pipeline.reviewer import LLMReviewer
from utils.token_counter import batch_code_blocks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

if "all_reviews" not in st.session_state:
    st.session_state.all_reviews = []
if "analysis_run" not in st.session_state:
    st.session_state.analysis_run = False

st.set_page_config(
    page_title="CIPHER // Code Intelligence",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@400;600;700;800&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
    background-color: #080808 !important;
    color: #E8E8E8 !important;
}

/* ── Scanline overlay on entire app ── */
body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #050505 !important;
    border-right: 1px solid #1A1A1A !important;
}
[data-testid="stSidebar"] * {
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── Sidebar inputs ── */
.stTextInput > div > div > input {
    background-color: #0D0D0D !important;
    color: #E8E8E8 !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    transition: border-color 0.15s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #F5A623 !important;
    box-shadow: 0 0 0 1px rgba(245,166,35,0.2) !important;
}
.stTextInput > div > div > input::placeholder {
    color: #444 !important;
}

/* ── Multiselect ── */
.stMultiSelect > div > div {
    background-color: #0D0D0D !important;
    border: 1px solid #2A2A2A !important;
    border-radius: 2px !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background-color: #1A1A1A !important;
    border: 1px solid #F5A623 !important;
    color: #F5A623 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    border-radius: 2px !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background-color: #F5A623 !important;
    color: #080808 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #FFB73D !important;
    transform: translateY(-1px) !important;
}

/* ── Secondary button ── */
.stButton > button:not([kind="primary"]) {
    background-color: transparent !important;
    color: #F5A623 !important;
    border: 1px solid #F5A623 !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.05em !important;
    transition: all 0.15s ease !important;
}
.stButton > button:not([kind="primary"]):hover {
    background-color: rgba(245,166,35,0.08) !important;
}

/* ── Toggle ── */
.stToggle > label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    color: #888 !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background-color: #0D0D0D !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
    margin-bottom: 8px !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stExpander"]:hover {
    border-color: #F5A623 !important;
}
[data-testid="stExpander"] summary {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    color: #CCC !important;
    background-color: #0D0D0D !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background-color: #0D0D0D !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.12em !important;
    color: #666 !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 28px !important;
    color: #F5A623 !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background-color: transparent !important;
    color: #F5A623 !important;
    border: 1px solid #F5A623 !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.05em !important;
    width: 100% !important;
}

/* ── Status boxes ── */
[data-testid="stStatusWidget"] {
    background-color: #0D0D0D !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
}

/* ── Divider ── */
hr {
    border-color: #1A1A1A !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #080808; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #F5A623; }

/* ── Custom component classes ── */
.cipher-header {
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2em;
    color: #F5A623;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.cipher-mono {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #666;
}
.severity-critical {
    display: inline-block;
    background: rgba(239,68,68,0.12);
    color: #F87171;
    border: 1px solid rgba(239,68,68,0.4);
    padding: 2px 10px;
    border-radius: 2px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.severity-high {
    display: inline-block;
    background: rgba(249,115,22,0.12);
    color: #FB923C;
    border: 1px solid rgba(249,115,22,0.4);
    padding: 2px 10px;
    border-radius: 2px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.severity-medium {
    display: inline-block;
    background: rgba(245,166,35,0.12);
    color: #F5A623;
    border: 1px solid rgba(245,166,35,0.4);
    padding: 2px 10px;
    border-radius: 2px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.severity-low {
    display: inline-block;
    background: rgba(99,102,241,0.12);
    color: #818CF8;
    border: 1px solid rgba(99,102,241,0.4);
    padding: 2px 10px;
    border-radius: 2px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.confidence-bar-outer {
    background: #1A1A1A;
    border-radius: 1px;
    height: 3px;
    width: 100%;
    margin-top: 6px;
}
.pipeline-step {
    background: #0D0D0D;
    border: 1px solid #1E1E1E;
    border-radius: 2px;
    padding: 12px 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #666;
    text-align: center;
    position: relative;
}
.pipeline-step.active {
    border-color: #F5A623;
    color: #F5A623;
}
.pipeline-step.done {
    border-color: #22C55E;
    color: #22C55E;
}
.finding-card {
    background: #0D0D0D;
    border: 1px solid #1E1E1E;
    border-left: 3px solid #F5A623;
    border-radius: 2px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 0.15s ease;
}
.finding-card:hover {
    border-color: #2A2A2A;
    border-left-color: #FFB73D;
}
.finding-card.critical { border-left-color: #EF4444; }
.finding-card.high     { border-left-color: #F97316; }
.finding-card.medium   { border-left-color: #F5A623; }
.finding-card.low      { border-left-color: #6366F1; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Helpers ────────────────────────────────────────────────────────────────────


@st.cache_data
def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def severity_badge(severity: str) -> str:
    cls = f"severity-{severity.lower()}"
    return f"<span class='{cls}'>{severity}</span>"


def confidence_bar(score: int) -> str:
    color = "#22C55E" if score >= 80 else "#F5A623" if score >= 60 else "#EF4444"
    return (
        f"<div class='confidence-bar-outer'>"
        f"<div style='width:{score}%;height:3px;background:{color};"
        f"border-radius:1px;transition:width 0.4s ease;'></div>"
        f"</div>"
    )


# ── Sidebar ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
    <div style='padding: 20px 0 16px 0;'>
        <div style='font-family:"Syne",sans-serif;font-size:18px;font-weight:800;
                    letter-spacing:-0.02em;color:#F5A623;'>CIPHER</div>
        <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;
                    color:#444;letter-spacing:0.2em;margin-top:2px;'>
            CODE INTELLIGENCE v1.0
        </div>
    </div>
    <div style='border-top:1px solid #1A1A1A;margin-bottom:20px;'></div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='cipher-header'>Target</div>",
        unsafe_allow_html=True,
    )
    repo_url = st.text_input(
        label="repo_url",
        label_visibility="collapsed",
        placeholder="https://github.com/owner/repo",
    )

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='cipher-header'>Severity Filter</div>",
        unsafe_allow_html=True,
    )
    severity_filter = st.multiselect(
        label="severity",
        label_visibility="collapsed",
        options=["Critical", "High", "Medium", "Low"],
        default=["Critical", "High", "Medium", "Low"],
    )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='cipher-header'>Category Filter</div>",
        unsafe_allow_html=True,
    )
    category_filter = st.multiselect(
        label="category",
        label_visibility="collapsed",
        options=[
            "Security",
            "Performance",
            "Bug",
            "Style",
            "Maintainability",
            "Documentation",
        ],
        default=[
            "Security",
            "Performance",
            "Bug",
            "Style",
            "Maintainability",
            "Documentation",
        ],
    )

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    show_low_confidence = st.toggle("Show low confidence flags", value=True)

    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='cipher-mono'>AST · GPT-4o-mini · tiktoken</div>",
        unsafe_allow_html=True,
    )


# ── Landing State ──────────────────────────────────────────────────────────────

if not repo_url and not st.session_state.analysis_run:
    st.markdown(
        """
    <div style='margin-top:8vh;'>
        <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;
                    color:#F5A623;letter-spacing:0.2em;margin-bottom:16px;'>
            // SYSTEM READY
        </div>
        <div style='font-family:"Syne",sans-serif;font-size:52px;font-weight:800;
                    letter-spacing:-0.04em;line-height:1;color:#E8E8E8;
                    margin-bottom:8px;'>
            Code under<br/>the microscope.
        </div>
        <div style='font-family:"IBM Plex Mono",monospace;font-size:13px;
                    color:#555;margin-top:20px;max-width:520px;line-height:1.8;'>
            Paste a GitHub repository URL in the sidebar.<br/>
            We clone, parse, and review every function<br/>
            with AST precision and zero hallucination tolerance.
        </div>
    </div>

    <div style='margin-top:48px;background:#0D0D0D;border:1px solid #1E1E1E;
                border-left:3px solid #F5A623;border-radius:2px;
                padding:24px 28px;max-width:620px;'>
        <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;
                    color:#444;margin-bottom:12px;letter-spacing:0.1em;'>
            PIPELINE PREVIEW
        </div>
        <div style='font-family:"IBM Plex Mono",monospace;font-size:12px;
                    color:#666;line-height:2;'>
            <span style='color:#F5A623;'>01</span> &nbsp;clone_repo(url, depth=1)
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <span style='color:#22C55E;'>// ephemeral</span><br/>
            <span style='color:#F5A623;'>02</span> &nbsp;ast.walk(tree)
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <span style='color:#22C55E;'>// FunctionDef + ClassDef</span><br/>
            <span style='color:#F5A623;'>03</span> &nbsp;tiktoken.batch(blocks, max=6000)
                &nbsp;
                <span style='color:#22C55E;'>// token-safe</span><br/>
            <span style='color:#F5A623;'>04</span> &nbsp;openai.parse(schema=CodeReviewReport)
                &nbsp;
                <span style='color:#22C55E;'>// structured output</span><br/>
            <span style='color:#F5A623;'>05</span> &nbsp;bucket(confidence >= 80)
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <span style='color:#22C55E;'>// epistemic humility</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.stop()


# ── Header + Run Button ────────────────────────────────────────────────────────

col_title, col_btn = st.columns([5, 1])
with col_title:
    if repo_url:
        st.markdown(
            f'<div style=\'font-family:"IBM Plex Mono",monospace;font-size:11px;'
            f"color:#555;margin-bottom:4px;'>TARGET</div>"
            f'<div style=\'font-family:"IBM Plex Mono",monospace;font-size:13px;'
            f"color:#F5A623;'>{repo_url}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style=\'font-family:"IBM Plex Mono",monospace;'
            "font-size:13px;color:#444;'>// awaiting target</div>",
            unsafe_allow_html=True,
        )

with col_btn:
    run_button = st.button(
        "► SCAN",
        type="primary",
        disabled=not repo_url,
        use_container_width=True,
    )

st.markdown(
    "<div style='border-top:1px solid #1A1A1A;margin:16px 0 24px 0;'></div>",
    unsafe_allow_html=True,
)


# ── Pipeline Execution ─────────────────────────────────────────────────────────

if run_button and repo_url:
    st.session_state.all_reviews = []
    st.session_state.analysis_run = False

    # Step 1 — Clone
    with st.status("01 // CLONING REPOSITORY", expanded=True) as s1:
        try:
            ingestor = RepositoryIngestor(repo_url)
            temp_dir = ingestor.clone_and_get_path()
            s1.update(label="01 // REPOSITORY CLONED ✓", state="complete")
        except (ValueError, RuntimeError) as e:
            s1.update(label="01 // CLONE FAILED ✗", state="error")
            st.error(f"Clone error: {e}")
            st.stop()

    # Step 2 — Parse
    with st.status("02 // AST PARSING", expanded=True) as s2:
        code_blocks = ASTParser.extract_code_blocks(temp_dir.name)
        temp_dir.cleanup()
        if not code_blocks:
            s2.update(label="02 // NO PYTHON BLOCKS FOUND ✗", state="error")
            st.warning("No Python functions or classes found in this repository.")
            st.stop()
        batches = batch_code_blocks(code_blocks)
        s2.update(
            label=f"02 // AST COMPLETE ✓  [{len(code_blocks)} blocks → {len(batches)} batches]",
            state="complete",
        )

    # Step 3 — LLM
    with st.status("03 // RUNNING AI ANALYSIS", expanded=True) as s3:
        try:
            reviewer = LLMReviewer()
        except EnvironmentError as e:
            s3.update(label="03 // CONFIG ERROR ✗", state="error")
            st.error(str(e))
            st.stop()

        progress = st.progress(0)
        batch_txt = st.empty()

        def update_progress(current: int, total: int):
            progress.progress(current / total)
            batch_txt.markdown(
                f'<span style=\'font-family:"IBM Plex Mono",monospace;'
                f"font-size:11px;color:#666;'>"
                f"batch {current:02d}/{total:02d} &nbsp;·&nbsp; "
                f"{int(current/total*100)}% complete</span>",
                unsafe_allow_html=True,
            )

        try:
            all_reviews = reviewer.analyze_all_batches(batches, update_progress)
            st.session_state.all_reviews = all_reviews
            st.session_state.analysis_run = True
        except RuntimeError as e:
            s3.update(label="03 // INFERENCE FAILED ✗", state="error")
            st.error(str(e))
            st.stop()

        batch_txt.empty()
        s3.update(
            label=f"03 // ANALYSIS COMPLETE ✓  [{len(all_reviews)} findings]",
            state="complete",
        )


# ── Results ────────────────────────────────────────────────────────────────────

all_reviews = st.session_state.all_reviews

if not all_reviews:
    if st.session_state.analysis_run:
        st.markdown(
            """
        <div style='text-align:center;padding:60px 0;'>
            <div style='font-family:"IBM Plex Mono",monospace;font-size:32px;
                        color:#22C55E;margin-bottom:12px;'>✓</div>
            <div style='font-family:"Syne",sans-serif;font-size:20px;
                        font-weight:700;color:#E8E8E8;'>Clean codebase.</div>
            <div style='font-family:"IBM Plex Mono",monospace;font-size:12px;
                        color:#555;margin-top:8px;'>
                No actionable issues identified. Zero findings.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    st.stop()

df = pd.DataFrame([r.model_dump() for r in all_reviews])

df_filtered = df[
    df["severity"].isin(severity_filter) & df["issue_category"].isin(category_filter)
]
if not show_low_confidence:
    df_filtered = df_filtered[~df_filtered["needs_verification"]]

# ── Metrics Row ────────────────────────────────────────────────────────────────

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("TOTAL FLAGS", len(df))
m2.metric("CRITICAL", len(df[df["severity"] == "Critical"]))
m3.metric("HIGH", len(df[df["severity"] == "High"]))
m4.metric("VERIFY", int(df["needs_verification"].sum()))
m5.metric("AVG CONFIDENCE", f"{df['confidence_score'].mean():.0f}%")

st.markdown(
    "<div style='border-top:1px solid #1A1A1A;margin:20px 0;'></div>",
    unsafe_allow_html=True,
)

# ── Split Layout ───────────────────────────────────────────────────────────────

left, right = st.columns([6, 4], gap="large")

high_conf_df = df_filtered[~df_filtered["needs_verification"]]
low_conf_df = df_filtered[df_filtered["needs_verification"]]

with left:
    st.markdown(
        "<div class='cipher-header'>High Confidence Findings</div>"
        "<div class='cipher-mono' style='margin-bottom:16px;'>"
        f"confidence ≥ 80% &nbsp;·&nbsp; {len(high_conf_df)} findings"
        "</div>",
        unsafe_allow_html=True,
    )

    if high_conf_df.empty:
        st.markdown(
            '<div style=\'font-family:"IBM Plex Mono",monospace;font-size:12px;'
            "color:#444;padding:24px 0;'>// no findings match current filters</div>",
            unsafe_allow_html=True,
        )
    else:
        for _, row in high_conf_df.iterrows():
            sev = row["severity"].lower()
            badge = severity_badge(row["severity"])
            bar = confidence_bar(row["confidence_score"])

            with st.expander(
                f"[{row['issue_category'].upper()}] {row['file_path']} → {row['function_name']}",
                expanded=False,
            ):
                st.markdown(
                    f"{badge}"
                    f"&nbsp;&nbsp;<span style='font-family:\"IBM Plex Mono\",monospace;"
                    f"font-size:11px;color:#555;'>line {row['line_number']} &nbsp;·&nbsp; "
                    f"confidence {row['confidence_score']}%</span>"
                    f"{bar}",
                    unsafe_allow_html=True,
                )
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:12px;"
                    f"color:#CCC;line-height:1.7;'>{row['comment']}</div>",
                    unsafe_allow_html=True,
                )
                if row.get("suggested_fix", "").strip():
                    st.markdown(
                        '<div style=\'font-family:"IBM Plex Mono",monospace;'
                        "font-size:10px;color:#F5A623;letter-spacing:0.1em;"
                        "margin:14px 0 6px 0;'>SUGGESTED FIX</div>",
                        unsafe_allow_html=True,
                    )
                    st.code(row["suggested_fix"], language="python")

with right:
    st.markdown(
        "<div class='cipher-header'>Needs Verification</div>"
        "<div class='cipher-mono' style='margin-bottom:16px;'>"
        f"confidence &lt; 80% &nbsp;·&nbsp; {len(low_conf_df)} flags"
        "</div>",
        unsafe_allow_html=True,
    )

    if low_conf_df.empty:
        st.markdown(
            '<div style=\'font-family:"IBM Plex Mono",monospace;font-size:12px;'
            "color:#444;padding:24px 0;'>// no low-confidence flags</div>",
            unsafe_allow_html=True,
        )
    else:
        for _, row in low_conf_df.iterrows():
            badge = severity_badge(row["severity"])
            bar = confidence_bar(row["confidence_score"])
            st.markdown(
                f"<div style='background:#0D0D0D;border:1px solid #1E1E1E;"
                f"border-left:3px solid #333;border-radius:2px;"
                f"padding:12px 16px;margin-bottom:8px;'>"
                f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:11px;"
                f"color:#888;margin-bottom:6px;'>"
                f"{row['file_path']} → <span style='color:#CCC;'>{row['function_name']}</span>"
                f"</div>"
                f"<div>{badge}&nbsp;&nbsp;"
                f"<span style='font-family:\"IBM Plex Mono\",monospace;font-size:10px;"
                f"color:#555;'>{row['confidence_score']}% confidence</span></div>"
                f"{bar}"
                f"<div style='font-family:\"IBM Plex Mono\",monospace;font-size:11px;"
                f"color:#666;margin-top:8px;line-height:1.6;'>{row['comment'][:160]}..."
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Export ─────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='border-top:1px solid #1A1A1A;margin:24px 0 16px 0;'></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='cipher-header'>Export</div>",
        unsafe_allow_html=True,
    )
    csv_data = convert_df_to_csv(df)
    st.download_button(
        label="⬇ DOWNLOAD FULL REPORT (.CSV)",
        data=csv_data,
        file_name="cipher_review_report.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style=\'font-family:"IBM Plex Mono",monospace;font-size:10px;'
        f"color:#333;text-align:center;'>"
        f"{len(df)} findings &nbsp;·&nbsp; "
        f"{len(high_conf_df)} actionable &nbsp;·&nbsp; "
        f"{len(low_conf_df)} flagged"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Bonus: GitHub PR Integration ───────────────────
    st.divider()
    st.subheader("🐙 Post to GitHub Pull Request (Bonus Feature)")
    st.caption(
        "Post the top findings directly as inline review comments on a live GitHub PR."
    )

    with st.expander("Configure PR Integration"):
        gh_repo = st.text_input(
            "Repository (owner/name format)",
            placeholder="e.g., torvalds/linux",
        )
        gh_pr_number = st.number_input(
            "Pull Request Number", min_value=1, value=1, step=1
        )
        max_comments = st.slider("Maximum comments to post", 1, 20, 5)

        if st.button("📝 Post Comments to PR") and gh_repo:
            try:
                from utils.github_api import GitHubReviewer

                gh_reviewer = GitHubReviewer()
                reviews_dicts = [r.model_dump() for r in all_reviews]
                result = gh_reviewer.post_batch_comments(
                    repo_name=gh_repo,
                    pr_number=int(gh_pr_number),
                    reviews=reviews_dicts,
                    max_comments=max_comments,
                )
                st.success(
                    f"✅ Done! Posted: {result['posted']} | "
                    f"Skipped: {result['skipped']} | "
                    f"Failed: {result['failed']}"
                )
            except EnvironmentError as e:
                st.error(f"❌ {e}")
            except RuntimeError as e:
                st.error(f"❌ {e}")
