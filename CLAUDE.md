# CLAUDE.md — ChatBot Project

## Project Overview

Full-stack AI chatbot for lead generation. Django REST backend + React/Vite/TypeScript frontend. Conversations progress through stages (greeting → discovery → qualification → contact → closing) to qualify and extract leads.

## Tech Stack

| Layer      | Tech                              |
| ---------- | --------------------------------- |
| Backend    | Django 6.0 + DRF 3.16            |
| Database   | PostgreSQL                        |
| Frontend   | React 19 + Vite 7 + TypeScript 5 |
| Styling    | Tailwind CSS 3 (class-based dark) |
| HTTP       | Axios 1.13                        |
| Routing    | React Router DOM 7                |
| AI Engines | Ollama, OpenAI (gpt-4), LM Studio|

## Project Structure

```
ChatBot/
├── chatbot_backend/           # Django project
│   ├── chatbot_backend/       # Settings, root URLs
│   ├── chat/                  # Main app: views, models, services
│   │   ├── services/          # lead_extraction, conversation_orchestrator, ai_service
│   │   ├── models.py          # Lead, Conversation, Message
│   │   ├── views.py           # POST /api/chat/ endpoint
│   │   └── utils.py           # LLM dispatch, prompt loading, caching
│   ├── utils/Prompts/         # Prompt templates (Lead/, Extract/, Chat/)
│   ├── manage.py
│   └── .env                   # Local env vars (not committed)
├── chatbot-frontend/          # React app
│   ├── src/
│   │   ├── components/        # chat/, sidebar/, common/
│   │   ├── hooks/             # useChat, useChatSession, useTheme
│   │   ├── services/          # apiClient.ts, chatApi.ts
│   │   ├── types/             # chat.ts
│   │   ├── config/            # env.ts
│   │   ├── layouts/           # AppLayout.tsx
│   │   ├── pages/             # HomePage.tsx
│   │   └── App.tsx, main.tsx, index.css
│   ├── .env.example
│   ├── vite.config.ts         # @ alias → src/
│   └── tailwind.config.ts
└── requirements.txt           # Python dependencies
```

## Key API

**POST `/api/chat/?engine=ollama|openai|lmstudio`**

Request: `{ "session_id": string, "data": string }`

Response: `{ "isSuccess": bool, "data": { "engine", "stage", "duration", "response", "lead": { "qualified", "intent_level", "email", "phone" } }, "error": null }`

## Backend Conventions

- **Service layer pattern**: business logic in `chat/services/`, not in views
- **Models**: Lead (name, email, phone, company, problem, intent_level, qualified, source), Conversation (session_id, stage, channel), Message (role, content)
- **Conversation stages**: greeting → discovery → qualification → contact → closing (keyword-based transitions)
- **Lead qualification**: high intent + (email OR phone) = qualified
- **LLM dispatch**: `generate_llm_response()` in `chat/utils.py` routes to engine-specific functions
- **Prompt loading**: templates in `utils/Prompts/{type}/{file}.txt`
- **Caching**: LLM responses cached 1 hour via SHA256 key
- **Logging**: structured logging with `logger.info/error/warning`
- **Python naming**: snake_case files and functions

## Frontend Conventions

- **Custom hooks** for all state management (no Redux/Zustand)
- **Component structure**: feature-based folders (chat/, sidebar/, common/)
- **File naming**: PascalCase for components, camelCase for hooks/services/utils
- **Path alias**: `@/` → `src/`
- **API client**: Axios instance in `services/apiClient.ts` (15s timeout, response interceptor returns `.data`)
- **Theme**: class-based dark mode with localStorage persistence, system preference fallback
- **Session**: session_id persisted in localStorage
- **TypeScript**: strict mode enabled, explicit interfaces in `types/`
- **Styling**: Tailwind utility classes, responsive at `md` breakpoint

## Development

```bash
# Backend
cd chatbot_backend
python manage.py runserver          # Port 8000

# Frontend
cd chatbot-frontend
npm run dev                         # Vite dev server (port 5173)
npm run build                       # tsc -b && vite build
npm run lint                        # ESLint
```

## Environment Variables

**Backend** (`chatbot_backend/.env`):
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- `OLLAMA_URL`, `LLM_MODEL_NAME`, `LLM_MODEL_OPEN_AI`, `OPENAI_API_KEY`

**Frontend** (`chatbot-frontend/.env`):
- `VITE_API_BASE_URL=http://localhost:8000`

## Git Workflow

- **Main branch**: `main`
- **Feature branches**: `feat/<description>`
- **Refactor branches**: `ref/<description>`
- **Remote**: GitHub (`Pratham8487/ChatBot`)
- CORS configured for `localhost:5174`

## Important Notes

- No CI/CD pipeline configured yet
- No Docker setup yet
- Django DEBUG=True and insecure SECRET_KEY — must change for production
- Admin interface has no custom registrations
- LangGraph was removed in favor of simpler keyword-based orchestration
