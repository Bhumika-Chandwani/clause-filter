import json
import re

with open("data/cuad/CUADv1.json", "r", encoding="utf-8") as f:
    cuad = json.load(f)

# maps your project's category name -> list of real CUAD category names
CATEGORY_MAP = {
    "Auto-Renewal & Termination": ["Renewal Term", "Notice Period To Terminate Renewal", "Termination For Convenience"],
    "Liability": ["Cap On Liability", "Uncapped Liability"],
    "IP Ownership & Licensing": ["Ip Ownership Assignment", "License Grant"],
    "Competitive Restrictions": ["Non-Compete", "Exclusivity", "No-Solicit Of Employees"],
    "Risk & Compliance Obligations": ["Audit Rights", "Insurance", "Warranty Duration"],
    "Commercial Commitments": ["Minimum Commitment"],
    "Governing Law": ["Governing Law"],
}

# reverse lookup: real CUAD category name -> your project's category name
cuad_to_project = {}
for project_cat, cuad_cats in CATEGORY_MAP.items():
    for c in cuad_cats:
        cuad_to_project[c] = project_cat

knowledge_base = []
entry_id = 0

for contract in cuad["data"]:
    contract_title = contract["title"]
    for para in contract["paragraphs"]:
        for qa in para["qas"]:
            match = re.search(r'related to "([^"]+)"', qa["question"])
            if not match:
                continue
            cuad_category = match.group(1)
            if cuad_category not in cuad_to_project:
                continue
            for answer in qa["answers"]:
                clause_text = answer["text"].strip()
                if len(clause_text) < 10:  # skip near-empty/junk answers
                    continue
                entry_id += 1
                knowledge_base.append({
                    "id": f"clause_{entry_id:04d}",
                    "project_category": cuad_to_project[cuad_category],
                    "cuad_category": cuad_category,
                    "contract_source": contract_title,
                    "clause_text": clause_text,
                })

print("Total entries collected:", len(knowledge_base))

with open("knowledge_base/clauses_raw.json", "w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, indent=2)

def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

with open("knowledge_base/clauses_raw.json", "r", encoding="utf-8") as f:
    clauses = json.load(f)

for c in clauses:
    c["clause_text"] = clean_text(c["clause_text"])

with open("knowledge_base/clauses_cleaned.json", "w", encoding="utf-8") as f:
    json.dump(clauses, f, indent=2)

print("Cleaned", len(clauses), "entries")

