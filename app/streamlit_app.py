import os
os.environ["HF_HOME"] = os.path.join(os.path.dirname(__file__), "hf_cache")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import tempfile
import plotly.graph_objects as go
from datetime import datetime
from parser import extract_text_from_pdf, split_into_clauses
from analyzer import analyze_clause

st.set_page_config(page_title="Clause Filter | Contract Risk Analyzer", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.block-container { padding-top: 2rem; max-width: 1200px; }

/* Header */
.app-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1.2rem 1.8rem; border-radius: 14px; margin-bottom: 1.5rem;
    background: linear-gradient(135deg, #0f1b1e 0%, #132a2a 100%);
    border: 1px solid #1e3a3a;
}
.app-header h1 { color: #e2e8f0; font-size: 1.6rem; margin: 0; font-weight: 700; }
.app-header .tagline { color: #5eead4; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; margin-top: 2px; }
.app-header .badge { background: #134e4a; color: #5eead4; padding: 5px 14px; border-radius: 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; border: 1px solid #14b8a6; }

/* Card */
.card {
    background: #131d23; border: 1px solid #1f2d35; border-radius: 14px;
    padding: 1.3rem 1.5rem; margin-bottom: 1rem;
}
.card-label { color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }
.card-value { font-size: 1.8rem; font-weight: 700; color: #e2e8f0; margin-top: 4px; }

/* Score ring */
.score-ring {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 1.5rem; border-radius: 16px; height: 100%;
}
.score-number { font-family: 'JetBrains Mono', monospace; font-size: 3rem; font-weight: 700; line-height: 1; }
.score-grade { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; margin-top: 0.5rem; font-weight: 600; letter-spacing: 0.03em; }

.clause-tag {
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #5eead4;
    background: #0f2927; padding: 3px 10px; border-radius: 6px; border: 1px solid #1e4a46;
}

/* Download button highlight */
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #14b8a6, #0d9488) !important;
    color: #04181a !important; font-weight: 700 !important;
    border: none !important; padding: 0.8rem 2rem !important;
    border-radius: 10px !important; font-size: 1rem !important;
    box-shadow: 0 4px 20px rgba(20, 184, 166, 0.35) !important;
}
div[data-testid="stDownloadButton"] button:hover {
    box-shadow: 0 6px 28px rgba(20, 184, 166, 0.55) !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

# ---- Sidebar ----
with st.sidebar:
    st.markdown("Clause Filter")
    st.markdown("<span style='color:#64748b; font-family:JetBrains Mono, monospace; font-size:0.78rem;'>RAG-powered contract risk analysis</span>", unsafe_allow_html=True)
    st.markdown("**How it works**")
    st.caption("1. Upload a service agreement PDF\n2. Clauses are parsed & embedded\n3. Matched against known risk patterns\n4. Flagged with explanations & fixes")


# ---- Header ----
st.markdown("""
<div class="app-header">
    <div>
        <h1>Contract Risk Analyzer</h1>
        <div class="tagline">&gt; upload a service agreement to scan for risky clauses</div>
    </div>
    <div class="badge">● LIVE</div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("Parsing contract structure..."):
        text = extract_text_from_pdf(tmp_path)
        clauses = split_into_clauses(text)

    st.success(f"✓ Parsed {len(clauses)} clauses — running risk analysis")

    progress_bar = st.progress(0)
    results = []
    for i, c in enumerate(clauses):
        result = analyze_clause(c["clause_text"])
        results.append({**c, **result})
        progress_bar.progress((i + 1) / len(clauses))
    progress_bar.empty()

    summary = {"high": 0, "medium": 0, "low": 0, "neutral": 0, "not_applicable": 0}
    for r in results:
        summary[r["risk_level"]] = summary.get(r["risk_level"], 0) + 1

    weighted = summary.get("high", 0) * 15 + summary.get("medium", 0) * 7 + summary.get("low", 0) * 2
    max_possible = len(results) * 15
    risk_score = min(100, round((weighted / max_possible) * 100)) if max_possible else 0

    if risk_score >= 60:
        score_color, grade = "#f87171", "HIGH RISK"
    elif risk_score >= 30:
        score_color, grade = "#fbbf24", "MODERATE RISK"
    else:
        score_color, grade = "#34d399", "LOW RISK"

    # ---- Top row: score + metric cards ----
    col_score, col_cards = st.columns([1, 2.6])
    with col_score:
        st.markdown(f"""
        <div class="card score-ring" style="border-color:{score_color}33; background: linear-gradient(145deg, #131d23, {score_color}0d);">
            <div class="score-number" style="color:{score_color};">{risk_score}</div>
            <div class="score-grade" style="color:{score_color};">{grade}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_cards:
        m1, m2, m3, m4 = st.columns(4)
        metrics = [("🔴 High", summary.get("high", 0), "#f87171"), ("🟡 Medium", summary.get("medium", 0), "#fbbf24"),
                   ("🟢 Low", summary.get("low", 0), "#34d399"), ("⚪ Info", summary.get("neutral", 0), "#94a3b8")]
        for col, (label, val, color) in zip([m1, m2, m3, m4], metrics):
            col.markdown(f"""<div class="card"><div class="card-label">{label}</div><div class="card-value" style="color:{color};">{val}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="card"><div class="card-label">Clauses Analyzed</div><div class="card-value">{len(results)}</div></div>""", unsafe_allow_html=True)

    # ---- Chart ----
    st.markdown("#### Risk Distribution")
    chart_labels, chart_values, chart_colors = [], [], []
    color_map = {"high": "#f87171", "medium": "#fbbf24", "low": "#34d399", "neutral": "#94a3b8", "not_applicable": "#1f2d35"}
    for level, count in summary.items():
        if count > 0:
            chart_labels.append(level.replace("_", " ").title())
            chart_values.append(count)
            chart_colors.append(color_map.get(level, "#334155"))

    fig = go.Figure(data=[go.Pie(labels=chart_labels, values=chart_values, marker=dict(colors=chart_colors, line=dict(color="#0a0e14", width=2)), hole=0.6)])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, paper_bgcolor="rgba(0,0,0,0)",
                       font=dict(color="#94a3b8"), showlegend=True, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig, use_container_width=True)

    # ---- Flagged clauses ----
    st.markdown("#### Flagged Clauses")
    risk_order = {"high": 0, "medium": 1, "low": 2, "neutral": 3, "not_applicable": 4}
    flagged = sorted([r for r in results if r["risk_level"] != "not_applicable"], key=lambda r: risk_order.get(r["risk_level"], 5))
    risk_colors = {"high": "🔴", "medium": "🟡", "low": "🟢", "neutral": "⚪"}

    for r in flagged:
        icon = risk_colors.get(r["risk_level"], "⚪")
        cache_badge = " ⚡" if r.get("from_cache") else ""
        with st.expander(f"{icon} [{r['header_number']}] {r['header_title']} — {r['risk_level'].upper()}{cache_badge}"):
            st.markdown(f'<span class="clause-tag">{r.get("matched_category") or "N/A"}</span>', unsafe_allow_html=True)
            st.write("")
            st.write("**Explanation:**", r["explanation"])
            if r.get("safer_alternative"):
                st.write("**💡 Suggested alternative:**", r["safer_alternative"])
            st.write("**Original clause text:**")
            st.text_area("clause", r["clause_text"], height=150, label_visibility="collapsed", key=r["header_number"])

    # ---- Download report, highlighted, at the end ----
    report_lines = [
        f"CONTRACT RISK ANALYSIS REPORT", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"File: {uploaded_file.name}", f"Overall Risk Score: {risk_score}/100 ({grade})",
        f"Clauses analyzed: {len(results)}",
        f"High: {summary.get('high',0)} | Medium: {summary.get('medium',0)} | Low: {summary.get('low',0)} | Informational: {summary.get('neutral',0)}",
        "=" * 70,
    ]
    for r in flagged:
        report_lines.append(f"\n[{r['header_number']}] {r['header_title']} — {r['risk_level'].upper()}")
        report_lines.append(f"Category: {r.get('matched_category') or 'N/A'}")
        report_lines.append(f"Explanation: {r['explanation']}")
        if r.get("safer_alternative"):
            report_lines.append(f"Suggested alternative: {r['safer_alternative']}")
        report_lines.append("-" * 70)
    report_text = "\n".join(report_lines)

    st.divider()
    st.markdown("<div style='text-align:center; padding: 1rem 0;'>", unsafe_allow_html=True)
    st.download_button("Download Full Risk Report", report_text, file_name=f"risk_report_{uploaded_file.name}.txt", use_container_width=False)
    st.markdown("</div>", unsafe_allow_html=True)

    os.remove(tmp_path)