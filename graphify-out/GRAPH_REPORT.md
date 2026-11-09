# Graph Report - /home/deval/Projects/cloud_os  (2026-05-29)

## Corpus Check
- Corpus is ~46,414 words - fits in a single context window. You may not need a graph.

## Summary
- 505 nodes · 769 edges · 32 communities detected
- Extraction: 68% EXTRACTED · 32% INFERRED · 0% AMBIGUOUS · INFERRED: 245 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Workflow Execution|Workflow Execution]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Workflow Execution|Workflow Execution]]
- [[_COMMUNITY_GPU Provider System|GPU Provider System]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Real-Time Events|Real-Time Events]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Workflow Execution|Workflow Execution]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Real-Time Events|Real-Time Events]]
- [[_COMMUNITY_Data Models|Data Models]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Frontend UI|Frontend UI]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Real-Time Events|Real-Time Events]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Authentication & Authorization|Authentication & Authorization]]
- [[_COMMUNITY_Community 51|Community 51]]

## God Nodes (most connected - your core abstractions)
1. `User` - 73 edges
2. `Workspace` - 40 edges
3. `ApiClient` - 27 edges
4. `WebSocketEvent` - 25 edges
5. `WorkspaceSession` - 23 edges
6. `EventType` - 23 edges
7. `TestWorkspaceEndpoints` - 12 edges
8. `WebSocketClient` - 12 edges
9. `websocket_endpoint()` - 11 edges
10. `TokenResponse` - 11 edges

## Surprising Connections (you probably didn't know these)
- `get_current_user Dependency` --references--> `User`  [EXTRACTED]
  src/backend/routes/auth.py → /home/deval/Projects/cloud_os/src/backend/models.py
- `get_user_info Method` --shares_data_with--> `User`  [INFERRED]
  src/backend/auth/github.py → /home/deval/Projects/cloud_os/src/backend/models.py
- `create_refresh_token Function` --shares_data_with--> `User`  [INFERRED]
  src/backend/auth/db.py → /home/deval/Projects/cloud_os/src/backend/models.py
- `WorkspaceService` --shares_data_with--> `Workspace`  [INFERRED]
  src/backend/routes/workspaces.py → /home/deval/Projects/cloud_os/src/backend/models.py
- `SessionService` --shares_data_with--> `WorkspaceSession`  [INFERRED]
  src/backend/routes/sessions.py → /home/deval/Projects/cloud_os/src/backend/models.py

## Hyperedges (group relationships)
- **OAuth to JWT Authentication Flow** — auth_github_githuboauthservice, auth_db_get_user_by_github_id, auth_db_create_user, auth_utils_create_access_token, routes_auth_github_callback [EXTRACTED 1.00]
- **Real-time WebSocket Event System** — websocket_manager_eventtype, websocket_manager_websocketevent, websocket_manager_connectionmanager, websocket_routes_websocket_endpoint [EXTRACTED 0.95]
- **Session Management Service** — routes_sessions_sessionservice, routes_sessions_create_session, models_workspacesession, tasks_provision_gpu_session [INFERRED 0.85]
- **Session Management System** — hook_use_sessions, websocket_client, api_client, comp_sessions_panel [INFERRED 0.88]
- **Metrics Collection Pipeline** — websocket_client, hook_use_session_metrics, comp_metrics_dashboard, type_session_metrics [INFERRED 0.85]
- **Authentication System** — pattern_oauth_flow, api_client, store_auth, page_auth_callback, comp_auth_page [INFERRED 0.90]
- **Desktop Environment** — pattern_desktop_ui, comp_workspace_window, comp_desktop_taskbar, store_desktop [INFERRED 0.87]
- **Workspace Context System** — store_workspace, store_session, api_client, comp_workspace_window, type_workspace [INFERRED 0.82]
- **connected_session_lifecycle** — frontend_auth_store, frontend_websocket_store, frontend_session_store [INFERRED 0.88]
- **state_management_trio** — frontend_auth_store, frontend_websocket_store, frontend_session_store [INFERRED 0.90]
- **Real-Time Streaming Architecture** — websocket_manager, frontend_websocket_client, metrics_collection, session_manager [INFERRED 0.90]
- **Authentication & Authorization Flow** — auth_service, auth_oauth2, auth_jwt, database_postgres, frontend_desktop [INFERRED 0.95]
- **GPU Allocation Pipeline** — gpu_scheduler, provider_system, session_manager, workspace_model [INFERRED 0.90]
- **Session Persistence & Failover** — session_manager, checkpoint_service, storage_integration, provider_system [INFERRED 0.95]
- **Distributed Workflow Execution** — workflow_engine, backend_celery, session_manager, websocket_manager, storage_integration [INFERRED 0.90]
- **Hot-Pluggable Provider Architecture** — provider_system, provider_interface, provider_runpod, provider_vastai, provider_lambda, provider_paperspace, provider_local_docker [INFERRED 0.95]
- **Backend Infrastructure Stack** — backend_fastapi, backend_sqlalchemy, backend_celery, database_postgres, cache_redis, docker_orchestration [INFERRED 0.95]

