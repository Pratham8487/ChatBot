# AI Chatbot Assistant (Django + React)

A full-stack AI chatbot application built with **Django (REST API)** and **React (Vite + TypeScript)**.  
The backend handles AI requests securely, while the frontend provides a modern chat UI suitable for website integration.

---

## 📌 Tech Stack

### Backend
- Python
- Django
- Django REST Framework
- Virtual Environment (venv)

### Frontend
- React
- Vite
- TypeScript
- npm

### AI Integration
- Ollama (Local LLM – free)
- Easily extendable to OpenAI / other providers

---

## 📂 Project Structure

ChatBot/
│
├── chatbot_backend/ # Django backend
│ ├── manage.py
│ └── chat/
│
├── chatbot-frontend/ # React frontend (Vite + TS)
│ ├── src/
│ ├── package.json
│
├── venv/ # Python virtual environment (ignored)
├── requirements.txt
├── .gitignore
└── README.md


---

## ⚙️ Backend Setup (Django)

### 1️⃣ Clone the repository
```bash
git clone <your-repo-url>
cd ChatBot


Install backend dependencies
pip install -r requirements.txt
