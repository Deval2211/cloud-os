# Universal AI Cloud OS

A production-grade, open-source (AGPL) browser-based cloud operating system for AI development, GPU orchestration, and distributed compute management.

**Status**: Architecture & Design Phase

## Overview

Universal AI Cloud OS is a unified platform that brings together:
- **Cloud GPU providers** (RunPod, Vast.ai, Lambda Labs, Google Colab, Kaggle)
- **Local GPU clusters** (homelabs, self-hosted servers)
- **Decentralized edge nodes** (future marketplace-ready architecture)
- **AI development tools** (VSCode in browser, Jupyter, workflow automation)
- **GPU orchestration** (intelligent scheduling, resource allocation, failover recovery)

Users get a **futuristic Linux cloud desktop** with:
- Persistent sessions & automatic checkpoint recovery
- Browser-based IDE with full VSCode capabilities
- Visual workflow automation (n8n/ComfyUI-style)
- Real-time GPU monitoring & smart taskbar
- AI-native assistant for environment setup & optimization
- Multi-user collaboration support

## Core Philosophy

- **Lightweight** - minimal overhead, maximum performance
- **Cloud-native** - Kubernetes-ready from day one
- **AI-native** - optimized for GPU workloads & model training
- **Developer-first** - tools developers love
- **GPU-focused** - intelligent scheduling & orchestration
- **Workflow-focused** - automate complex compute tasks
- **Browser-first** - no installation needed

## Key Features

### 1. Browser-Based Cloud Desktop
Modern Linux-inspired desktop environment with floating windows, taskbar, multi-workspace support, and persistent layout state.

### 2. Real-time GPU Monitoring
Smart taskbar showing active GPUs, VRAM usage, running workloads, training jobs, and live metrics via WebSockets.

### 3. Full Browser IDE
Integrated code-server (VSCode in browser) with extensions, terminals, notebooks, debugging, and AI coding assistants.

### 4. Visual Workflow Engine
n8n/ComfyUI-inspired drag-and-drop workflow builder for AI pipelines, fine-tuning, inference, and dataset automation.

### 5. Modular Provider System
Hot-pluggable provider plugins supporting 10+ GPU cloud providers and unlimited edge agents.

### 6. Session Persistence & Checkpoint Recovery
Auto-save environments, auto-checkpoint training states, persistent notebooks, and automatic recovery on provider failure.

### 7. AI-Native Assistant System
Built-in LLM-powered agents that can:
- Generate environments from natural language
- Auto-fix CUDA issues
- Optimize VRAM usage
- Orchestrate complex workflows
- Deploy inference servers

### 8. Edge Agent Network
Lightweight agents deployable on local PCs, homelabs, and university GPUs for decentralized compute orchestration.

### 9. Container & Kubernetes Orchestration
Docker-based initially with Kubernetes-compatible architecture from the start.