## Communities

### Community 0 - "Authentication & Authorization"
Cohesion: 0.04
Nodes (52): create_refresh_token Function, create_user Function, get_user_by_github_id Function, update_user Function, get_user_info Method, generate_refresh_token Function, hash_token Function, User model - Authentication and profile (+44 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (53): Enum, ConnectionManager, EventType, from_json(), WebSocket connection management and real-time events, Register new connection, Unregister connection, Broadcast event to all users in workspace (+45 more)

### Community 2 - "Authentication & Authorization"
Cohesion: 0.05
Nodes (56): JWT Tokens, OAuth2 Authentication, Role-Based Access Control, Authentication Service, Backend API, Celery Task Queue, FastAPI Framework, SQLAlchemy ORM (+48 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (44): get_current_user(), get_current_user_info(), github_callback(), github_login(), Authentication routes, Get current user information, Refresh access token using refresh token from cookie, Dependency to get current authenticated user (+36 more)

### Community 4 - "Authentication & Authorization"
Cohesion: 0.09
Nodes (37): ApiClient Class, AuthPage Component, DesktopTaskbar Component, EditorWindow Component, FileBrowser Component, MetricsDashboard Component, SessionsPanel Component, TerminalWindow Component (+29 more)

### Community 5 - "Workflow Execution"
Cohesion: 0.06
Nodes (5): handleGithubLogin(), ApiClient, initializeApp(), handleStartSession(), handleStopSession()

### Community 6 - "Authentication & Authorization"
Cohesion: 0.09
Nodes (23): create_refresh_token(), create_user(), get_db_session(), get_user_by_github_id(), Database operations for authentication, Dependency for getting database session, Fetch user by GitHub ID, Create a refresh token for the user (+15 more)

### Community 7 - "Workflow Execution"
Cohesion: 0.08
Nodes (23): cleanup_expired_checkpoints(), collect_system_metrics(), collect_workflow_results(), create_checkpoint(), execute_workflow_node(), monitor_session_metrics(), process_ai_request(), provision_gpu_session() (+15 more)

### Community 8 - "GPU Provider System"
Cohesion: 0.15
Nodes (17): Base, AuditLog, Checkpoint, Metrics, ProviderCredentials, SQLAlchemy database models for Cloud OS, Checkpoint model - Session snapshots for recovery, Workflow model - DAG definitions (+9 more)

### Community 9 - "Authentication & Authorization"
Cohesion: 0.17
Nodes (12): exchange_code_for_token Method, create_access_token Function, verify_token Function, BaseSettings, Config, Configuration management for Cloud OS Backend, Application settings from environment variables, Settings (+4 more)

### Community 10 - "Real-Time Events"
Cohesion: 0.18
Nodes (1): WebSocketClient

### Community 11 - "Authentication & Authorization"
Cohesion: 0.18
Nodes (11): frontend_auth_state, frontend_auth_store, frontend_event_type, frontend_session_metrics, frontend_session_state, frontend_session_store, frontend_user, frontend_websocket_client (+3 more)

### Community 12 - "Workflow Execution"
Cohesion: 0.22
Nodes (2): handleCanvasMouseMove(), updateNode()

### Community 13 - "Community 13"
Cohesion: 0.4
Nodes (2): handleKeyDown(), handleSave()

### Community 15 - "Real-Time Events"
Cohesion: 0.4
Nodes (5): broadcast_to_workspace Method, ConnectionManager Class, EventType Enum, WebSocketEvent Class, websocket_endpoint Route

### Community 16 - "Data Models"
Cohesion: 0.5
Nodes (3): init_db(), Database initialization script, Initialize database with all tables

### Community 18 - "Authentication & Authorization"
Cohesion: 0.5
Nodes (4): Phase 1: Infrastructure Scaffolding, Phase 2: Authentication & Workspaces, Phase 3: WebSocket Real-Time, Phase 4: Session Provisioning

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (2): handleCommand(), handleKeyDown()

### Community 20 - "Community 20"
Cohesion: 0.67
Nodes (3): Autoprefixer, PostCSS Configuration, Tailwind CSS

### Community 21 - "Frontend UI"
Cohesion: 0.67
Nodes (3): Frontend Application, Next.js Configuration, Tailwind CSS Config

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Cloud OS Backend Package

### Community 27 - "Authentication & Authorization"
Cohesion: 1.0
Nodes (2): GitHubOAuthService, github_login Endpoint

### Community 30 - "Real-Time Events"
Cohesion: 1.0
Nodes (1): Create event from JSON

### Community 33 - "Authentication & Authorization"
Cohesion: 1.0
Nodes (1): Get GitHub OAuth authorization URL and state token

### Community 34 - "Authentication & Authorization"
Cohesion: 1.0
Nodes (1): Exchange authorization code for access token

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Get GitHub user information

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Delete workspace (soft delete)

### Community 47 - "Community 47"
Cohesion: 1.0
Nodes (1): UserResponse Schema

### Community 48 - "Authentication & Authorization"
Cohesion: 1.0
Nodes (1): TokenResponse Schema

### Community 49 - "Community 49"
Cohesion: 1.0
Nodes (1): CurrentUserResponse Schema

### Community 50 - "Authentication & Authorization"
Cohesion: 1.0
Nodes (1): verify_refresh_token Function

### Community 51 - "Community 51"
Cohesion: 1.0
Nodes (1): Root Layout

## Knowledge Gaps
- **84 isolated node(s):** `Celery task definitions for Cloud OS Backend`, `Provision a GPU session`, `Monitor session metrics`, `Create a checkpoint for a session`, `Restore a session from checkpoint` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Real-Time Events`** (12 nodes): `websocket.ts`, `WebSocketClient`, `.attemptReconnect()`, `.constructor()`, `.disconnect()`, `.handleMessage()`, `.isConnected()`, `.off()`, `.on()`, `.sendEvent()`, `.startHeartbeat()`, `.stopHeartbeat()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Workflow Execution`** (10 nodes): `WorkflowBuilder.tsx`, `addEdge()`, `addNode()`, `deleteNode()`, `handleCanvasMouseMove()`, `handleCanvasMouseUp()`, `handleNodeMouseDown()`, `handleSave()`, `nodeColor()`, `updateNode()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (6 nodes): `getLanguage()`, `handleKeyDown()`, `handleSave()`, `handleScroll()`, `updateLineNumbers()`, `EditorWindow.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (3 nodes): `TerminalWindow.tsx`, `handleCommand()`, `handleKeyDown()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `Cloud OS Backend Package`, `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Authentication & Authorization`** (2 nodes): `GitHubOAuthService`, `github_login Endpoint`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Real-Time Events`** (1 nodes): `Create event from JSON`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Authentication & Authorization`** (1 nodes): `Get GitHub OAuth authorization URL and state token`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Authentication & Authorization`** (1 nodes): `Exchange authorization code for access token`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Get GitHub user information`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Delete workspace (soft delete)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `UserResponse Schema`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Authentication & Authorization`** (1 nodes): `TokenResponse Schema`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 49`** (1 nodes): `CurrentUserResponse Schema`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Authentication & Authorization`** (1 nodes): `verify_refresh_token Function`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 51`** (1 nodes): `Root Layout`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Authentication & Authorization` to `Community 1`, `Community 3`, `Authentication & Authorization`, `GPU Provider System`, `Authentication & Authorization`?**
  _High betweenness centrality (0.235) - this node is a cross-community bridge._
- **Why does `WorkspaceSession` connect `Community 1` to `GPU Provider System`, `Workflow Execution`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `Workspace` connect `Community 1` to `GPU Provider System`, `Authentication & Authorization`, `Community 3`, `Real-Time Events`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 67 inferred relationships involving `User` (e.g. with `TestAuthEndpoints` and `TestWorkspaceEndpoints`) actually correct?**
  _`User` has 67 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `Workspace` (e.g. with `WebSocket routes for real-time events` and `Extract user from WebSocket token`) actually correct?**
  _`Workspace` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `WebSocketEvent` (e.g. with `WebSocket routes for real-time events` and `Extract user from WebSocket token`) actually correct?**
  _`WebSocketEvent` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `WorkspaceSession` (e.g. with `SessionService` and `SessionCreate`) actually correct?**
  _`WorkspaceSession` has 19 INFERRED edges - model-reasoned connections that need verification._