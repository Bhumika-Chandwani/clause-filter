import os
os.environ["HF_HOME"] = "D:/FYMCA/contract-checker/hf_cache"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="../knowledge_base/chroma_store")
collection = chroma_client.get_collection("clause_patterns")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

ANALYSIS_PROMPT = """You are a contract risk analysis assistant. Compare the uploaded contract clause below against similar known clause patterns, and judge its risk level.

Uploaded clause:
"{clause_text}"

Similar known patterns for reference:
{reference_patterns}

Respond with ONLY a JSON object, no other text:
{{
  "risk_level": "high" | "medium" | "low" | "neutral",
  "matched_category": "the category name from the closest reference pattern",
  "explanation": "one or two sentences explaining the risk, referencing what makes it similar or different from the reference patterns"
}}
"""
DISTANCE_THRESHOLD = 0.85 

def analyze_clause(clause_text):
    query_embedding = embed_model.encode([clause_text]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=3)

    top_distance = results["distances"][0][0]

    if top_distance > DISTANCE_THRESHOLD:
        return {
            "risk_level": "not_applicable",
            "matched_category": None,
            "explanation": "This clause does not closely match any known risk pattern category (likely administrative/boilerplate content).",
            "top_distance": top_distance
        }

    reference_patterns = ""
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        reference_patterns += f"- Category: {meta['project_category']}, Risk: {meta['risk_level']}, Pattern: {results['documents'][0][i][:200]}\n  Why: {meta['why_risky']}\n\n"

    prompt = ANALYSIS_PROMPT.format(clause_text=clause_text, reference_patterns=reference_patterns)

    response = groq_client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "", 1).strip()

    result = json.loads(raw)
    result["top_distance"] = top_distance
    return result