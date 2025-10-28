# XTeam
Multi-Agent-Platform

## Beschreibung
XTeam ist eine Multi-Agent-Plattform zur KI-gestützten Softwareentwicklung. Ziel ist es, komplexe Entwicklungsprojekte automatisiert und kollaborativ zu bearbeiten, von der Anforderung bis zum fertigen Code.

## Projektstruktur
```
metagpt-platform/
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

