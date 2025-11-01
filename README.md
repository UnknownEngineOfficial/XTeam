# XTeam
Multi-Agent-Platform

## Beschreibung
XTeam ist eine Multi-Agent-Plattform zur KI-gestützten Softwareentwicklung. Ziel ist es, komplexe Entwicklungsprojekte automatisiert und kollaborativ zu bearbeiten, von der Anforderung bis zum fertigen Code.

Ziel ein erweitertes MGX MetaGPT X.

## Projektstruktur
```
XTEAM/
├── frontend/                          # React + Vite Frontend
│   ├── public/
│   │   └── assets/
│   ├── src/
│   │   ├── components/                # Wiederverwendbare UI-Komponenten
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   └── InputBar.tsx
│   │   │   ├── editor/
│   │   │   │   ├── CodeEditor.tsx     # Monaco Editor Integration
│   │   │   │   ├── FileTree.tsx
│   │   │   │   └── Terminal.tsx
│   │   │   ├── preview/
│   │   │   │   ├── LivePreview.tsx    # iframe Sandbox
│   │   │   │   └── PreviewControls.tsx
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       ├── Modal.tsx
│   │   │       └── Loader.tsx
│   │   ├── pages/                     # Route-Level Components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ProjectView.tsx
│   │   │   ├── Auth.tsx
│   │   │   └── Settings.tsx
│   │   ├── hooks/                     # Custom React Hooks
│   │   │   ├── useWebSocket.ts        # WebSocket Management
│   │   │   ├── useProject.ts
│   │   │   └── useAuth.ts
│   │   ├── services/                  # API & Integration Layer
│   │   │   ├── websocket.ts           # WebSocket Client
│   │   │   ├── api.ts                 # REST API Calls
│   │   │   └── storage.ts             # LocalStorage/SessionStorage
│   │   ├── store/                     # State Management (Zustand/Redux)
│   │   │   ├── projectStore.ts
│   │   │   ├── authStore.ts
│   │   │   └── uiStore.ts
│   │   ├── types/                     # TypeScript Type Definitions
│   │   │   ├── project.ts
│   │   │   ├── agent.ts
│   │   │   └── websocket.ts
│   │   ├── utils/                     # Helper Functions
│   │   │   ├── formatters.ts
│   │   │   └── validators.ts
│   │   ├── styles/                    # Global Styles
│   │   │   └── globals.css
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
│
├── backend/                           # FastAPI + MetaGPT Backend
│   ├── app/
│   │   ├── core/                      # Core Configuration
│   │   │   ├── config.py              # Environment Variables
│   │   │   ├── security.py            # JWT Auth
│   │   │   └── database.py            # DB Connection
│   │   ├── api/                       # API Endpoints
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── agents.py
│   │   │   │   └── websocket.py       # WebSocket Endpoint
│   │   │   └── deps.py                # Dependencies
│   │   ├── metagpt_integration/       # MetaGPT Wrapper
│   │   │   ├── agent_manager.py       # Agent Orchestration
│   │   │   ├── task_queue.py          # Async Task Processing
│   │   │   ├── file_handler.py        # Workspace Management
│   │   │   └── streaming.py           # Real-time Updates
│   │   ├── models/                    # Database Models
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   └── execution.py
│   │   ├── schemas/                   # Pydantic Schemas
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   └── websocket.py
│   │   ├── services/                  # Business Logic
│   │   │   ├── project_service.py
│   │   │   ├── agent_service.py
│   │   │   └── deployment_service.py
│   │   ├── websocket/                 # WebSocket Management
│   │   │   ├── connection_manager.py  # Connection Pool
│   │   │   ├── message_handler.py
│   │   │   └── broadcast.py
│   │   └── main.py                    # FastAPI Application
│   ├── metagpt/                       # MetaGPT Framework (Submodule)
│   │   └── [MetaGPT Repository]
│   ├── workspaces/                    # Generated Projects
│   │   └── [project_id]/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
│
├── shared/                            # Shared Types/Constants
│   └── types.ts
│
├── docker/
│   ├── docker-compose.yml
│   ├── frontend.Dockerfile
│   └── backend.Dockerfile
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
└── README.md
```

## Technologie-Stack
### Frontend
- React 18 + TypeScript
- Vite (Build Tool)
- Tailwind CSS
- Monaco Editor (Code Viewer)
- Websocket Client
- Zustand (State Management)
### Backend
- FastAPI (Python 3.9+)
- WebSocket Support
- PostgreSQL (User/Project Data)
- Redis (Task Queue)
- JWT Authentication
### MetaGPT Integration 
- MetaGPT Framework (Submodule)
- Custom Agent Manager
- Asynchrone Task Execution

