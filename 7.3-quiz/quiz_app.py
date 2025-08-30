# quiz_app.py
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Study Quiz", layout="centered")

st.title("📝 Self-Testing Quiz")
st.write("Quiz yourself on the Q&A pairs generated in Step 7.2")

# --- Load Q&A CSV ---
@st.cache_data
def load_qna(file_path="qna_pairs.csv"):
    df = pd.read_csv(file_path)
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    return df

try:
    df = load_qna()
except FileNotFoundError:
    st.error("⚠️ Could not find 'qna_pairs.csv'. Please generate Q&As in Step 7.2 first.")
    st.stop()

# --- Prepare questions ---
questions = df.to_dict(orient="records")
random.shuffle(questions)

# --- Session state for quiz progress ---
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
    st.session_state.score = 0

# --- Show current question ---
if st.session_state.q_index < len(questions):
    q = questions[st.session_state.q_index]
    st.subheader(f"Q{st.session_state.q_index+1}: {q['question']}")

    # Create wrong options from other answers
    other_answers = [x["answer"] for x in questions if x != q]
    if len(other_answers) >= 3:
        choices = random.sample(other_answers, 3)
    else:
        choices = other_answers

    # Add the correct answer
    choices.append(q["answer"])
    random.shuffle(choices)

    selected = st.radio("Choose an answer:", choices, key=f"q_{st.session_state.q_index}")

    if st.button("Submit", key=f"submit_{st.session_state.q_index}"):
        if selected == q["answer"]:
            st.success("✅ Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Wrong. Correct answer: {q['answer']}")

        st.session_state.q_index += 1
        st.rerun()   # 👈 updated API (instead of st.experimental_rerun)
else:
    st.success(f"🎉 Quiz complete! Your score: {st.session_state.score}/{len(questions)}")
    if st.button("Restart"):
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.rerun()
