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

## ⚙️ Backend Setup (Django)

### 1️⃣ Clone the repository
- (Using https)

```bash
git clone https://github.com/Pratham10036/ChatBot.git
cd ChatBot
```
- (Using SSH)

```bash
git clone git@github.com:Pratham10036/ChatBot.git
cd ChatBot
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
```

### 3️⃣ Activate the virtual environment
- Windows

```bash
venv\Scripts\activate
```
- Linux / macOS

```bash
source venv/bin/activate
```


### 4️⃣ Install backend dependencies

```bash
pip install -r requirements.txt
```

### 5️⃣ Run the Django development server

```bash
python manage.py runserver
```

#### Backend will be available at: http://localhost:8000

# ⚛️ Frontend Setup (React + Vite + TypeScript)

### 1️⃣ Navigate to frontend directory

```bash
cd chatbot-frontend
```

### 2️⃣ Install frontend dependencies

```bash
npm install
```

### 3️⃣ Start the Vite development server
```bash
npm run dev
```

#### Frontend will be available at: http://localhost:5173

# 🤖 AI Setup (Ollama – Free Local LLM)

### 1️⃣ Install Ollama
#### Download from: https://ollama.com

### 2️⃣ Pull an AI model

```bash
ollama pull llama3
```

### 3️⃣ Run the model
```bash
ollama run llama3
```
#### Ollama runs locally and exposes an API at: http://localhost:11434
The Django backend communicates with Ollama through this endpoint.

# 🔐 Environment Variables

#### Create a .env file if required (do NOT commit this file):

```bash
DEBUG=True
```
.env files are excluded using .gitignore for security reasons.

## 🚀 How to Run the Project
- Start Ollama
- Activate Python virtual environment

- Run Django backend server

- Run React frontend server

- Open the frontend URL in browser

- Start chatting with the AI assistant


## 🧠 Features

- REST-based chatbot API

- Secure backend architecture

- Local AI model (no API cost)

- Modern frontend with React + TypeScript

- Easy to deploy and scale

- Resume-ready real-world project