## Architektur-Diagramm
```
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER (Frontend)                           │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  Chat    │ │  Monaco  │ │  File   │ │  Live   │ │Terminal │  │
│  │  UI      │ │  Editor  │ │  Tree   │ │ Preview │ │ Output  │  │
│  └──────────┘ └──────────┘ └─────────┘ └─────────┘ └─────────┘  │
│           React + Vite + TypeScript                             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/WSS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NGINX Reverse Proxy                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐           │
│  │  /ws        │  │  /api/v1/*   │  │  /            │           │
│  │  WebSocket  │  │  REST API    │  │  Static Files │           │
│  └─────────────┘  └──────────────┘  └───────────────┘           │
│              ◄── SSL, CORS, Rate Limiting, Load Balancing       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  WebSocket      │  │  REST API    │  │  JWT Auth    │        │
│  │  Manager        │  │  Endpoints   │  │  Middleware  │        │
│  └─────────────────┘  └──────────────┘  └──────────────┘        │
│              Python 3.9+ with uvicorn                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BUSINESS SERVICES LAYER                       │
│  ┌──────────────┐ ┌─────────────┐ ┌──────────────┐              │
│  │  Project     │ │  Agent      │ │  Deployment  │              │
│  │  Service     │ │  Service    │ │  Service     │              │
│  └──────────────┘ └─────────────┘ └──────────────┘              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              METAGPT INTEGRATION LAYER                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Agent      │  │  Task Queue  │  │  Streaming   │            │
│  │  Manager    │  │  (Redis)     │  │  Handler     │            │
│  └─────────────┘  └──────────────┘  └──────────────┘            │
│  ┌──────────────────────────────────────────────────┐           │
│  │  Workspace Manager (/workspaces/{project_id}/)   │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   METAGPT FRAMEWORK                             │
│                   Multi-Agent System                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Product  │ │Architect │ │ Engineer │ │    QA    │            │
│  │ Manager  │ │          │ │          │ │ Engineer │            │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
│  ┌──────────────────────────────────────────────────┐           │
│  │         Project Manager (Coordinator)            │           │
│  └──────────────────────────────────────────────────┘           │
│              ◄── SOP-based collaboration                        │
└────────┬────────────────────────┬────────────────────┬──────────┘
         │                        │                    │
         ▼                        ▼                    ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │  File System    │
│                 │    │                 │    │                 │
│  - Users        │    │  - Task Queue   │    │  - Workspaces   │
│  - Projects     │    │  - Cache        │    │  - Generated    │
│  - Executions   │    │  - Sessions     │    │    Code         │
│  - History      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                    │
         └────────────────────────┴────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                           │
│  ┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │   LLM APIs       │  │  Supabase    │  │   Deployment    │    │
│  │                  │  │              │  │                 │    │
│  │  - OpenAI        │  │  - Auth      │  │  - Vercel       │    │
│  │  - Azure OpenAI  │  │  - Database  │  │  - Netlify      │    │
│  │  - Groq          │  │  - Storage   │  │  - Docker       │    │
│  │  - Ollama        │  │              │  │                 │    │
│  └──────────────────┘  └──────────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Datenfluss-Beschreibung

### User-Request Flow (↓)
```
Browser → NGINX → FastAPI → Services → Integration → MetaGPT Agents → LLM APIs
```

### Response Flow (↑)
```
Generated Code → Workspace → Streaming Handler → WebSocket → Browser (Real-time)
```

### Persistierung (↔)
```
FastAPI ↔ PostgreSQL (Metadata)
FastAPI ↔ Redis (Queue/Cache)
Integration ↔ File System (Generated Code)
```


## 🚀 Quick Start mit Docker

### Voraussetzungen
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### Installation

1. **Repository klonen**
```bash
git clone https://github.com/UnknownEngineOfficial/XTeam.git
cd XTeam
```

2. **Umgebungsvariablen konfigurieren**
```bash
cp .env.example .env
# Bearbeite .env und füge deine API-Keys hinzu
nano .env
```

Wichtigste Variablen:
- `OPENAI_API_KEY` - OpenAI API Key für LLM
- `SECRET_KEY` - JWT Secret (generiere einen sicheren Schlüssel)
- `POSTGRES_PASSWORD` - Datenbank-Passwort

3. **Services mit Docker Compose starten**
```bash
cd docker
docker-compose up -d
```

Dies startet:
- **Backend** (FastAPI) auf `http://localhost:8000`
- **Frontend** (React) auf `http://localhost:3000`
- **PostgreSQL** Datenbank auf Port `5432`
- **Redis** Cache auf Port `6379`
- **Celery Worker** für asynchrone Tasks

