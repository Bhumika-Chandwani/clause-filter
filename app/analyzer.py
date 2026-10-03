import os
os.environ["HF_HOME"] = os.path.join(os.path.dirname(__file__), "hf_cache")
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import json
import hashlib
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="../knowledge_base/chroma_store")
collection = chroma_client.get_collection("clause_patterns")


def get_groq_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY")  # fallback for local dev


groq_client = Groq(api_key=get_groq_key())

ANALYSIS_PROMPT = """You are a contract risk analysis assistant. Compare the uploaded contract clause below against similar known clause patterns, and judge its risk level.

Uploaded clause:
"{clause_text}"

Similar known patterns for reference:
{reference_patterns}

Respond with ONLY a JSON object, no other text:
{{
  "risk_level": "high" | "medium" | "low" | "neutral",
  "matched_category": "the category name from the closest reference pattern",
  "explanation": "one or two sentences explaining the risk, referencing what makes it similar or different from the reference patterns",
  "safer_alternative": "one or two sentences describing a fairer/more balanced version of this clause, or null if already fair"
}}
"""

DISTANCE_THRESHOLD = 0.85

cache_collection = chroma_client.get_or_create_collection("analysis_cache")

CACHE_DISTANCE_THRESHOLD = 0.05


def check_cache(clause_text, query_embedding):
    try:
        if cache_collection.count() == 0:
            return None
        results = cache_collection.query(query_embeddings=query_embedding, n_results=1)
        if results["distances"][0] and results["distances"][0][0] < CACHE_DISTANCE_THRESHOLD:
            return json.loads(results["metadatas"][0][0]["result_json"])
    except Exception:
        return None
    return None


def save_to_cache(clause_text, query_embedding, result):
    cache_id = hashlib.md5(clause_text.encode()).hexdigest()
    cache_collection.add(
        documents=[clause_text],
        embeddings=query_embedding,
        ids=[cache_id],
        metadatas=[{"result_json": json.dumps(result)}]
    )


def analyze_clause(clause_text):
    query_embedding = embed_model.encode([clause_text]).tolist()

    cached_result = check_cache(clause_text, query_embedding)
    if cached_result is not None:
        cached_result["from_cache"] = True
        return cached_result

    results = collection.query(query_embeddings=query_embedding, n_results=3)
    top_distance = results["distances"][0][0]

    if top_distance > DISTANCE_THRESHOLD:
        result = {
            "risk_level": "not_applicable",
            "matched_category": None,
            "explanation": "This clause does not closely match any known risk pattern category (likely administrative/boilerplate content).",
            "top_distance": top_distance,
            "from_cache": False
        }
        save_to_cache(clause_text, query_embedding, result)
        return result

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
    result["from_cache"] = False

    save_to_cache(clause_text, query_embedding, result)
    return result