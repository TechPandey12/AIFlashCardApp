# qna_generator.py
import pandas as pd
from transformers import pipeline
import sys

def generate_qna(text: str, num_questions: int = 10):
    """Generate Q&A pairs from given text using Hugging Face pipelines."""
    # Load pipeline
    qg_pipeline = pipeline("question-generation", model="iarfmoose/t5-base-question-generator")

    # Generate Q&A
    qa_pairs = qg_pipeline(text)

    # Convert to list of dicts (Q/A)
    qna_data = []
    for item in qa_pairs:
        qna_data.append({
            "question": item['question'],
            "answer": item['answer']
        })

    # Trim to required number
    return qna_data[:num_questions]

def save_qna_to_csv(qna_data, file_path="qna_pairs.csv"):
    """Save Q&A pairs into a CSV file."""
    df = pd.DataFrame(qna_data)
    df.to_csv(file_path, index=False, encoding="utf-8")
    print(f"✅ Saved {len(qna_data)} Q&A pairs to {file_path}")

if __name__ == "__main__":
    # Example usage (standalone run)
    if len(sys.argv) < 2:
        print("Usage: python qna_generator.py 'Your text here'")
        sys.exit(1)

    input_text = sys.argv[1]
    qna = generate_qna(input_text, num_questions=15)
    save_qna_to_csv(qna)