### 10. Enterprise Security
OAuth2 authentication, encrypted secrets, RBAC, multi-tenant architecture, zero-trust principles.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js, React, TailwindCSS, Zustand, Framer Motion |
| **Desktop UI** | Custom React window manager |
| **IDE** | code-server (VSCode) |
| **Backend** | FastAPI (Python) |
| **Realtime** | WebSockets, Server-Sent Events |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL |
| **Storage** | MinIO/S3 |
| **Monitoring** | Prometheus, Grafana, NVIDIA DCGM |
| **Containers** | Docker, Kubernetes-ready |
| **Streaming** | WebRTC, noVNC, xterm.js |
| **License** | AGPL v3 |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER BROWSER                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Desktop Environment (React)                 │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐   │  │
│  │  │ Taskbar │ │ Workflow │ │IDE/Editor│ │Terminal│   │  │
│  │  │ & GPU   │ │ Builder  │ │(Server)  │ │ (xterm)│   │  │
│  │  │Monitor  │ │          │ │          │ │        │   │  │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────┘   │  │
│  └───────────────────────────────────────────────────────┘  │
│                         ▼ WebSocket/REST                     │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Gateway & Auth Service                          │   │
│  └──────────────────────────────────────────────────────┘   │
│         ▼                    ▼                    ▼           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Workspace    │  │ Provider     │  │ GPU Scheduler &  │  │
│  │ Manager      │  │ Orchestrator │  │ Resource Manager │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         ▼                    ▼                    ▼           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Workflow     │  │ Session      │  │ AI Assistant     │  │
│  │ Engine       │  │ Manager      │  │ Service          │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         ▼                    ▼                    ▼           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Checkpoint   │  │ Storage      │  │ Monitoring &     │  │
│  │ Manager      │  │ Integration  │  │ Metrics Engine   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│              ▼                              ▼                 │
│         ┌──────────────────────────────────┐                │
│         │     PostgreSQL + Redis Cache     │                │
│         └──────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            PROVIDER NETWORK & COMPUTE LAYER                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  RunPod  │ │Vast.ai   │ │Paperspace│ │  Local Agents│   │
│  │  Plugin  │ │Plugin    │ │Plugin    │ │  (Docker)    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│            ▼                                   ▼              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Kubernetes / Docker Swarm Orchestration Layer      │   │
│  │  (GPU allocation, isolation, networking)           │   │
│  └─────────────────────────────────────────────────────┘   │
│            ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  GPU Execution Engines (Docker containers)          │   │
│  │  - Jupyter Kernels                                  │   │
│  │  - VSCode Server                                    │   │
│  │  - Training Jobs (PyTorch, TensorFlow)              │   │
│  │  - Inference Servers (vLLM, TGI, Ollama)            │   │
│  │  - Linux Desktop Stream (WebRTC/noVNC)              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL INTEGRATIONS                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ S3/MinIO │ │HuggingFace│ │Google    │ │OpenAI/Claude │   │
│  │ Storage  │ │Model Hub │ │Drive     │ │ LLM APIs     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
cloud-os/
├── README.md
├── LICENSE (AGPL-v3)
├── docker-compose.yml
├── Dockerfile
├── kubernetes/                    # K8s manifests
├── src/
│   ├── frontend/                  # Next.js frontend
│   │   ├── app/
│   │   ├── components/            # React components
│   │   ├── lib/
│   │   ├── styles/
│   │   ├── hooks/
│   │   └── pages/
│   ├── backend/                   # FastAPI backend
│   │   ├── main.py
│   │   ├── api/                   # API routes
│   │   ├── services/              # Business logic
│   │   ├── models/                # Data models
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── providers/             # Provider implementations
│   │   ├── middleware/
│   │   ├── auth/
│   │   ├── config/
│   │   └── utils/
│   ├── edge-agent/                # Edge agent (Go/Python)
│   │   ├── main.py
│   │   ├── executor/
│   │   ├── registry/
│   │   ├── metrics/
│   │   └── auth/
│   ├── provider-sdk/              # Provider plugin SDK
│   │   ├── base.py
│   │   ├── interfaces.py
│   │   ├── examples/
│   │   └── utils/
│   └── shared/                    # Shared types & utils
│       ├── types.ts
│       ├── constants.ts
│       └── helpers.ts
├── docs/
│   ├── architecture/              # Architecture documents
│   ├── design/                    # Component designs
│   ├── api/                       # API specifications
│   └── operations/                # Deployment & ops
├── tests/
│   ├── frontend/
│   ├── backend/
│   └── integration/
├── scripts/
│   ├── setup-dev.sh
│   ├── deploy.sh
│   └── migrate-db.sh
└── .github/
    └── workflows/                 # CI/CD pipelines
```

## Quick Links

- [Core Architecture](docs/architecture/00-CORE_ARCHITECTURE.md)
- [Frontend Architecture](docs/architecture/01-FRONTEND_ARCHITECTURE.md)
- [Backend Architecture](docs/architecture/02-BACKEND_ARCHITECTURE.md)
- [Database Schema](docs/design/DATABASE_SCHEMA.md)
- [Provider Plugin SDK](docs/design/PROVIDER_SDK.md)
- [Workflow Engine Design](docs/design/WORKFLOW_ENGINE.md)
- [GPU Scheduler](docs/design/GPU_SCHEDULER.md)
- [Session Persistence](docs/design/SESSION_PERSISTENCE.md)
- [Security Architecture](docs/design/SECURITY_ARCHITECTURE.md)
- [API Specifications](docs/api/API_SPECIFICATIONS.md)
- [Deployment Guide](docs/operations/DEPLOYMENT.md)
- [MVP Roadmap](docs/operations/MVP_ROADMAP.md)

## Getting Started

See [docs/operations/DEPLOYMENT.md](docs/operations/DEPLOYMENT.md) for development setup and deployment instructions.

## License

AGPL v3 - See LICENSE file for details

## Contributing

We welcome contributions! Please read CONTRIBUTING.md (coming soon).

---

**Built with enterprise-grade architecture. AI-native. GPU-focused. Browser-first.**
