# XTeam Quick Start Guide

This guide will help you get XTeam up and running quickly using Docker.

## Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher
- At least 4GB of available RAM
- An OpenAI API key (or other LLM provider)

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/UnknownEngineOfficial/XTeam.git
cd XTeam
```

### 2. Configure Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and set at least these required variables:

```env
# Required: Set a secure secret key
SECRET_KEY=your-super-secret-key-here-change-this

# Required: Set your OpenAI API key
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Database password (default is fine for local dev)
POSTGRES_PASSWORD=xteam_password
```

### 3. Start the Services

```bash
cd docker
docker compose up -d
```

This will:
- Download and build all necessary Docker images
- Start PostgreSQL database
- Start Redis cache
- Start the FastAPI backend
- Start the React frontend
- Start Celery worker for async tasks

### 4. Wait for Services to be Ready

Check service health:

```bash
docker compose ps
```

All services should show "healthy" status after ~1 minute.

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## First Time Setup

### Create an Admin User

Connect to the backend container and create a superuser:

```bash
docker compose exec backend python -c "
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            email='admin@xteam.ai',
            username='admin',
            full_name='Admin User',
            hashed_password=get_password_hash('admin123'),
            is_superuser=True,
            is_active=True
        )
        db.add(admin)
        await db.commit()
        print('Admin user created: admin@xteam.ai / admin123')

asyncio.run(create_admin())
"
```

### Verify Database Migrations

```bash
docker compose exec backend alembic current
```

## Common Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f worker
```

### Restart a Service

```bash
docker compose restart backend
```

### Stop All Services

```bash
docker compose down
```

### Stop and Remove All Data

```bash
docker compose down -v
```

### Rebuild After Code Changes

```bash
docker compose up -d --build
```

## Development Workflow

For active development, you may want to run services locally instead of in Docker:

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

You can still use Docker for database and Redis:

```bash
docker compose up -d db redis
```

## Troubleshooting

### Services Won't Start

1. Check if ports are already in use:
   ```bash
   lsof -i :3000  # Frontend
   lsof -i :8000  # Backend
   lsof -i :5432  # PostgreSQL
   lsof -i :6379  # Redis
   ```

2. Check Docker logs:
   ```bash
   docker compose logs
   ```

### Database Connection Errors

1. Ensure PostgreSQL is healthy:
   ```bash
   docker compose ps db
   ```

2. Check database logs:
   ```bash
   docker compose logs db
   ```

3. Try restarting the database:
   ```bash
   docker compose restart db
   ```

### Frontend Can't Connect to Backend

1. Check CORS settings in `.env`:
   ```env
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

2. Verify backend is accessible:
   ```bash
   curl http://localhost:8000/health
   ```

### OpenAI API Errors

1. Verify your API key is set correctly in `.env`
2. Check your OpenAI account has credits
3. Try a different model (e.g., gpt-3.5-turbo instead of gpt-4)

## Next Steps

- Read the [full documentation](README.md)
- Explore the [API documentation](http://localhost:8000/docs)
- Check out the [example projects](docs/examples/)
- Join our [community discussions](https://github.com/UnknownEngineOfficial/XTeam/discussions)

## Support

If you encounter issues:
1. Check the [troubleshooting guide](docs/troubleshooting.md)
2. Search [existing issues](https://github.com/UnknownEngineOfficial/XTeam/issues)
3. Create a [new issue](https://github.com/UnknownEngineOfficial/XTeam/issues/new) with:
   - Your OS and Docker version
   - Steps to reproduce
   - Relevant logs
