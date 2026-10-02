import os
os.environ["HF_HOME"] = "D:/FYMCA/contract-checker/hf_cache"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
import tempfile
from parser import extract_text_from_pdf, split_into_clauses
from analyzer import analyze_clause

st.set_page_config(page_title="Contract Compliance Checker", layout="wide")
st.title("📄 Contract Compliance Checker")
st.write("Upload a service agreement (PDF) to check for risky clauses.")

uploaded_file = st.file_uploader("Choose a PDF", type="pdf")

if uploaded_file is not None:
    # save uploaded file to a temp path so PyMuPDF can open it
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("Extracting and parsing contract..."):
        text = extract_text_from_pdf(tmp_path)
        clauses = split_into_clauses(text)

    st.success(f"Found {len(clauses)} clauses. Analyzing each one...")

    progress_bar = st.progress(0)
    results = []

    for i, c in enumerate(clauses):
        result = analyze_clause(c["clause_text"])
        results.append({**c, **result})
        progress_bar.progress((i + 1) / len(clauses))

    progress_bar.empty()

    # summary counts
    summary = {"high": 0, "medium": 0, "low": 0, "neutral": 0, "not_applicable": 0}
    for r in results:
        summary[r["risk_level"]] = summary.get(r["risk_level"], 0) + 1

    st.subheader("Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("High Risk", summary.get("high", 0))
    col2.metric("Medium Risk", summary.get("medium", 0))
    col3.metric("Low Risk", summary.get("low", 0))
    col4.metric("Informational", summary.get("neutral", 0))

    st.subheader("Flagged Clauses")

    risk_order = {"high": 0, "medium": 1, "low": 2, "neutral": 3, "not_applicable": 4}
    flagged = [r for r in results if r["risk_level"] != "not_applicable"]
    flagged.sort(key=lambda r: risk_order.get(r["risk_level"], 5))

    risk_colors = {"high": "🔴", "medium": "🟡", "low": "🟢", "neutral": "⚪"}

    for r in flagged:
        icon = risk_colors.get(r["risk_level"], "⚪")
        with st.expander(f"{icon} [{r['header_number']}] {r['header_title']} — {r['risk_level'].upper()}"):
            st.write("**Explanation:**", r["explanation"])
            st.write("**Matched category:**", r.get("matched_category") or "N/A")
            st.write("**Original clause text:**")
            st.text(r["clause_text"][:1000])

    os.remove(tmp_path)  # clean up the temp file