# clean_notes.py
import re
import fitz  # PyMuPDF for PDF text extraction

def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file."""
    pdf = fitz.open(file_path)
    text = ""
    for page in pdf:
        text += page.get_text()
    return text

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def clean_text(text: str) -> str:
    """Clean raw notes text: remove newlines, multiple spaces, etc."""
    text = re.sub(r'\n+', ' ', text)     # collapse newlines
    text = re.sub(r'\s+', ' ', text)     # collapse multiple spaces
    text = text.strip()
    return text

if __name__ == "__main__":
    # Example usage (standalone run)
    file_path = input("Enter path of PDF or TXT file: ")

    if file_path.endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_path)
    elif file_path.endswith(".txt"):
        raw_text = extract_text_from_txt(file_path)
    else:
        raise ValueError("Unsupported file type. Use .pdf or .txt")

    cleaned = clean_text(raw_text)
    print("\n--- Cleaned Notes ---\n")
    print(cleaned[:1000])  # Print only first 1000 chars
