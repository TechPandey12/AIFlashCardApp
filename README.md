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
<img width="1916" height="878" alt="Screenshot 2025-08-30 211849" src="https://github.com/user-attachments/assets/9f7a75ef-e86b-483a-a56d-dea166fb6467" />

<img width="1913" height="878" alt="Screenshot 2025-08-30 221002" src="https://github.com/user-attachments/assets/c12c971c-8126-42e1-9839-7fcff3fca71f" />


<img width="1914" height="876" alt="Screenshot 2025-08-30 221019" src="https://github.com/user-attachments/assets/824aa129-fc02-4175-a2d8-0f3e871422a6" />

<img width="1905" height="873" alt="Screenshot 2025-08-30 221151" src="https://github.com/user-attachments/assets/afc09ec2-777a-4311-96aa-4aa627a99078" />

<img width="1903" height="868" alt="Screenshot 2025-08-30 221221" src="https://github.com/user-attachments/assets/72f9a66d-104d-4445-8daa-0fc6afa581a4" />

<img width="1878" height="889" alt="Screenshot 2025-08-30 221314" src="https://github.com/user-attachments/assets/d604339d-1f6b-491a-8f75-70aaa3d30286" />





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
