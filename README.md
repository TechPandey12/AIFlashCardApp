# 📚 AI Flashcards Generator

A Streamlit web app that converts study material (PDF, text, etc.) into interactive flashcards using OpenAI's GPT models.  
This helps students revise faster with automatically generated Q&A style cards.

---

## 🚀 Features
- Upload study material (PDF/TXT)
- Generate flashcards instantly using GPT
- Interactive flashcards with question/answer mode
- Control number of cards generated
- Save and revisit cards by subject
- Clean and minimal Streamlit UI

---

## 🛠️ Tech Stack
- **Python 3.10+**
- **Streamlit** (Frontend UI)
- **OpenAI GPT-5 API** (Flashcard generation)
- **SQLite** (Flashcard storage)
- **PyPDF2 / pdfplumber** (PDF text extraction)

---

## ⚙️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
Create and activate a virtual environment:

bash
Copy code
python -m venv .venv
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Mac/Linux
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Set up your OpenAI API key:

bash
Copy code
setx OPENAI_API_KEY "your_api_key_here"   # Windows
export OPENAI_API_KEY="your_api_key_here" # Mac/Linux
▶️ Usage
Run the Streamlit app:

bash
Copy code
streamlit run study_app.py
Then open the provided Local URL (e.g., http://localhost:8501) in your browser.

📸 Demo
<img width="1916" height="878" alt="image" src="https://github.com/user-attachments/assets/cfc0be76-093d-4b12-8672-9116a8a0b804" /> 
<img width="1908" height="887" alt="image" src="https://github.com/user-attachments/assets/dc192f76-42b3-4be9-9989-888f3987dd6a" />

<img width="1914" height="876" alt="image" src="https://github.com/user-attachments/assets/40574598-75ae-473f-8237-5f796c012188" /> 
<img width="1905" height="873" alt="image" src="https://github.com/user-attachments/assets/de3e2a0f-dbad-43cb-ae06-2f670e250265" /> 
<img width="1903" height="868" alt="image" src="https://github.com/user-attachments/assets/9f62c0e2-6e15-46f4-a535-1c923c961a00" /> 
<img width="1878" height="889" alt="image" src="https://github.com/user-attachments/assets/43523ef3-2f9f-4bb1-8429-090e1356ad45" />




https://youtu.be/Y3eDaaCd9kc?si=oll00kxk6E4dwe21 :YouTube demo link

📂 Project Structure

bash
Copy code
study_app/
│── study_app.py       # Main Streamlit app
│── requirements.txt   # Python dependencies
│── db.sqlite          # SQLite database (created at runtime)
│── README.md          # Project documentation

🙌 Contributors
 –Pranshu Pandey-Developer & Maintainer


📜 License

This project is licensed under the MIT License - see the LICENSE file for details
