import json
import random
from collections import defaultdict

with open("knowledge_base/clauses_cleaned.json", "r", encoding="utf-8") as f:
    clauses = json.load(f)

by_category = defaultdict(list)
for c in clauses:
    by_category[c["project_category"]].append(c)

random.seed(42)  # fixes the randomness so results are reproducible if you re-run this
sample = []
for category, items in by_category.items():
    # keep only reasonably readable lengths - not a one-word fragment, not a giant paragraph
    filtered = [c for c in items if 40 < len(c["clause_text"]) < 500]
    picked = random.sample(filtered, min(15, len(filtered)))
    sample.extend(picked)
    print(f"{category}: {len(filtered)} available after filtering, picked {len(picked)}")

print("\nTotal sampled:", len(sample))

with open("knowledge_base/clauses_sample.json", "w", encoding="utf-8") as f:
    json.dump(sample, f, indent=2)