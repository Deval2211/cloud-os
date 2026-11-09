# OAuth Setup & Testing Guide

## Quick Setup

### 1. Create GitHub OAuth Application

1. Go to https://github.com/settings/developers
2. Click **"New OAuth App"** button
3. Fill in the form:
   - **Application name**: `Cloud OS Dev` (or any name)
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:8000/api/v1/auth/github/callback`
4. Click **"Create OAuth App"**
5. Copy **Client ID** and generate **Client Secret**

### 2. Configure Environment

```bash
cd /home/deval/Projects/cloud\ os

# Edit .env with your GitHub credentials
cat > .env << EOF
ENVIRONMENT=development
DEBUG=true
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

DATABASE_URL=postgresql://postgres:postgres@postgres:5432/cloud_os
REDIS_URL=redis://redis:6379

GITHUB_CLIENT_ID=YOUR_CLIENT_ID_HERE
GITHUB_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback

MINIO_ENDPOINT=minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
EOF
```

### 3. Start Services

```bash
# Start Docker containers
docker-compose up -d

# Wait for services to be healthy
docker-compose exec backend curl http://localhost:8000/health
```

### 4. Test OAuth Flow

#### Via Browser

1. Open http://localhost:3000
2. Click **"Sign in with GitHub"**
3. Authorize the application
4. Should redirect to dashboard
5. Check browser DevTools Console for access token

#### Via cURL (Manual Testing)

```bash
# 1. Get OAuth URL
curl http://localhost:8000/api/v1/auth/github

# Response:
# {
#   "url": "https://github.com/login/oauth/authorize?client_id=...",
#   "state": "..."
# }

# 2. Visit URL in browser and get authorization code
# 3. Exchange code for tokens (replace CODE with actual code)
curl -X POST http://localhost:8000/api/v1/auth/github/callback \
  -H "Content-Type: application/json" \
  -d '{
    "code": "YOUR_AUTH_CODE_HERE",
    "state": "YOUR_STATE_HERE"
  }'

# Response:
# {
#   "user": {
#     "id": "...",
#     "username": "...",
#     "email": "...",
#     "display_name": "...",
#     "is_active": true,
#     "is_admin": false,
#     "created_at": "...",
#     "updated_at": "..."
#   },
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer",
#   "expires_in": 900
# }

# 4. Use access token for protected endpoints
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/v1/auth/me

# Response:
# {
#   "user": { ... },
#   "token": {
#     "access_token": "...",
#     "refresh_token": "...",
#     "token_type": "bearer",
#     "expires_in": 900
#   }
# }
```

## Workspace CRUD Testing

### Create Workspace

```bash
TOKEN="your_access_token"

curl -X POST http://localhost:8000/api/v1/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Project",
    "description": "A place to build cool stuff"
  }'
```

### List Workspaces

```bash
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/workspaces
```

### Get Workspace Details

```bash
WORKSPACE_ID="workspace-id-from-list"

curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/v1/workspaces/$WORKSPACE_ID
```

### Update Workspace

```bash
curl -X PATCH http://localhost:8000/api/v1/workspaces/$WORKSPACE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "description": "Updated description"
  }'
```

### Delete Workspace

```bash
curl -X DELETE http://localhost:8000/api/v1/workspaces/$WORKSPACE_ID \
  -H "Authorization: Bearer $TOKEN"
```

## API Documentation

### Interactive API Docs

Visit http://localhost:8000/docs to see all endpoints with:
- Request/response examples
- Parameter descriptions
- Try-it-out functionality

## Debugging

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Database Queries

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d cloud_os

# List users
SELECT * FROM users;

# List workspaces
SELECT * FROM workspaces;

# List refresh tokens
SELECT * FROM refresh_tokens;
```

### API Troubleshooting

| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Check token is in Authorization header as "Bearer TOKEN" |
| 403 Forbidden | Check you own the resource (user isolation) |
| 404 Not Found | Check resource ID is correct |
| 500 Internal Server | Check backend logs with `docker-compose logs backend` |
| CORS Error | Frontend and backend URLs must match .env settings |

## Environment Variables Reference

```bash
# Server
ENVIRONMENT=development          # development or production
DEBUG=true                       # Enable debug mode
API_HOST=0.0.0.0               # Backend listen address
API_PORT=8000                   # Backend listen port
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
DATABASE_POOL_SIZE=20           # Connection pool size
DATABASE_POOL_TIMEOUT=30        # Connection timeout (seconds)

# Redis
REDIS_URL=redis://redis:6379
REDIS_CACHE_TTL=3600           # Cache time-to-live (seconds)

# S3 Storage
MINIO_ENDPOINT=minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_USE_SSL=false
CHECKPOINT_BUCKET=cloud-os-checkpoints
CHECKPOINT_RETENTION_DAYS=30

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15       # Access token expiry
REFRESH_TOKEN_EXPIRATION_DAYS=30 # Refresh token expiry

# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/auth/github/callback

# Providers
ENABLED_PROVIDERS=local_docker
RUNPOD_API_KEY=                 # Optional - for RunPod integration
VASTAI_API_KEY=                 # Optional - for Vast.ai integration

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=                 # Optional - for AI assistant
DEFAULT_LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.3

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=                      # Your email
SMTP_PASSWORD=                  # App password
SMTP_FROM_EMAIL=noreply@cloud-os.example.com

# Monitoring
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL
SENTRY_DSN=                     # Optional - for error tracking

# Features
ENABLE_WORKFLOW_ENGINE=true
ENABLE_AI_ASSISTANT=true
ENABLE_COLLABORATION=false
ENABLE_EDGE_AGENTS=false
```

## Next Steps

1. **Test the OAuth flow** using the steps above
2. **Create workspaces** to verify CRUD operations
3. **Check API documentation** at http://localhost:8000/docs
4. **Review test file** at `src/backend/tests/test_auth_workspace.py`
5. **Run tests** with `make test`

## Common Issues & Fixes

### GitHub OAuth Fails

**Error**: "Failed to authenticate"

**Fix**:
1. Verify Client ID and Secret are correct in .env
2. Check callback URL matches exactly: `http://localhost:8000/api/v1/auth/github/callback`
3. Restart backend: `docker-compose restart backend`

### Token Expired

**Error**: 401 Unauthorized after 15 minutes

**Expected**: Access tokens expire. Refresh automatically via refresh token (browser handles via cookie)

### Workspace Not Found After Creation

**Fix**: Check you're using the returned workspace ID from creation response

### CORS Errors

**Error**: "Cross-Origin Request Blocked"

**Fix**:
1. Check FRONTEND_URL and BACKEND_URL in .env match your browser URLs
2. Restart backend to apply env changes
3. Check browser console for actual error

## Production Setup

### Security Checklist

- [ ] Change all passwords in .env
- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure HTTPS/SSL certificates
- [ ] Set DEBUG=false
- [ ] Enable SENTRY_DSN for error tracking
- [ ] Configure SMTP for email notifications
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Regular security updates

### Environment Differences

| Setting | Development | Production |
|---------|-------------|-----------|
| DEBUG | true | false |
| ENVIRONMENT | development | production |
| MINIO_USE_SSL | false | true |
| SECURE cookies | false | true |
| CORS | * | specific origins |
| LOG_LEVEL | DEBUG | WARNING |

---

**Ready to test? Start at Step 1!** 🚀
