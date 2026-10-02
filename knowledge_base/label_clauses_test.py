import json
import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

with open("knowledge_base/clauses_sample.json", "r", encoding="utf-8") as f:
    clauses = json.load(f)

PROMPT_TEMPLATE = """You are helping build a knowledge base for a contract risk-checking tool.

Given a clause from a real contract, classify it and explain the risk in plain English.

Category: {category}
Clause: "{clause_text}"

Respond with ONLY a JSON object, no other text, in this exact format:
{{
  "risk_level": "high" | "medium" | "low" | "neutral",
  "why_risky": "one sentence explaining why this risk level applies, in plain English",
  "safer_alternative": "one sentence describing a fairer/safer version of this clause, or null if the clause is already neutral/fair"
}}

Risk level guide:
- "high": clearly one-sided or harmful to the party receiving this clause
- "medium": somewhat unfavorable but not extreme, or ambiguous/vague wording that could be exploited
- "low": mostly standard/fair language with minor room for improvement
- "neutral": purely informational, not inherently risky (e.g. stating governing law, standard boilerplate)
"""

labeled = []
failed = []

for i, entry in enumerate(clauses):
    prompt = PROMPT_TEMPLATE.format(
        category=entry["project_category"],
        clause_text=entry["clause_text"]
    )
    try:
        response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}]
        )
        raw_text = response.choices[0].message.content.strip()
        # strip markdown code fences if the model wraps its JSON in them
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`").replace("json", "", 1).strip()

        label_data = json.loads(raw_text)
        entry.update(label_data)
        labeled.append(entry)
        print(f"[{i+1}/{len(clauses)}] Labeled: {entry['id']} - {label_data['risk_level']}")

    except Exception as e:
        print(f"[{i+1}/{len(clauses)}] FAILED: {entry['id']} - {e}")
        failed.append(entry)

    time.sleep(1)  # small pause to stay comfortably under free-tier rate limits

print(f"\nDone. Labeled: {len(labeled)}, Failed: {len(failed)}")

with open("knowledge_base/clauses_labeled_draft.json", "w", encoding="utf-8") as f:
    json.dump(labeled, f, indent=2)

if failed:
    with open("knowledge_base/clauses_failed.json", "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2)
    print("Failed entries saved to knowledge_base/clauses_failed.json for retry")