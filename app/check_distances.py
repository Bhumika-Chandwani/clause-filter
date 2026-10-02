from parser import extract_text_from_pdf, split_into_clauses
from analyzer import embed_model, collection

text = extract_text_from_pdf("../data/sample_contract.pdf")
clauses = split_into_clauses(text)

for c in clauses:
    query_embedding = embed_model.encode([c["clause_text"]]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=1)
    top_distance = results["distances"][0][0]
    print(f"{top_distance:.4f}  [{c['header_number']}] {c['header_title']}")