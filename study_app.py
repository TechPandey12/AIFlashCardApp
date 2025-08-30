# study_app.py
"""
Study App (Streamlit) single-file:
Tabs:
- Upload Notes (PDF/TXT) -> store bytes in session
- Flashcards -> GPT-generated concept/formula flashcards (definitions/formulas only)
- Spaced Repetition -> Leitner boxes (Box1-hard, Box2-medium, Box3-easy)
- Quiz -> MCQs (generated from same upload) + hard-pool handling
- Review Mistakes -> mistakes recorded from quizzes
- Progress -> SQLite chart of past attempts by subject

Persistence:
- SQLite database "study_app.db" with tables: flashcards, qa_pairs, progress, mistakes
"""

import streamlit as st
import re
import os
import json
import random
import sqlite3
import datetime
from io import BytesIO

# Optional libs
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except Exception:
    HAS_PDFPLUMBER = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except Exception:
    HAS_PYMUPDF = False

# OpenAI (preferred) - used for better flashcards and MCQs
try:
    import openai
    HAS_OPENAI = True
    openai_api_key = os.getenv("OPENAI_API_KEY", None)
    if openai_api_key:
        openai.api_key = openai_api_key
except Exception:
    HAS_OPENAI = False

# Streamlit setup
st.set_page_config(page_title="📘 Study App (Leitner + GPT)", layout="wide")

# CSS theme (soft blue + white)
st.markdown(
    """
    <style>
      body {background-color:#f8fbff;}
      .main {background:#ffffff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);}
      .flashcard{background:#eef5ff;border-radius:10px;padding:12px;margin-bottom:10px;border-left:4px solid #4a90e2;}
      .small-muted {color: #6b7280; font-size:12px;}
      .btn-primary > button {background-color:#4a90e2;color:white;border-radius:8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Session-state initialization (do this BEFORE navigation widget)
# ---------------------------
if "uploaded_bytes" not in st.session_state:
    st.session_state.uploaded_bytes = None
if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = None
if "subject" not in st.session_state:
    st.session_state.subject = "General"
if "flashcards_loaded" not in st.session_state:
    st.session_state.flashcards_loaded = False
if "qa_loaded" not in st.session_state:
    st.session_state.qa_loaded = False
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "progress" not in st.session_state:
    st.session_state.progress = {"correct": 0, "wrong": 0}
if "quiz_pool_hard" not in st.session_state:
    st.session_state.quiz_pool_hard = []
if "use_hard_pool" not in st.session_state:
    st.session_state.use_hard_pool = False
# redirect mechanism: set redirect_to before nav widget to programmatically switch page
if "redirect_to" not in st.session_state:
    st.session_state.redirect_to = None

# ---------------------------
# Database (SQLite) setup
# ---------------------------
DB = "study_app.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # flashcards table stores individual flashcards for subject
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        question TEXT,
        answer TEXT,
        box INTEGER DEFAULT 1,
        last_reviewed TEXT
    )
    """
    )
    # qa_pairs table stores MCQs generated for quizzes (options stored as JSON)
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS qa_pairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        question TEXT,
        options_json TEXT,
        answer TEXT,
        difficulty INTEGER DEFAULT 1
    )
    """
    )
    # progress table stores quiz attempts
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        date TEXT DEFAULT CURRENT_TIMESTAMP,
        accuracy REAL
    )
    """
    )
    # mistakes table stores incorrect QA for review
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        question TEXT,
        correct_answer TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    conn.commit()
    conn.close()


init_db()


