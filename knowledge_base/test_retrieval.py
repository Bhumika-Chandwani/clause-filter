import os
os.environ["HF_HOME"] = "D:/FYMCA/contract-checker/hf_cache"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import chromadb  # import chromadb BEFORE sentence_transformers/torch
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="knowledge_base/chroma_store")
collection = chroma_client.get_collection("clause_patterns")

test_clause = "This Agreement shall automatically renew for successive one-year terms unless either party gives 90 days written notice."
query_embedding = model.encode([test_clause]).tolist()

results = collection.query(query_embeddings=query_embedding, n_results=3)

for i in range(len(results["ids"][0])):
    print(f"\nMatch {i+1}:")
    print("ID:", results["ids"][0][i])
    print("Distance:", results["distances"][0][i])
    print("Category:", results["metadatas"][0][i]["project_category"])
    print("Risk:", results["metadatas"][0][i]["risk_level"])
    print("Text:", results["documents"][0][i][:150])