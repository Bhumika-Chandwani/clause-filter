import time
from parser import extract_text_from_pdf, split_into_clauses
from analyzer import analyze_clause

PDF_PATH = "../data/sample_contract.pdf"

text = extract_text_from_pdf(PDF_PATH)
clauses = split_into_clauses(text)

report = []

for i, c in enumerate(clauses):
    print(f"Analyzing [{i+1}/{len(clauses)}] {c['header_number']} {c['header_title']}...")
    try:
        result = analyze_clause(c["clause_text"])
        report.append({
            "header_number": c["header_number"],
            "header_title": c["header_title"],
            "clause_text": c["clause_text"],
            **result
        })
    except Exception as e:
        print(f"  FAILED: {e}")
    time.sleep(1)  # stay comfortably within rate limits

# summary counts
summary = {"high": 0, "medium": 0, "low": 0, "not_applicable": 0}
for r in report:
    summary[r["risk_level"]] = summary.get(r["risk_level"], 0) + 1

print("\n" + "=" * 50)
print("SUMMARY:", summary)

import json
with open("../data/report_output.json", "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "clauses": report}, f, indent=2)

print("\nFull report saved to data/report_output.json")