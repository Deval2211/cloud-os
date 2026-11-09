# Backend Architecture

**Document**: Backend System Design
**Version**: 1.0
**Status**: Design Phase

## Overview

The backend is a **distributed, event-driven FastAPI application** that orchestrates workspaces, manages GPU resources, handles provider integration, and coordinates complex workflows.

**Core Principles:**
- **Stateless**: All services are horizontally scalable
- **Event-driven**: Services communicate via events (not direct calls)
- **Asynchronous**: Long-running operations use Celery task queues
- **Modular**: Clear separation of concerns
- **Resilient**: Circuit breakers, retries, fallbacks

**Tech Stack:**
- **Framework**: FastAPI + Starlette
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL + SQLAlchemy ORM
- **Async Runtime**: asyncio + uvicorn
- **Real-time**: WebSockets (Socket.io)
- **Monitoring**: Prometheus client library

## Directory Structure

```
src/backend/
├── main.py                        # Application entry point
├── config.py                      # Configuration & settings
├── requirements.txt               # Dependencies
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── auth.py               # /api/v1/auth/*
│   │   ├── workspaces.py         # /api/v1/workspaces/*
│   │   ├── sessions.py           # /api/v1/sessions/*
│   │   ├── providers.py          # /api/v1/providers/*
│   │   ├── workflows.py          # /api/v1/workflows/*
│   │   ├── storage.py            # /api/v1/storage/*
│   │   ├── assist.py             # /api/v1/assist/*
│   │   └── __init__.py
│   └── v2/                        # Future API versions
├── services/
│   ├── __init__.py
│   ├── auth_service.py           # OAuth, JWT, RBAC
│   ├── workspace_service.py      # Workspace CRUD
│   ├── session_service.py        # Session lifecycle
│   ├── provider_service.py       # Provider orchestration
│   ├── scheduler_service.py      # GPU scheduling
│   ├── workflow_service.py       # Workflow execution
│   ├── checkpoint_service.py     # Persistence & recovery
│   ├── storage_service.py        # S3/MinIO integration
│   ├── metrics_service.py        # Monitoring
│   └── ai_assist_service.py      # AI assistant
├── models/
│   ├── __init__.py
│   ├── user.py                   # User model
│   ├── workspace.py              # Workspace model
│   ├── session.py                # Session model
│   ├── workflow.py               # Workflow model
│   ├── checkpoint.py             # Checkpoint model
│   ├── provider_config.py        # Provider settings
│   └── metrics.py                # Metrics model
├── schemas/
│   ├── __init__.py
│   ├── user.py                   # User schemas
│   ├── workspace.py              # Workspace schemas
│   ├── session.py                # Session schemas
│   ├── workflow.py               # Workflow schemas
│   └── error.py                  # Error responses
├── providers/
│   ├── __init__.py
│   ├── base.py                   # ProviderBase interface
│   ├── runpod.py                 # RunPod plugin
│   ├── vastai.py                 # Vast.ai plugin
│   ├── lambda_labs.py            # Lambda Labs plugin
│   ├── paperspace.py             # Paperspace plugin
│   ├── local_docker.py           # Local Docker plugin
│   ├── registry.py               # Plugin registry
│   └── manager.py                # Provider manager
├── middleware/
│   ├── __init__.py
│   ├── auth.py                   # Authentication middleware
│   ├── cors.py                   # CORS configuration
│   ├── logging.py                # Structured logging
│   ├── error_handler.py          # Error handling
│   └── rate_limit.py             # Rate limiting
├── tasks/
│   ├── __init__.py
│   ├── workspace_tasks.py        # Workspace Celery tasks
│   ├── session_tasks.py          # Session management tasks
│   ├── workflow_tasks.py         # Workflow execution tasks
│   ├── checkpoint_tasks.py       # Checkpoint/recovery tasks
│   └── metrics_tasks.py          # Metrics collection tasks
├── utils/
│   ├── __init__.py
│   ├── security.py               # Encryption, hashing
│   ├── validators.py             # Data validation
│   ├── formatters.py             # Response formatting
│   ├── logger.py                 # Structured logging
│   └── errors.py                 # Custom exceptions
├── websocket/
│   ├── __init__.py
│   ├── manager.py                # WebSocket connection manager
│   ├── events.py                 # Event definitions
│   └── handlers.py               # Event handlers
├── db/
│   ├── __init__.py
│   ├── session.py                # Database session
│   ├── base.py                   # Base model
│   └── migrations/               # Alembic migrations
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_auth.py
    ├── test_providers.py
    └── test_workflows.py
```

