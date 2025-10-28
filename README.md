# XTeam
Multi-Agent-Platform

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

## Architektur-Diagramm
```

```