4. **Datenbank-Migrationen ausführen**
```bash
docker-compose exec backend alembic upgrade head
```

5. **Anwendung öffnen**
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Development Setup (ohne Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Konfiguration

### Environment Variables

Vollständige Liste in `.env.example`. Wichtigste Konfigurationen:

#### Application
```env
APP_NAME=XTeam
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

#### Database
```env
DATABASE_URL=postgresql+asyncpg://xteam:password@db:5432/xteam
```

#### Redis & Celery
```env
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/2
```

#### LLM APIs
```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Azure OpenAI (optional)
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...

# Groq (optional)
GROQ_API_KEY=...

# Ollama (lokales LLM)
OLLAMA_BASE_URL=http://localhost:11434
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests
```bash
cd frontend
npm run test
```

### CI/CD
Das Projekt verwendet GitHub Actions für automatisierte Tests:
- **CI Pipeline**: Lint, Test, Build bei jedem Push
- **Deploy Pipeline**: Docker Build & Push bei Tag/Main

## 📦 Deployment

### Docker Production Deployment

1. **Images bauen**
```bash
# Backend
docker build -f docker/backend.Dockerfile -t xteam-backend:latest .

# Frontend
docker build -f docker/frontend.Dockerfile -t xteam-frontend:latest .
```

2. **Mit Docker Compose deployen**
```bash
cd docker
docker-compose -f docker-compose.yml up -d
```

3. **Gesundheitsprüfungen**
```bash
# Backend Health
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

### Kubernetes Deployment

Für Kubernetes-Deployments können die Docker-Images verwendet werden:

```yaml
# Beispiel Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xteam-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: xteam-backend
  template:
    metadata:
      labels:
        app: xteam-backend
    spec:
      containers:
      - name: backend
        image: ghcr.io/unknownenginofficial/xteam/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: xteam-secrets
              key: database-url
```

### Cloud Platforms

#### Vercel (Frontend)
```bash
cd frontend
npm run build
vercel --prod
```

#### Railway/Render (Fullstack)
- Verbinde dein GitHub Repository
- Wähle `docker-compose.yml` als Konfiguration
- Füge Environment Variables hinzu
- Deploy!

## 🔍 Monitoring & Logs

### Logs anzeigen
```bash
# Alle Services
docker-compose logs -f

# Nur Backend
docker-compose logs -f backend

# Nur Worker
docker-compose logs -f worker
```

### Metriken (Optional)
Das System kann mit Prometheus/Grafana für Monitoring erweitert werden.

## 🛠️ Development

### Code Style
Das Projekt verwendet:
- **Backend**: Black, Ruff, MyPy, isort
- **Frontend**: ESLint, Prettier

```bash
# Backend Linting
cd backend
ruff check app/ --fix
black app/
mypy app/

# Frontend Linting
cd frontend
npm run lint
```

### Datenbank-Migrationen

Neue Migration erstellen:
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Celery Worker starten (Development)
```bash
cd backend
celery -A app.tasks worker --loglevel=info
```

### Celery Beat starten (Scheduled Tasks)
```bash
cd backend
celery -A app.tasks beat --loglevel=info
```

## ��️ Architektur-Entscheidungen

### Warum Docker?
- **Konsistenz**: Gleiche Umgebung überall (Dev, Staging, Prod)
- **Isolation**: Services laufen unabhängig
- **Skalierbarkeit**: Einfaches horizontales Scaling
- **Portabilität**: Läuft auf jedem System mit Docker

### Warum Alembic?
- **Schema-Versionierung**: Alle DB-Änderungen nachverfolgbar
- **Migrations-Kontrolle**: Schrittweise Updates/Rollbacks
- **Team-Kollaboration**: Konfliktfreie Schema-Entwicklung

### Warum Celery?
- **Async Processing**: Lange Tasks blockieren nicht die API
- **Retry-Mechanismus**: Automatische Wiederholungen bei Fehlern
- **Scheduling**: Periodische Tasks (Cleanup, Statistics)

## 🤝 Contributing

1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Pushe zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

### Code-Standards
- Tests für neue Features schreiben
- Code-Style-Guidelines befolgen (Black, ESLint)
- Commit-Messages aussagekräftig formulieren
- PR-Beschreibung mit Context und Screenshots

## �� Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details

## 🆘 Support

- GitHub Issues: [Issues](https://github.com/UnknownEngineOfficial/XTeam/issues)
- Discussions: [Discussions](https://github.com/UnknownEngineOfficial/XTeam/discussions)

