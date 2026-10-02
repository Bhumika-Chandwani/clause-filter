from parser import extract_text_from_pdf, clean_pdf_artifacts, HEADER_PATTERN

text = extract_text_from_pdf("../data/sample_contract.pdf")
text = clean_pdf_artifacts(text)

matches = list(HEADER_PATTERN.finditer(text))
for m in matches:
    print(f"pos={m.start():6d}  [{m.group(1)}]  {m.group(2)}")