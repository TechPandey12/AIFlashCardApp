# spaced_repetition/progress_tracker_json.py
import json
import os
from datetime import date, timedelta

PROGRESS_FILE = "progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def init_question(qid, question):
    progress = load_progress()
    if qid not in progress:
        progress[qid] = {
            "question": question,
            "box": 1,
            "last_review": str(date.today())
        }
    save_progress(progress)

def update_progress(qid, correct):
    progress = load_progress()
    if qid in progress:
        if correct:
            progress[qid]["box"] = min(5, progress[qid]["box"] + 1)
        else:
            progress[qid]["box"] = 1
        progress[qid]["last_review"] = str(date.today())
    save_progress(progress)

def get_due_questions():
    progress = load_progress()
    due = []
    for qid, data in progress.items():
        box = data["box"]
        last = date.fromisoformat(data["last_review"])
        interval = 2 ** (box - 1)
        if date.today() >= last + timedelta(days=interval):
            due.append(qid)
    return due

def load_all_progress():
    return load_progress()
