# spaced_repetition/progress_tracker_csv.py
import pandas as pd
import os
from datetime import date, timedelta

PROGRESS_FILE = "progress.csv"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        return pd.read_csv(PROGRESS_FILE)
    return pd.DataFrame(columns=["id", "question", "box", "last_review"])

def save_progress(df):
    df.to_csv(PROGRESS_FILE, index=False)

def init_question(qid, question):
    df = load_progress()
    if qid not in df["id"].values:
        new_row = pd.DataFrame([{
            "id": qid,
            "question": question,
            "box": 1,
            "last_review": str(date.today())
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_progress(df)

def update_progress(qid, correct):
    df = load_progress()
    if qid in df["id"].values:
        idx = df.index[df["id"] == qid][0]
        if correct:
            df.at[idx, "box"] = min(5, df.at[idx, "box"] + 1)
        else:
            df.at[idx, "box"] = 1
        df.at[idx, "last_review"] = str(date.today())
        save_progress(df)

def get_due_questions():
    df = load_progress()
    due = []
    for _, row in df.iterrows():
        box = row["box"]
        last = date.fromisoformat(str(row["last_review"]))
        interval = 0
        if date.today() >= last + timedelta(days=interval):
            due.append(row["id"])
    return due

def load_all_progress():
    return load_progress()