## Application Initialization

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Startup/Shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_services()
    await setup_websocket_manager()
    celery_app.start()
    yield
    # Shutdown
    celery_app.stop()
    await cleanup_services()

app = FastAPI(
    title="Cloud OS API",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend.example.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware order matters!
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Routes
from api.v1 import router as api_v1
app.include_router(api_v1, prefix="/api/v1")

# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.handle_event(websocket, data)
    finally:
        await manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Core Services

### 1. Authentication Service

```python
# services/auth_service.py
class AuthService:
    """Handles OAuth, JWT, and RBAC"""
    
    async def exchange_oauth_code(
        self, 
        provider: str, 
        code: str
    ) -> tuple[User, str, str]:
        """Exchange OAuth code for tokens"""
        # 1. Call OAuth provider
        # 2. Get user info
        # 3. Find or create user in DB
        # 4. Generate JWT and Refresh Token
        # 5. Return both
        pass
    
    async def generate_jwt(self, user: User) -> str:
        """Generate short-lived JWT (15 min)"""
        payload = {
            'sub': str(user.id),
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(minutes=15)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    async def generate_refresh_token(self, user: User) -> str:
        """Generate long-lived refresh token (30 days)"""
        token = secrets.token_urlsafe(32)
        await db.refresh_tokens.insert({
            'user_id': str(user.id),
            'token': token,
            'expires_at': datetime.utcnow() + timedelta(days=30),
            'created_at': datetime.utcnow()
        })
        return token
    
    async def refresh_jwt(self, refresh_token: str) -> str:
        """Issue new JWT from refresh token"""
        record = await db.refresh_tokens.find_one({'token': refresh_token})
        if not record or record['expires_at'] < datetime.utcnow():
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({'id': record['user_id']})
        
        # Rotate refresh token
        await db.refresh_tokens.delete_one({'token': refresh_token})
        new_refresh_token = await self.generate_refresh_token(user)
        
        return await self.generate_jwt(user)
    
    async def verify_jwt(self, token: str) -> User:
        """Verify JWT and return user"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user = await db.users.find_one({'id': payload['sub']})
            if not user:
                raise HTTPException(status_code=401)
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
    
    async def has_permission(
        self, 
        user: User, 
        resource: str, 
        action: str
    ) -> bool:
        """Check RBAC permission"""
        # Check user role + resource permissions
        pass
```

### 2. Workspace Service

```python
# services/workspace_service.py
class WorkspaceService:
    """Manages workspace lifecycle"""
    
    async def create_workspace(
        self, 
        user: User, 
        config: CreateWorkspaceSchema
    ) -> Workspace:
        """Create new workspace"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name=config.name,
            base_image=config.base_image or "python:3.11",
            environment=config.environment or {},
            created_at=datetime.utcnow()
        )
        db.session.add(workspace)
        await db.session.commit()
        
        # Emit event
        await event_bus.publish("workspace.created", {
            "workspace_id": str(workspace.id),
            "user_id": str(user.id)
        })
        
        return workspace
    
    async def get_workspace(self, user: User, workspace_id: str) -> Workspace:
        """Get workspace with permission check"""
        workspace = await db.session.get(Workspace, workspace_id)
        if not workspace or workspace.user_id != user.id:
            raise HTTPException(status_code=404)
        return workspace
    
    async def update_workspace(
        self, 
        user: User, 
        workspace_id: str, 
        updates: Dict
    ) -> Workspace:
        """Update workspace"""
        workspace = await self.get_workspace(user, workspace_id)
        
        for key, value in updates.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)
        
        workspace.updated_at = datetime.utcnow()
        await db.session.commit()
        
        await event_bus.publish("workspace.updated", {
            "workspace_id": str(workspace.id)
        })
        
        return workspace
    
    async def delete_workspace(self, user: User, workspace_id: str):
        """Delete workspace (soft delete)"""
        workspace = await self.get_workspace(user, workspace_id)
        
        # Terminate any active sessions
        sessions = await db.session.query(Session).filter(
            Session.workspace_id == workspace.id,
            Session.status.in_(['active', 'paused'])
        ).all()
        
        for session in sessions:
            await session_service.terminate_session(session.id)
        
        # Soft delete
        workspace.deleted_at = datetime.utcnow()
        await db.session.commit()
        
        await event_bus.publish("workspace.deleted", {
            "workspace_id": str(workspace.id)
        })
```

### 3. Session Manager Service

```python
# services/session_service.py
class SessionService:
    """Manages session lifecycle and recovery"""
    
    async def create_session(
        self, 
        workspace: Workspace, 
        gpu_type: str | None = None
    ) -> Session:
        """Create new GPU session"""
        # 1. Query scheduler for best GPU
        gpu_allocation = await scheduler.allocate_gpu(
            workspace=workspace,
            preferred_type=gpu_type
        )
        
        # 2. Call provider to provision
        provider = provider_manager.get_provider(gpu_allocation.provider)
        compute_session = await provider.provision_session(
            workspace=workspace,
            gpu_spec=gpu_allocation.spec
        )
        
        # 3. Create DB record
        session = Session(
            id=str(uuid.uuid4()),
            workspace_id=workspace.id,
            provider=gpu_allocation.provider,
            provider_session_id=compute_session.id,
            gpu_model=compute_session.gpu_model,
            vram_gb=compute_session.vram_gb,
            status="active",
            created_at=datetime.utcnow()
        )
        db.session.add(session)
        await db.session.commit()
        
        # 4. Start auto-checkpoint task
        tasks.start_checkpoint_loop.delay(str(session.id))
        
        # 5. Start metrics collection
        tasks.collect_metrics.delay(str(session.id))
        
        return session
    
    async def get_session_metrics(
        self, 
        session_id: str, 
        time_range: TimeRange
    ) -> List[Metrics]:
        """Get historical metrics"""
        metrics = await db.session.query(Metrics).filter(
            Metrics.session_id == session_id,
            Metrics.timestamp.between(
                time_range.start,
                time_range.end
            )
        ).all()
        return metrics
    
    async def terminate_session(self, session_id: str):
        """Clean up session"""
        session = await db.session.get(Session, session_id)
        if not session:
            return
        
        # Call provider to terminate
        provider = provider_manager.get_provider(session.provider)
        await provider.terminate_session(session.provider_session_id)
        
        # Update DB
        session.status = "terminated"
        session.terminated_at = datetime.utcnow()
        await db.session.commit()
        
        await event_bus.publish("session.terminated", {
            "session_id": session_id
        })
    
    async def handle_session_failure(self, session_id: str):
        """Recover from session failure"""
        session = await db.session.get(Session, session_id)
        
        # Get latest checkpoint
        checkpoint = await db.session.query(Checkpoint).filter(
            Checkpoint.session_id == session_id
        ).order_by(Checkpoint.created_at.desc()).first()
        
        if not checkpoint:
            # Can't recover
            session.status = "failed"
            await db.session.commit()
            return
        
        # Try to restore from checkpoint
        try:
            # 1. Select new provider
            new_provider = await scheduler.allocate_gpu(
                workspace=session.workspace,
                exclude_provider=session.provider
            )
            
            # 2. Provision new session
            provider = provider_manager.get_provider(new_provider.provider)
            new_compute_session = await provider.restore_session(
                checkpoint_path=checkpoint.storage_path
            )
            
            # 3. Update session record
            session.provider = new_provider.provider
            session.provider_session_id = new_compute_session.id
            session.status = "recovered"
            session.updated_at = datetime.utcnow()
            
            await db.session.commit()
            
            await event_bus.publish("session.recovered", {
                "session_id": session_id,
                "new_provider": new_provider.provider
            })
        except Exception as e:
            session.status = "recovery_failed"
            await db.session.commit()
            raise
```

### 4. GPU Scheduler

```python
# services/scheduler_service.py
class GPUScheduler:
    """Intelligent GPU allocation and scheduling"""
    
    async def allocate_gpu(
        self, 
        workspace: Workspace,
        preferred_type: str | None = None,
        exclude_provider: str | None = None
    ) -> GPUAllocation:
        """Select best GPU for workload"""
        
        # 1. Collect all available GPUs from all providers
        available_gpus = await self._collect_gpu_inventory()
        
        # 2. Filter by requirements
        candidates = [
            gpu for gpu in available_gpus
            if (
                gpu.provider != exclude_provider and
                self._meets_requirements(gpu, workspace)
            )
        ]
        
        # 3. Score candidates
        scores = {
            gpu.id: self._score_gpu(gpu, workspace)
            for gpu in candidates
        }
        
        # 4. Select best
        best_gpu_id = max(scores, key=scores.get)
        best_gpu = next(g for g in candidates if g.id == best_gpu_id)
        
        return GPUAllocation(
            gpu_id=best_gpu.id,
            provider=best_gpu.provider,
            spec={
                'gpu_model': best_gpu.model,
                'vram_gb': best_gpu.vram_gb,
                'cuda_version': best_gpu.cuda_version
            }
        )
    
    def _score_gpu(self, gpu: GPU, workspace: Workspace) -> float:
        """Score GPU suitability"""
        score = 0.0
        
        # Factor 1: Cost (cheaper = higher score)
        cost_factor = 1.0 / (gpu.hourly_cost + 0.01)
        score += cost_factor * 0.3
        
        # Factor 2: Availability (less utilized = higher score)
        availability_factor = 1.0 - gpu.utilization
        score += availability_factor * 0.3
        
        # Factor 3: Performance (faster = higher score)
        performance_factor = gpu.flops / 1e12  # Normalize to TFLOPs
        score += performance_factor * 0.2
        
        # Factor 4: Latency (lower = higher score)
        latency_factor = 1.0 / (gpu.latency_ms + 1)
        score += latency_factor * 0.2
        
        return score
    
    async def _collect_gpu_inventory(self) -> List[GPU]:
        """Query all providers for available GPUs"""
        inventory = []
        
        providers = provider_manager.get_all_providers()
        
        tasks = [
            provider.get_available_gpus()
            for provider in providers
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                logger.error(f"Provider {provider.name} error: {result}")
                continue
            
            for gpu in result:
                gpu.provider = provider.name
                inventory.append(gpu)
        
        return inventory
```

### 5. Workflow Engine

```python
# services/workflow_service.py
class WorkflowService:
    """Executes visual workflows"""
    
    async def execute_workflow(
        self, 
        workflow: Workflow, 
        session: Session
    ) -> WorkflowRun:
        """Start workflow execution"""
        
        # 1. Parse and validate DAG
        dag = WorkflowDAG.from_definition(workflow.definition)
        if not dag.is_valid():
            raise HTTPException(status_code=400, detail="Invalid workflow DAG")
        
        # 2. Create run record
        run = WorkflowRun(
            id=str(uuid.uuid4()),
            workflow_id=workflow.id,
            session_id=session.id,
            status="pending",
            created_at=datetime.utcnow()
        )
        db.session.add(run)
        await db.session.commit()
        
        # 3. Queue execution task
        tasks.execute_workflow_dag.delay(
            str(workflow.id),
            str(run.id),
            str(session.id),
            dag.to_dict()
        )
        
        return run
    
    async def execute_node(
        self, 
        node: WorkflowNode, 
        inputs: Dict,
        session: Session
    ) -> Any:
        """Execute single workflow node"""
        
        if node.type == "python_code":
            return await self._execute_python_node(node, inputs, session)
        elif node.type == "fine_tune":
            return await self._execute_fine_tune_node(node, inputs, session)
        elif node.type == "inference":
            return await self._execute_inference_node(node, inputs, session)
        # ... other node types
        else:
            raise ValueError(f"Unknown node type: {node.type}")
    
    async def _execute_python_node(
        self, 
        node: WorkflowNode, 
        inputs: Dict,
        session: Session
    ) -> str:
        """Execute Python code in session"""
        
        # Prepare code
        code = node.config['code']
        
        # Prepare environment
        env_vars = {
            'WORKFLOW_RUN_ID': node.run_id,
            'NODE_ID': node.id,
            **inputs
        }
        
        # Execute remotely via provider
        provider = provider_manager.get_provider(session.provider)
        result = await provider.execute_command(
            session.provider_session_id,
            f"python -c {repr(code)}"
        )
        
        return result
```

### 6. AI Assistant Service

```python
# services/ai_assist_service.py
class AIAssistService:
    """LLM-powered assistance"""
    
    async def generate_environment(self, prompt: str) -> EnvironmentGeneration:
        """Generate Dockerfile and setup from prompt"""
        
        # 1. Call LLM
        response = await self.llm_client.complete(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_DOCKERFILE
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            functions=[
                {
                    "name": "create_dockerfile",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dockerfile": {"type": "string"},
                            "env_vars": {"type": "object"},
                            "required_gpu_vram": {"type": "integer"},
                            "estimated_gpu_model": {"type": "string"}
                        }
                    }
                }
            ]
        )
        
        # 2. Parse response
        result = json.loads(response)
        
        return EnvironmentGeneration(
            dockerfile=result['dockerfile'],
            environment=result['env_vars'],
            gpu_requirements={
                'vram_gb': result['required_gpu_vram'],
                'model': result['estimated_gpu_model']
            }
        )
    
    async def fix_error(
        self, 
        error_message: str, 
        logs: str,
        context: Dict
    ) -> str:
        """AI-powered error diagnosis and fixing"""
        
        response = await self.llm_client.complete(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_DEBUGGING
                },
                {
                    "role": "user",
                    "content": f"""
Error: {error_message}

Logs:
{logs}

Context: {json.dumps(context)}

Provide a fix or workaround.
"""
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
```

## Celery Task Queue

```python
# tasks/__init__.py
from celery import Celery

celery_app = Celery('cloud-os')
celery_app.conf.broker_url = REDIS_URL
celery_app.conf.result_backend = REDIS_URL

# tasks/checkpoint_tasks.py
@celery_app.task(bind=True, max_retries=3)
def start_checkpoint_loop(self, session_id: str):
    """Periodically checkpoint session"""
    while True:
        try:
            asyncio.run(checkpoint_service.create_checkpoint(session_id))
            time.sleep(300)  # Every 5 minutes
        except Exception as exc:
            self.retry(exc=exc, countdown=60)

@celery_app.task(bind=True)
def execute_workflow_dag(self, workflow_id: str, run_id: str, session_id: str, dag: dict):
    """Execute workflow with fanout/join pattern"""
    
    session = db.session.get(Session, session_id)
    run = db.session.get(WorkflowRun, run_id)
    
    try:
        # Execute DAG using topological sort
        dag_obj = WorkflowDAG.from_dict(dag)
        
        for node in dag_obj.topological_sort():
            # Get inputs from previous nodes
            inputs = {
                dep_id: results.get(dep_id)
                for dep_id in node.dependencies
            }
            
            # Execute node
            result = asyncio.run(
                workflow_service.execute_node(node, inputs, session)
            )
            
            results[node.id] = result
            
            # Emit progress
            event_bus.publish(f"workflow.node_completed.{run_id}", {
                "node_id": node.id,
                "result": result
            })
        
        # Mark run as completed
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.result = results
        
    except Exception as e:
        run.status = "failed"
        run.error_message = str(e)
    
    finally:
        db.session.commit()
```

## Error Handling Middleware

```python
# middleware/error_handler.py
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": request.headers.get("X-Request-ID")
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request.headers.get("X-Request-ID")
        }
    )
```

## Configuration Management

```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    
    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 3600
    
    # Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15
    
    # Providers
    ENABLED_PROVIDERS: list = ["runpod", "vastai", "local_docker"]
    
    # Storage
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    
    # LLM
    OPENAI_API_KEY: str
    DEFAULT_LLM_MODEL: str = "gpt-4"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Next Steps

- See [Database Schema](../design/DATABASE_SCHEMA.md)
- Review [Provider SDK](../design/PROVIDER_SDK.md)
- See [API Specifications](../api/API_SPECIFICATIONS.md)
- Check [Deployment Guide](../operations/DEPLOYMENT.md)
