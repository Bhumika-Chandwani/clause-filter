import pymupdf as fitz
import re
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def clean_pdf_artifacts(text):
    text = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s*(AM|PM)', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\bEX-10\.\d+\b', '', text)
    text = re.sub(r'\n\s*\d{1,3}/\d{1,3}\s*\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text

HEADER_PATTERN = re.compile(
    r'\n[^\S\n]*(Section\s+\d+\.\d+\.?)[^\S\n]+([A-Z][A-Za-z0-9 ,;:/&\'\-]{2,80}?)(?:\.(?=\s)|\n|[^\S\n]{2,})',
)

def clean_pdf_artifacts(text):
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s*(AM|PM)', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\bEX-10\.\d+\b', '', text)
    text = re.sub(r'\n\s*\d{1,3}/\d{1,3}\s*\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text


def strip_table_of_contents(text, header_pattern):
    matches = list(header_pattern.finditer(text))
    if not matches:
        return text

    def normalize(s):
        return re.sub(r'\s+', ' ', s).strip()

    first_header_number = normalize(matches[0].group(1))
    same_number_matches = [m for m in matches if normalize(m.group(1)) == first_header_number]

    if len(same_number_matches) >= 2:
        body_start = same_number_matches[1].start()
        return text[body_start:]

    return text


def split_into_clauses(text):
    text = clean_pdf_artifacts(text)
    text = strip_table_of_contents(text, HEADER_PATTERN)
    matches = list(HEADER_PATTERN.finditer(text))
    clauses = []

    for i, match in enumerate(matches):
        header_number = match.group(1).strip()
        header_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        clause_text = text[start:end].strip()

        if len(clause_text) > 150:
            clauses.append({
                "header_number": header_number,
                "header_title": header_title,
                "clause_text": clause_text
            })

    return clauses