def db_insert_flashcard(subject, question, answer, box=1):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO flashcards (subject, question, answer, box, last_reviewed) VALUES (?, ?, ?, ?, ?)",
        (subject, question, answer, box, datetime.datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def db_upsert_flashcards(subject, cards):
    """Replace flashcards for the subject with provided list (cards: [{q,a,box}])."""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM flashcards WHERE subject=?", (subject,))
    for c in cards:
        cur.execute(
            "INSERT INTO flashcards (subject, question, answer, box, last_reviewed) VALUES (?, ?, ?, ?, ?)",
            (subject, c["q"], c["a"], c.get("box", 1), c.get("last_reviewed", datetime.datetime.utcnow().isoformat())),
        )
    conn.commit()
    conn.close()


def db_get_flashcards(subject):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, question, answer, box, last_reviewed FROM flashcards WHERE subject=?", (subject,))
    rows = cur.fetchall()
    conn.close()
    cards = []
    for r in rows:
        cards.append({"id": r[0], "q": r[1], "a": r[2], "box": r[3], "last_reviewed": r[4]})
    return cards


def db_upsert_qas(subject, qas):
    """Store QA pairs (list of dicts {question, options:list, answer}). Replaces existing for subject."""
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM qa_pairs WHERE subject=?", (subject,))
    for qa in qas:
        cur.execute(
            "INSERT INTO qa_pairs (subject, question, options_json, answer, difficulty) VALUES (?, ?, ?, ?, ?)",
            (subject, qa["question"], json.dumps(qa["options"]), qa["answer"], qa.get("difficulty", 1)),
        )
    conn.commit()
    conn.close()


def db_get_qas(subject):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, question, options_json, answer, difficulty FROM qa_pairs WHERE subject=?", (subject,))
    rows = cur.fetchall()
    conn.close()
    qas = []
    for r in rows:
        qas.append({"id": r[0], "question": r[1], "options": json.loads(r[2]), "answer": r[3], "difficulty": r[4]})
    return qas


def db_log_progress(subject, accuracy):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO progress (subject, accuracy) VALUES (?, ?)", (subject, float(accuracy)))
    conn.commit()
    conn.close()


def db_get_progress(subject=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if subject and subject != "All":
        cur.execute("SELECT date, accuracy FROM progress WHERE subject=? ORDER BY date", (subject,))
    else:
        cur.execute("SELECT date, accuracy, subject FROM progress ORDER BY date")
    rows = cur.fetchall()
    conn.close()
    return rows


def db_record_mistake(subject, question, correct_answer):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO mistakes (subject, question, correct_answer) VALUES (?, ?, ?)", (subject, question, correct_answer))
    conn.commit()
    conn.close()


def db_get_mistakes(subject=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if subject:
        cur.execute("SELECT question, correct_answer, timestamp FROM mistakes WHERE subject=? ORDER BY timestamp DESC", (subject,))
    else:
        cur.execute("SELECT question, correct_answer, timestamp FROM mistakes ORDER BY timestamp DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------
# Utilities: PDF/TXT extraction & chunking
# ---------------------------
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text = ""
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for p in pdf.pages:
                    page_text = p.extract_text() or ""
                    text += page_text + "\n"
            if text.strip():
                return text
        except Exception:
            pass
    if HAS_PYMUPDF:
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for p in doc:
                text += p.get_text() or ""
            if text.strip():
                return text
        except Exception:
            pass
    return text


def extract_chunks_from_upload(uploaded_bytes, filename, chunk_chars=12000):
    if not uploaded_bytes:
        return []
    if filename.lower().endswith(".pdf"):
        full_text = extract_text_from_pdf_bytes(uploaded_bytes)
    else:
        try:
            full_text = uploaded_bytes.decode("utf-8", errors="ignore")
        except Exception:
            full_text = ""
    full_text = re.sub(r"\s+", " ", full_text).strip()
    if not full_text:
        return []
    return [full_text[i : i + chunk_chars] for i in range(0, len(full_text), chunk_chars)]


# ---------------------------
# Heuristic key-point extraction (fallback if OpenAI missing)
# ---------------------------
STOPWORDS = set(
    """a an the and or but if of at by for from in on to with without within into over under than then is are was were be being been have has had do does did can could should would may might must this that these those it its as not no""".split()
)


def sentence_score(text):
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text)
    freq = {}
    for w in words:
        lw = w.lower()
        if lw in STOPWORDS:
            continue
        freq[lw] = freq.get(lw, 0) + 1
    sents = re.split(r"(?<=[.!?])\s+", text)
    scored = []
    for s in sents:
        sc = sum(freq.get(w.lower(), 0) for w in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", s))
        if len(s.strip()) > 40:
            scored.append((sc, s.strip()))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [s for _, s in scored]


def extract_key_points_from_chunks(chunks, n_points=12):
    candidates = []
    for ch in chunks:
        for s in sentence_score(ch):
            if s not in candidates:
                candidates.append(s)
            if len(candidates) >= n_points:
                break
        if len(candidates) >= n_points:
            break
    cards = []
    used = set()
    for s in candidates[:n_points]:
        front = (s[:110] + "...") if len(s) > 110 else s
        back = s
        key = back.strip().lower()
        if key in used:
            continue
        used.add(key)
        cards.append(
            {
                "q": front,
                "a": back,
                "box": 1,
                "last_reviewed": (datetime.datetime.utcnow() - datetime.timedelta(days=30)).isoformat(),
            }
        )
    return cards


# ---------------------------
# OpenAI helpers (flashcards + MCQs)
# ---------------------------
def openai_generate_flashcards(chunks, n_items=12):
    """
    Uses OpenAI (Chat API) to extract definitions/formulas/key-concepts only.
    Returns list of cards {q,a}
    """
    if not HAS_OPENAI or not openai.api_key:
        return []

    cards = []
    for ch in chunks:
        prompt = f"""
Extract the most important definitions, formulas and short concept summaries from the text below.
Return each item as a single line with no numbering or additional explanation.
Only include concise formulas or definitions (one-liners). Ignore headings and captions.
Return up to {n_items} items for this chunk.
Text:
{ch}
"""
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful study assistant that extracts formulas and short definitions."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=700,
            )
            text = resp["choices"][0]["message"]["content"].strip()
            # parse lines
            for line in text.splitlines():
                line = line.strip().lstrip("-• ").strip()
                if not line:
                    continue
                # treat short line as flashcard: front is truncated preview, back is full line
                front = (line[:110] + "...") if len(line) > 110 else line
                back = line
                cards.append({"q": front, "a": back, "box": 1, "last_reviewed": datetime.datetime.utcnow().isoformat()})
                if len(cards) >= n_items:
                    return cards
        except Exception as e:
            # don't crash; return what we have
            print("OpenAI flashcard error:", e)
            break
    return cards


def openai_generate_mcqs(chunks, num_questions=10):
    """
    Use OpenAI to generate MCQs in strict format for the quiz.
    Returns list of {question, options, answer}.
    """
    if not HAS_OPENAI or not openai.api_key:
        return []

    qa_pairs = []
    for ch in chunks:
        prompt = f"""
Generate up to {num_questions} multiple-choice questions from the text below. Each question must be concise and test understanding (definitions, formulas, key facts).
Return ONLY in strict format (one block per question):

Q: <question>
A) <opt1>
B) <opt2>
C) <opt3>
D) <opt4>
Answer: <A/B/C/D>

Text:
{ch}
"""
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You produce clean MCQs in the requested format."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=900,
            )
            text = resp["choices"][0]["message"]["content"].strip()
            blocks = text.split("Q: ")
            for block in blocks:
                b = block.strip()
                if not b:
                    continue
                lines = [ln.strip() for ln in b.splitlines() if ln.strip()]
                q = lines[0]
                opts = []
                ans = None
                for ln in lines[1:]:
                    if ln.startswith(("A)", "A)")) or ln.startswith("A)"):
                        opts.append(ln[2:].strip() if len(ln) > 2 else "")
                    elif ln.startswith(("A)", "B)", "C)", "D)")):
                        opts.append(ln[2:].strip())
                    elif ln.startswith(("A)", "B)", "C)", "D)")):
                        opts.append(ln[2:].strip())
                    elif ln.startswith(("A)", "B)", "C)", "D)")):
                        opts.append(ln[2:].strip())
                    elif ln.startswith(("A)", "B)", "C)", "D)")):
                        opts.append(ln[2:].strip())
                    elif ln.startswith("A)") or ln.startswith("B)") or ln.startswith("C)") or ln.startswith("D)"):
                        opts.append(ln[2:].strip())
                    elif ln.startswith("A)") or ln.startswith("B)") or ln.startswith("C)") or ln.startswith("D)"):
                        opts.append(ln[2:].strip())
                    # check for "A) ..." pattern; also check Answer:
                    if ln.lower().startswith("answer"):
                        m = re.search(r"([ABCD])", ln, re.I)
                        if m and len(opts) >= 4:
                            ans = opts[ord(m.group(1).upper()) - ord("A")]
                # fallback: try to find options lines starting with A) B) C) D)
                if q and len(opts) >= 4 and ans:
                    qa_pairs.append({"question": q, "options": opts[:4], "answer": ans})
                if len(qa_pairs) >= num_questions:
                    return qa_pairs[:num_questions]
        except Exception as e:
            print("OpenAI MCQ error:", e)
            break
    return qa_pairs[:num_questions]


# ---------------------------
# Leitner scheduling helpers
# ---------------------------
BOX_INTERVALS = {1: 0, 2: 1, 3: 3}  # box 1: review now (hard), box2: 1 day, box3: 3 days (easy)
# mapping: Box1 = Hard (review most often), Box2 = Medium, Box3 = Easy/mastered

def is_due(card):
    try:
        last = card.get("last_reviewed")
        if not last:
            return True
        last_date = datetime.datetime.fromisoformat(last).date()
        box = int(card.get("box", 1))
        interval = BOX_INTERVALS.get(box, 3)
        return (datetime.datetime.utcnow().date() - last_date).days >= interval
    except Exception:
        return True


def promote_box(card):
    card["box"] = min(3, int(card.get("box", 1)) + 1)
    card["last_reviewed"] = datetime.datetime.utcnow().isoformat()


def demote_box(card):
    card["box"] = 1
    card["last_reviewed"] = datetime.datetime.utcnow().isoformat()


# ---------------------------
# Navigation: determine default selection BEFORE creating widget
# Use redirect_to to request page change (set elsewhere), apply BEFORE widget
# ---------------------------
_page_options = ["Upload Notes", "Flashcards", "Spaced Repetition", "Quiz", "Review Mistakes", "Progress"]
_default = st.session_state.get("nav", "Upload Notes")
# If redirect_to set previously, apply it now (before widget creation)
if st.session_state.get("redirect_to"):
    _default = st.session_state["redirect_to"]
    # clear redirect_to after using it (we'll clear after widget creation)
# Create navigation widget with key "nav" (safe — we set default via index)
try:
    nav_index = _page_options.index(_default) if _default in _page_options else 0
except Exception:
    nav_index = 0

nav = st.sidebar.radio("Go to", _page_options, index=nav_index, key="nav")

# After widget creation: clear redirect_to if it was used
if st.session_state.get("redirect_to"):
    st.session_state.redirect_to = None


# ---------------------------
# UI: Upload Tab
# ---------------------------
if nav == "Upload Notes":
    st.title("📂 Upload Notes (PDF or TXT)")
    st.write("Upload a PDF or TXT. The file is saved in session — then open Flashcards to generate concept flashcards, or Quiz to generate MCQs.")
    st.session_state.subject = st.text_input("Subject name", value=st.session_state.subject)

    uploaded = st.file_uploader("Upload a PDF or TXT file (saved to session)", type=["pdf", "txt"], accept_multiple_files=False)

    if uploaded is not None:
        try:
            st.session_state.uploaded_bytes = uploaded.getvalue()
            st.session_state.uploaded_name = uploaded.name
            st.success(f"Saved {uploaded.name} in session.")
            # set redirect_to so the next rerun will open Flashcards (set before radio on next run)
            st.session_state.redirect_to = "Flashcards"
            # attempt to rerun so redirect happens immediately
            try:
                st.experimental_rerun()
            except Exception:
                # older Streamlit might not have experimental_rerun; instruct user
                st.info("Upload saved — please click 'Flashcards' in the sidebar to continue.")
        except Exception as e:
            st.error("Failed to read uploaded file. Try again.")
            print("Upload error:", e)

    st.markdown("**Uploaded file:**")
    if st.session_state.uploaded_name:
        st.write(f"- {st.session_state.uploaded_name}")
    else:
        st.write("- None")


# ---------------------------
# Flashcards tab
# ---------------------------
elif nav == "Flashcards":
    st.title("🧾 Flashcards — Definitions & Formulas Only")
    st.write("Flashcards are concept summaries (formulas, definitions, short explanations). Click the button to generate them from the last uploaded file (session).")
    if not st.session_state.uploaded_bytes:
        st.info("No uploaded file in session. Upload a PDF/TXT first in Upload Notes tab.")
    else:
        st.info(f"Last uploaded: {st.session_state.uploaded_name} — Subject: {st.session_state.subject}")
        n = st.number_input("Number of flashcards to extract", min_value=4, max_value=80, value=12, step=2)
        if st.button("Generate Flashcards from uploaded file"):
            chunks = extract_chunks_from_upload(st.session_state.uploaded_bytes, st.session_state.uploaded_name)
            cards = []
            # first try OpenAI generator
            if HAS_OPENAI and openai.api_key:
                try:
                    cards = openai_generate_flashcards(chunks, n_items=n)
                except Exception as e:
                    print("OpenAI flashcards failed:", e)
                    cards = []
            # fallback
            if not cards:
                cards = extract_key_points_from_chunks(chunks, n_points=n)
            # store to DB & session
            if cards:
                db_upsert_flashcards(st.session_state.subject, cards)
                st.session_state.flashcards_loaded = True
                st.success(f"Generated {len(cards)} flashcards for subject '{st.session_state.subject}'.")
            else:
                st.error("Could not generate flashcards from this file. Try a clearer or longer document.")

    # display flashcards (informative cards only, NO show-answer button)
    cards = db_get_flashcards(st.session_state.subject)
    if cards:
        st.write("Flashcards (front = short summary; back = full item):")
        for i, c in enumerate(cards, start=1):
            st.markdown(f"<div class='flashcard'><b>Card {i}:</b> {c['q']}<div class='small-muted'><br/>{c['a']}</div></div>", unsafe_allow_html=True)
    else:
        st.info("No flashcards stored for this subject yet.")


# ---------------------------
# Spaced Repetition tab (Leitner)
# ---------------------------
elif nav == "Spaced Repetition":
    st.title("⏳ Spaced Repetition (Leitner boxes)")
    cards = db_get_flashcards(st.session_state.subject)
    if not cards:
        st.info("No flashcards found. Generate flashcards in the Flashcards tab first.")
    else:
        # Compute due cards
        due_cards = [c for c in cards if is_due(c)]
        st.caption(f"Cards due today: {len(due_cards)} (subject: {st.session_state.subject})")

        # Show box distribution
        boxes = {1: 0, 2: 0, 3: 0}
        for c in cards:
            boxes[int(c.get("box", 1))] += 1
        c1, c2, c3 = st.columns(3)
        c1.metric("Box 1 — Hard (review often)", boxes[1])
        c2.metric("Box 2 — Medium", boxes[2])
        c3.metric("Box 3 — Easy/Mastered", boxes[3])

        st.divider()

        if not due_cards:
            st.success("No cards due right now. Great job!")
        else:
            st.write("Review due cards below — choose Easy / Medium / Hard for each card.")
            for idx, card in enumerate(due_cards, start=1):
                st.markdown(f"**Q{idx}:** {card['q']}  (Box {card['box']})")
                # Reveal detail option
                if st.button(f"Show Details #{idx}", key=f"show_{card['id']}"):
                    st.info(card["a"])
                col_easy, col_med, col_hard = st.columns(3)
                if col_easy.button("Easy (promote)", key=f"easy_{card['id']}"):
                    promote_box(card)
                    # update DB
                    conn = sqlite3.connect(DB)
                    cur = conn.cursor()
                    cur.execute("UPDATE flashcards SET box=?, last_reviewed=? WHERE id=?", (card["box"], card["last_reviewed"], card["id"]))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()
                if col_med.button("Medium (keep)", key=f"med_{card['id']}"):
                    # keep same box but update last_reviewed
                    card["last_reviewed"] = datetime.datetime.utcnow().isoformat()
                    conn = sqlite3.connect(DB)
                    cur = conn.cursor()
                    cur.execute("UPDATE flashcards SET last_reviewed=? WHERE id=?", (card["last_reviewed"], card["id"]))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()
                if col_hard.button("Hard → Send to Quiz", key=f"hard_{card['id']}"):
                    # demote to box 1 and add to hard quiz pool
                    demote_box(card)
                    conn = sqlite3.connect(DB)
                    cur = conn.cursor()
                    cur.execute("UPDATE flashcards SET box=?, last_reviewed=? WHERE id=?", (card["box"], card["last_reviewed"], card["id"]))
                    conn.commit()
                    conn.close()
                    # Create a simple MCQ from the card answer: correct = full answer, options are distractors
                    options = [card["a"]]
                    # build distractors from other flashcards
                    other_answers = [o["a"] for o in cards if o["id"] != card["id"] and o["a"].strip()]
                    random.shuffle(other_answers)
                    options.extend(other_answers[:3])
                    while len(options) < 4:
                        options.append("None of the above")
                    random.shuffle(options)
                    st.session_state.quiz_pool_hard.append({"question": card["q"], "options": options[:4], "answer": card["a"], "source_flashcard_id": card["id"]})
                    st.session_state.use_hard_pool = True
                    # set redirect_to for next run to Quiz
                    st.session_state.redirect_to = "Quiz"
                    try:
                        st.experimental_rerun()
                    except Exception:
                        st.success("Added to Hard-pool. Click Quiz in the sidebar to take the questions.")


# ---------------------------
# Quiz tab
# ---------------------------
elif nav == "Quiz":
    st.title("🎯 Quiz (MCQs)")

    # Option to generate MCQs from uploaded file (explicit)
    if st.session_state.uploaded_bytes:
        st.write("You can generate MCQs from the last uploaded document (keeps QA separated from flashcards).")
        n = st.number_input("MCQs to generate", min_value=4, max_value=60, value=10, step=1)
        if st.button("Generate MCQs for Quiz from last upload"):
            chunks = extract_chunks_from_upload(st.session_state.uploaded_bytes, st.session_state.uploaded_name)
            qas = []
            # Try OpenAI QG
            if HAS_OPENAI and openai.api_key:
                try:
                    qas = openai_generate_mcqs(chunks, num_questions=n)
                except Exception as e:
                    print("OpenAI MCQ generation error:", e)
                    qas = []
            # Fallback small cloze generator if OpenAI unavailable
            if not qas:
                # simple cloze-based MCQs (keeps context)
                qas = []
                for ch in chunks:
                    sents = re.split(r"(?<=[.!?])\s+", ch)
                    for s in sents:
                        words = re.findall(r"[A-Za-z][A-Za-z\-]{3,}", s)
                        if not words:
                            continue
                        target = words[0]
                        blanked = re.sub(rf"\b{re.escape(target)}\b", "____", s, flags=re.I)
                        options = [target]
                        other_words = list({w for w in words[1:] if w.lower() != target.lower()})
                        random.shuffle(other_words)
                        options.extend(other_words[:3])
                        while len(options) < 4:
                            options.append("None of the above")
                        random.shuffle(options)
                        qas.append({"question": f"Complete: {blanked}", "options": options[:4], "answer": target})
                        if len(qas) >= n:
                            break
                    if len(qas) >= n:
                        break
            # store in DB and session
            if qas:
                db_upsert_qas(st.session_state.subject, qas)
                st.success(f"Generated {len(qas)} MCQs for quiz. Scroll below to take them.")
            else:
                st.error("Could not generate MCQs from this file.")
    else:
        st.info("Upload a file first in Upload tab to generate MCQs.")

    # Choose source: Hard pool or subject QA
    if st.session_state.use_hard_pool and st.session_state.quiz_pool_hard:
        qna_list = st.session_state.quiz_pool_hard
        pool_name = "Hard Pool (from Spaced Repetition)"
    else:
        qna_list = db_get_qas(st.session_state.subject)
        pool_name = st.session_state.subject

    if not qna_list:
        st.info("No quiz items available. Generate MCQs from Upload tab or mark flashcards Hard in Spaced Repetition.")
    else:
        idx = st.session_state.quiz_index
        total = len(qna_list)
        if idx < total:
            qa = qna_list[idx]
            st.subheader(f"{pool_name} — Question {idx+1}/{total}")
            st.write(qa["question"])
            # Show options (ensure exactly 4)
            opts = qa["options"] if "options" in qa else qa.get("options", [])
            if isinstance(opts, str):
                # if options stored as JSON string in DB
                try:
                    opts = json.loads(opts)
                except Exception:
                    opts = []
            if len(opts) < 4:
                # top up with generic distractors
                extras = ["None of the above", "Cannot be determined", "Not applicable", "Context dependent"]
                for e in extras:
                    if len(opts) >= 4:
                        break
                    if e not in opts:
                        opts.append(e)
            # display as radio
            user_choice = st.radio("Choose an answer:", opts, key=f"quiz_{idx}")
            if st.button("Submit Answer"):
                # check correct
                correct = qa["answer"]
                if user_choice == correct:
                    st.success("✅ Correct!")
                    st.session_state.progress["correct"] += 1
                    # If item came from flashcard hard pool, promote that flashcard maybe
                    if st.session_state.use_hard_pool and "source_flashcard_id" in qa:
                        # promote that flashcard's box (it was added as Hard earlier)
                        conn = sqlite3.connect(DB)
                        cur = conn.cursor()
                        # promote box for the flashcard
                        cur.execute("SELECT box FROM flashcards WHERE id=?", (qa["source_flashcard_id"],))
                        r = cur.fetchone()
                        if r:
                            new_box = min(3, int(r[0]) + 1)
                            cur.execute("UPDATE flashcards SET box=?, last_reviewed=? WHERE id=?", (new_box, datetime.datetime.utcnow().isoformat(), qa["source_flashcard_id"]))
                            conn.commit()
                        conn.close()
                else:
                    st.error(f"❌ Wrong. Correct: {correct}")
                    st.session_state.progress["wrong"] += 1
                    # record mistake in DB
                    db_record_mistake(st.session_state.subject, qa["question"], correct)
                    # If hard-pool flashcard, demote the original flashcard to Box1
                    if st.session_state.use_hard_pool and "source_flashcard_id" in qa:
                        conn = sqlite3.connect(DB)
                        cur = conn.cursor()
                        cur.execute("UPDATE flashcards SET box=1, last_reviewed=? WHERE id=?", (datetime.datetime.utcnow().isoformat(), qa["source_flashcard_id"]))
                        conn.commit()
                        conn.close()

                st.session_state.quiz_index += 1
                # if attempt used hard pool and consumed all, reset state
                try:
                    st.experimental_rerun()
                except Exception:
                    pass
        else:
            # quiz complete
            c = st.session_state.progress["correct"]
            w = st.session_state.progress["wrong"]
            total_ans = c + w if (c + w) > 0 else len(qna_list)
            acc = round((c / total_ans) * 100, 2) if total_ans else 0.0
            st.success(f"🎉 Quiz complete — Score: {c}/{total_ans} ({acc}%)")
            # persist progress (only for regular pool, not hard-pool)
            if not st.session_state.use_hard_pool:
                db_log_progress(st.session_state.subject, acc)
            # reset hard pool state
            if st.session_state.use_hard_pool:
                st.session_state.quiz_pool_hard = []
                st.session_state.use_hard_pool = False
            # show option to restart and show history snippet
            if st.button("Restart Quiz"):
                st.session_state.quiz_index = 0
                st.session_state.progress = {"correct": 0, "wrong": 0}
                st.experimental_rerun()

            # show recent progress for this subject
            st.subheader("Recent Attempts (subject)")
            rows = db_get_progress(st.session_state.subject)
            if rows:
                last5 = rows[-10:]
                for r in last5:
                    st.write(f"- {r[0]} — {r[1]:.2f}%")
            else:
                st.info("No saved attempts for this subject yet.")


# ---------------------------
# Review Mistakes tab
# ---------------------------
elif nav == "Review Mistakes":
    st.title("🩺 Review Mistakes")
    rows = db_get_mistakes(st.session_state.subject)
    if not rows:
        st.info("No mistakes recorded yet.")
    else:
        for r in rows:
            st.markdown(f"- **Q:** {r[0]}  \n  **Answer:** {r[1]}  \n  _Recorded:_ {r[2]}")


# ---------------------------
# Progress tab
# ---------------------------
elif nav == "Progress":
    st.title("📊 Progress & History")
    subj_list = ["All"] + [st.session_state.subject]
    subject_filter = st.selectbox("Filter subject", subj_list, index=0)
    rows = db_get_progress(subject_filter if subject_filter != "All" else None)
    if rows:
        # simple table + small plot (accuracy over time)
        st.write("Past attempts (newest last):")
        for r in rows:
            date = r[0]
            acc = r[1]
            subj = r[2] if len(r) > 2 else st.session_state.subject
            st.write(f"- {subj} — {acc:.2f}% ({date})")
        # plot accuracy over time if many
        try:
            import matplotlib.pyplot as plt
            dates = [datetime.datetime.fromisoformat(r[0]) for r in rows]
            accs = [r[1] for r in rows]
            fig, ax = plt.subplots()
            ax.plot(dates, accs, marker="o")
            ax.set_title(f"Accuracy over time ({subject_filter})")
            ax.set_ylabel("Accuracy %")
            ax.set_xlabel("Date")
            st.pyplot(fig)
        except Exception:
            pass
    else:
        st.info("No progress recorded yet. Take quizzes to build history.")


# ---------------------------
# End of app
# ---------------------------
