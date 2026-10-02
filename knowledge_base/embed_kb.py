import os
os.environ["HF_HOME"] = "D:/FYMCA/contract-checker/hf_cache"

import json
import chromadb
from sentence_transformers import SentenceTransformer

with open("knowledge_base/clauses_final.json", "r", encoding="utf-8") as f:
    clauses = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")  # small, fast, good enough for this scale

chroma_client = chromadb.PersistentClient(path="knowledge_base/chroma_store")
collection = chroma_client.get_or_create_collection("clause_patterns")

documents = [c["clause_text"] for c in clauses]
embeddings = model.encode(documents).tolist()
ids = [c["id"] for c in clauses]
metadatas = [
    {
        "project_category": c["project_category"],
        "risk_level": c["risk_level"],
        "why_risky": c["why_risky"],
        "safer_alternative": c["safer_alternative"] or "",
    }
    for c in clauses
]

collection.add(documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas)
print(f"Added {len(clauses)} entries to Chroma collection.")