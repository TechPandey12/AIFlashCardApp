# 7.4-progress/progress_tracker.py

import pandas as pd
from datetime import datetime

# File where quiz history will be stored
HISTORY_FILE = "quiz_history.csv"

def save_quiz_result(score, total):
    """
    Save one quiz attempt into a history log CSV.
    Each row will have: date, score, total, accuracy.
    """
    result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "score": score,
        "total": total,
        "accuracy": round((score / total) * 100, 2) if total > 0 else 0
    }

    try:
        df = pd.read_csv(HISTORY_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["date", "score", "total", "accuracy"])

    # Append new result
    df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)

    # Save back to CSV
    df.to_csv(HISTORY_FILE, index=False)


def load_history():
    """
    Load all past quiz attempts from the history log.
    Returns a DataFrame with date, score, total, accuracy.
    """
    try:
        return pd.read_csv(HISTORY_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "score", "total", "accuracy"])
