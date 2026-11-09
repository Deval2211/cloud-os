# Deployment Guide

**Document**: Development, Staging, and Production Deployment
**Version**: 1.0
**Status**: Design Phase

## Local Development Setup

### Prerequisites

```bash
# Install Docker & Docker Compose
docker --version
docker-compose --version

# Python 3.11+
python3 --version

# Node.js 18+
node --version
```

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/cloud-os.git
cd cloud-os

# Copy environment file
cp .env.example .env

# Fill in environment variables
vim .env

# Build services
docker-compose build

# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed initial data
docker-compose exec backend python scripts/seed.py
```

### Docker Compose Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cloud_os
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/cloud_os
      REDIS_URL: redis://redis:6379
      MINIO_ENDPOINT: minio:9000
      DEBUG: "true"
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./src/backend:/app

  celery-worker:
    build:
      context: ./src/backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/cloud_os
      REDIS_URL: redis://redis:6379
    depends_on:
      - redis
      - postgres
    command: celery -A tasks worker -l info
    volumes:
      - ./src/backend:/app

  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile.dev
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./src/frontend:/app
    command: npm run dev

  code-server:
    image: codercom/code-server:latest
    environment:
      PASSWORD: "password"
    ports:
      - "8080:8080"
    volumes:
      - code_server_data:/home/coder/project

volumes:
  postgres_data:
  redis_data:
  minio_data:
  code_server_data:
```

### Development Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery-worker

# Run tests
docker-compose exec backend pytest tests/

# Lint
docker-compose exec backend flake8 .
docker-compose exec frontend npm run lint

# Format
docker-compose exec backend black .
docker-compose exec frontend npm run format

# Database migrations
docker-compose exec backend alembic revision --autogenerate -m "message"
docker-compose exec backend alembic upgrade head

# Shell access
docker-compose exec backend python
docker-compose exec postgres psql -U postgres -d cloud_os
```

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
kubectl version --client

# Access to Kubernetes cluster
export KUBECONFIG=~/.kube/config
kubectl config use-context production
```

### Kubernetes Manifests

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cloud-os

---
# kubernetes/postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: cloud-os
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        environment:
        - name: POSTGRES_DB
          value: cloud_os
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: postgres-pvc

---
# kubernetes/postgres-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: cloud-os
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432

---
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: cloud-os
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: cloud-os-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: redis-config
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# kubernetes/backend-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: cloud-os
spec:
  selector:
    app: backend
  type: ClusterIP
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000

---
# kubernetes/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cloud-os
  namespace: cloud-os
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.cloud-os.example.com
    secretName: cloud-os-tls
  rules:
  - host: api.cloud-os.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

### Deployment Commands

```bash
# Apply manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/postgres-deployment.yaml
kubectl apply -f kubernetes/redis-deployment.yaml
kubectl apply -f kubernetes/backend-deployment.yaml
kubectl apply -f kubernetes/frontend-deployment.yaml
kubectl apply -f kubernetes/ingress.yaml

# Check status
kubectl get pods -n cloud-os
kubectl get svc -n cloud-os
kubectl get ingress -n cloud-os

# View logs
kubectl logs -n cloud-os deployment/backend

# Scale deployment
kubectl scale deployment backend -n cloud-os --replicas=5

# Update image
kubectl set image deployment/backend backend=cloud-os-backend:v1.1.0 -n cloud-os

# Rollout status
kubectl rollout status deployment/backend -n cloud-os

# Rollback
kubectl rollout undo deployment/backend -n cloud-os
```

## Secrets Management

### Development

```bash
# Create .env file
cp .env.example .env
# Edit .env with local values
```

### Kubernetes

```bash
# Create secret
kubectl create secret generic postgres-credentials \
  --from-literal=username=postgres \
  --from-literal=password=secret \
  -n cloud-os

# Create TLS secret
kubectl create secret tls cloud-os-tls \
  --cert=certs/server.crt \
  --key=certs/server.key \
  -n cloud-os

# View secrets
kubectl get secrets -n cloud-os
kubectl describe secret postgres-credentials -n cloud-os
```

## Monitoring & Logging

### Prometheus Setup

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### Grafana Dashboards

- Backend metrics (request latency, error rate)
- GPU metrics (utilization, temperature, VRAM)
- Database metrics (connection count, query time)
- Storage metrics (disk usage, I/O)

### Logging Stack (ELK)

```bash
# Start ELK
docker-compose -f docker-compose.elk.yml up -d

# Access Kibana
open http://localhost:5601
```

## Backup & Disaster Recovery

### Database Backup

```bash
# Daily backup
0 2 * * * pg_dump cloud_os | gzip | aws s3 cp - s3://cloud-os-backups/db/$(date +\%Y\%m\%d).sql.gz

# Restore
aws s3 cp s3://cloud-os-backups/db/YYYYMMDD.sql.gz - | gunzip | psql cloud_os
```

### S3 Backup Replication

```bash
# Enable S3 cross-region replication
aws s3api put-bucket-replication \
  --bucket cloud-os-checkpoints \
  --replication-configuration file://replication.json
```

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build images
        run: |
          docker build -t cloud-os-backend:latest ./src/backend
          docker build -t cloud-os-frontend:latest ./src/frontend
      - name: Push to registry
        run: |
          docker tag cloud-os-backend:latest registry.example.com/cloud-os-backend:latest
          docker push registry.example.com/cloud-os-backend:latest
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to K8s
        run: |
          kubectl set image deployment/backend backend=cloud-os-backend:latest -n cloud-os
          kubectl rollout status deployment/backend -n cloud-os
```

## Performance Tuning

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_sessions_user_workspace ON workspace_sessions(workspace_id, status);
CREATE INDEX idx_checkpoints_session_created ON checkpoints(session_id, created_at DESC);

-- Connection pooling
pgbouncer config:
[databases]
cloud_os = host=postgres port=5432 dbname=cloud_os

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

### Redis Optimization

```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Monitor
redis-cli MONITOR
redis-cli INFO stats
```

### Kubernetes Resource Optimization

```yaml
# HPA (Horizontal Pod Autoscaling)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Troubleshooting

### Common Issues

```bash
# Backend won't start
docker-compose logs backend

# Database connection error
docker-compose exec postgres psql -U postgres -d cloud_os -c "SELECT 1"

# Redis connection error
docker-compose exec redis redis-cli ping

# Out of disk space
docker system prune -a
docker volume prune
```

## Production Checklist

- [ ] SSL/TLS certificates configured
- [ ] Environment variables set correctly
- [ ] Database backups configured
- [ ] Monitoring and alerts set up
- [ ] Log aggregation working
- [ ] Secret management in place
- [ ] Rate limiting configured
- [ ] CORS properly restricted
- [ ] Database migrations tested
- [ ] Failover strategy documented
- [ ] On-call runbook created
- [ ] Disaster recovery tested

## Next Steps

- See [MVP Roadmap](MVP_ROADMAP.md)
- Review [Monitoring Guide](MONITORING.md)
