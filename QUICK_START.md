# Cloud OS - Quick Start Guide

Welcome to Cloud OS! This guide will help you set up and run the platform locally.

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Git

## Initial Setup

### 1. Clone the Repository

```bash
cd /home/deval/Projects/cloud os
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your configuration:
- Set `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` (create a GitHub OAuth app at https://github.com/settings/developers)
- Other values can be left as defaults for local development

### 3. Start Docker Containers

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- MinIO S3 (port 9000)
- FastAPI Backend (port 8000)
- Celery Worker
- Next.js Frontend (port 3000)
- Prometheus (port 9090)
- Grafana (port 3001)

### 4. Initialize Database

The database is automatically initialized when the backend container starts. Migrations will run automatically.

If you need to manually reset the database:

```bash
docker-compose exec backend python -m db.init_db
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin)

## Development Workflow

### Backend Development

Watch backend logs:
```bash
docker-compose logs -f backend
```

Restart backend after code changes:
```bash
docker-compose restart backend
```

### Frontend Development

Watch frontend logs:
```bash
docker-compose logs -f frontend
```

The frontend automatically reloads on code changes (hot reload enabled).

### Database Migrations

To create a new migration:

```bash
docker-compose exec backend alembic revision --autogenerate -m "Description"
```

To apply migrations:

```bash
docker-compose exec backend alembic upgrade head
```

## Common Commands

### View Container Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Access Container Shell

```bash
# Backend
docker-compose exec backend bash

# Frontend
docker-compose exec frontend sh

# PostgreSQL
docker-compose exec postgres psql -U postgres -d cloud_os
```

### Stop All Services

```bash
docker-compose down
```

### Reset Everything

```bash
# Stop and remove all containers/volumes
docker-compose down -v

# Restart
docker-compose up -d
```

## Testing the API

### Health Check

```bash
curl http://localhost:8000/health
```

### API Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## GitHub OAuth Setup

1. Go to https://github.com/settings/developers
2. Create a new OAuth Application
3. Set Authorization callback URL to: `http://localhost:8000/api/v1/auth/github/callback`
4. Copy Client ID and Client Secret to `.env`
5. Restart backend: `docker-compose restart backend`

## Next Steps

1. **Read Documentation**:
   - [Architecture Overview](docs/architecture/00-CORE_ARCHITECTURE.md)
   - [Frontend Architecture](docs/architecture/01-FRONTEND_ARCHITECTURE.md)
   - [Backend Architecture](docs/architecture/02-BACKEND_ARCHITECTURE.md)
   - [API Specifications](docs/api/API_SPECIFICATIONS.md)

2. **Implement Features** (See [MVP Roadmap](docs/operations/MVP_ROADMAP.md)):
   - Authentication (OAuth2 + JWT)
   - Workspace Management
   - GPU Session Provisioning
   - WebSocket Real-time Events
   - Workflow Engine
   - Provider Integration (RunPod, Vast.ai)

3. **Set Up CI/CD**:
   - Configure GitHub Actions
   - Set up automated testing
   - Configure deployment pipeline

## Troubleshooting

### Port Already in Use

If a port is already in use, you can change it in `docker-compose.yml`.

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Connect directly
docker-compose exec postgres psql -U postgres
```

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Try rebuilding
docker-compose build --no-cache backend
docker-compose up backend
```

### Frontend Won't Load

```bash
# Clear Node cache
docker-compose exec frontend rm -rf node_modules .next

# Rebuild
docker-compose down frontend
docker-compose up -d frontend
```

## Performance Tips

- Use `docker-compose exec` instead of SSH for accessing containers (faster)
- Set `DEBUG=false` in production
- Configure proper database connection pooling
- Use CDN for static assets
- Enable Prometheus scraping for metrics

## Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Configure HTTPS with proper SSL certificates
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Regular backups of PostgreSQL data
- [ ] Rotate encryption keys regularly

## Getting Help

- Check [architecture docs](docs/)
- Review [API specifications](docs/api/API_SPECIFICATIONS.md)
- Check container logs
- Open GitHub Issues

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Create a pull request
5. Wait for CI/CD and review

## License

AGPL-3.0-or-later - See LICENSE file for details

---

Happy hacking! 🚀
