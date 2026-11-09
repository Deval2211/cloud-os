# Security Architecture

**Document**: Enterprise-Grade Security Design
**Version**: 1.0
**Status**: Design Phase

## Overview

Cloud OS implements security across multiple layers:
- **Network**: TLS 1.3 encryption, secure channels
- **Authentication**: OAuth2, JWT tokens, MFA-ready
- **Authorization**: RBAC with fine-grained permissions
- **Secrets**: Encrypted storage, key rotation
- **Multi-tenancy**: Complete isolation between users
- **Audit**: Complete audit trail of actions

## Authentication Architecture

### OAuth2 Login Flow

```
1. User clicks "Login with GitHub"
2. Frontend redirects to /api/v1/auth/github
3. Backend exchanges code for GitHub access token
4. Backend fetches user info from GitHub API
5. Backend creates/updates user in DB
6. Backend generates JWT (short-lived: 15 min)
7. Backend generates Refresh Token (long-lived: 30 days)
8. Backend sets HttpOnly cookie with Refresh Token
9. Backend returns JWT in response body
10. Frontend stores JWT in memory (not localStorage)
```

### JWT Structure

```python
# Backend
def generate_jwt(user: User) -> str:
    payload = {
        'sub': str(user.id),  # Subject (user ID)
        'email': user.email,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'type': 'access'
    }
    
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm='HS256'
    )

# Frontend middleware
function authMiddleware(req, res, next) {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ error: 'No token' });
    }
    
    try {
        const decoded = jwt.verify(token, PUBLIC_KEY);
        req.user = decoded;
        next();
    } catch (err) {
        return res.status(401).json({ error: 'Invalid token' });
    }
}
```

### Refresh Token Management

```python
# Database
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) UNIQUE NOT NULL,  -- SHA256
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,  -- NULL if valid
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

# When issuing new JWT
@app.post("/api/v1/auth/refresh")
async def refresh_token(request: Request):
    # Extract refresh token from HttpOnly cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401)
    
    # Verify token exists and hasn't expired
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    record = await db.refresh_tokens.find_one({
        'token_hash': token_hash,
        'expires_at': {'$gt': datetime.utcnow()},
        'revoked_at': None
    })
    
    if not record:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({'id': record['user_id']})
    
    # Generate NEW refresh token (rotation)
    new_refresh_token = secrets.token_urlsafe(32)
    new_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
    
    # Invalidate old token
    await db.refresh_tokens.update_one(
        {'id': record['id']},
        {'$set': {'revoked_at': datetime.utcnow()}}
    )
    
    # Save new token
    await db.refresh_tokens.insert_one({
        'user_id': user['id'],
        'token_hash': new_token_hash,
        'expires_at': datetime.utcnow() + timedelta(days=30),
        'ip_address': request.client.host,
        'user_agent': request.headers.get('user-agent')
    })
    
    # Generate new JWT
    new_jwt = generate_jwt(user)
    
    # Return new JWT + set new refresh token cookie
    return {
        'access_token': new_jwt,
        'token_type': 'bearer',
        'expires_in': 900  # 15 minutes
    }, response.set_cookie(
        'refresh_token',
        new_refresh_token,
        httponly=True,
        secure=True,
        samesite='Strict',
        max_age=2592000  # 30 days
    )
```

## Authorization (RBAC)

### Role-Based Access Control

```python
# Database
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 'user', 'admin', 'enterprise_admin'
    description TEXT,
    permissions JSONB
);

CREATE TABLE user_roles (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    role_id UUID NOT NULL REFERENCES roles(id),
    workspace_id UUID REFERENCES workspaces(id),  -- NULL = global role
    granted_at TIMESTAMP DEFAULT NOW()
);

# Middleware
@app.middleware("http")
async def rbac_middleware(request: Request, call_next):
    user = request.state.user
    resource = request.url.path
    action = request.method  # GET, POST, DELETE, etc.
    
    # Check permission
    has_permission = await check_permission(user, resource, action)
    
    if not has_permission:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await call_next(request)

# Permission checker
async def check_permission(user: User, resource: str, action: str) -> bool:
    # Get user's roles
    roles = await db.user_roles.find({
        'user_id': user.id
    }).to_list(None)
    
    # Check if any role has permission
    for role in roles:
        role_obj = await db.roles.find_one({'id': role['role_id']})
        
        if is_permitted(role_obj['permissions'], resource, action):
            return True
    
    return False
```

## Secret Management

### Provider Credentials Encryption

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

class SecretManager:
    """Encrypt/decrypt secrets"""
    
    async def encrypt_provider_credentials(
        self,
        user_id: str,
        provider: str,
        credentials: Dict[str, str]
    ) -> tuple[bytes, bytes, bytes]:
        """
        Encrypt credentials using AES-256-GCM.
        
        Returns:
            (encrypted_data, iv, salt)
        """
        
        # Derive encryption key from user ID + master key
        salt = os.urandom(16)
        key = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        ).derive((str(user_id) + MASTER_KEY).encode())
        
        # Encrypt credentials
        iv = os.urandom(12)
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv)
        )
        encryptor = cipher.encryptor()
        
        credentials_json = json.dumps(credentials).encode()
        encrypted = encryptor.update(credentials_json) + encryptor.finalize()
        
        # Return encrypted data + IV + salt
        return encrypted, iv, salt
    
    async def decrypt_provider_credentials(
        self,
        user_id: str,
        encrypted_data: bytes,
        iv: bytes,
        salt: bytes
    ) -> Dict[str, str]:
        """Decrypt stored credentials"""
        
        # Derive same key
        key = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        ).derive((str(user_id) + MASTER_KEY).encode())
        
        # Decrypt
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_data) + decryptor.finalize()
        
        return json.loads(decrypted.decode())

# Usage
secret_manager = SecretManager()

# Store credentials
encrypted, iv, salt = await secret_manager.encrypt_provider_credentials(
    user_id="user123",
    provider="runpod",
    credentials={"api_key": "secret-key"}
)

# Retrieve credentials
credentials = await secret_manager.decrypt_provider_credentials(
    user_id="user123",
    encrypted_data=encrypted,
    iv=iv,
    salt=salt
)
```

## Network Security

### TLS Configuration

```python
# main.py
import ssl

# Create SSL context
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain("certs/server.crt", "certs/server.key")
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3

# Run with HTTPS
uvicorn.run(
    app,
    host="0.0.0.0",
    port=443,
    ssl_context=ssl_context
)
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cloud-os.example.com",
        "https://www.cloud-os.example.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600
)
```

### CSRF Protection

```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/api/v1/workspaces")
async def create_workspace(
    request: Request,
    csrf_protect: CsrfProtect = Depends()
):
    await csrf_protect.validate_csrf(request)
    # ... create workspace
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, credentials: LoginSchema):
    # ... authenticate
```

## Multi-Tenancy Isolation

### Row-Level Security

```python
# PostgreSQL RLS policy
CREATE POLICY workspace_isolation ON workspaces
    FOR SELECT
    USING (user_id = current_user_id());

# In Python ORM
@db.session.before_execute
def add_user_filter(mapper, connection, target):
    """Automatically filter queries by user"""
    if hasattr(target, 'user_id'):
        target = target.filter(target.user_id == current_user.id)
```

### Session Isolation

```python
# Verify user owns session
async def get_session_for_user(user: User, session_id: str):
    session = await db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404)
    
    # Check ownership via workspace
    if session.workspace.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return session
```

## Audit Logging

```python
# Log all important actions
class AuditLogger:
    async def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict,
        ip_address: str,
        user_agent: str
    ):
        audit_record = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        
        db.session.add(audit_record)
        await db.session.commit()
        
        logger.info(f"Audit: {action} by {user_id} on {resource_type}:{resource_id}")

# Log every API action
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)
    
    if request.user and request.method in ['POST', 'PUT', 'DELETE']:
        await audit_logger.log_action(
            user_id=str(request.user.id),
            action=f"{request.method} {request.url.path}",
            resource_type=extract_resource_type(request.url.path),
            resource_id=extract_resource_id(request.url.path),
            details=await request.json() if request.method in ['POST', 'PUT'] else {},
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent', '')
        )
    
    return response
```

## Compliance & Privacy

### GDPR Support

```python
# User data export
@app.get("/api/v1/user/export")
async def export_user_data(user: User = Depends(get_current_user)):
    """Export all user data (GDPR right to access)"""
    
    data = {
        'user': user.dict(),
        'workspaces': [w.dict() for w in user.workspaces],
        'sessions': [s.dict() for s in user.sessions],
        'workflows': [w.dict() for w in user.workflows]
    }
    
    return FileResponse(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        filename='user-data.json'
    )

# User deletion
@app.post("/api/v1/user/delete")
async def delete_user(user: User = Depends(get_current_user)):
    """Delete all user data (GDPR right to be forgotten)"""
    
    # Soft delete user
    user.deleted_at = datetime.utcnow()
    
    # Delete associated data
    await db.workspaces.delete_many({'user_id': user.id})
    await db.sessions.delete_many({'user_id': user.id})
    await db.workflows.delete_many({'user_id': user.id})
    await db.credentials.delete_many({'user_id': user.id})
    
    db.session.add(user)
    await db.session.commit()
```

## Security Checklist

- [ ] HTTPS/TLS 1.3 enabled
- [ ] CORS restricted to known domains
- [ ] CSRF tokens on state-changing requests
- [ ] Rate limiting on sensitive endpoints
- [ ] Password reset tokens expire in 1 hour
- [ ] Secrets encrypted at rest
- [ ] Secrets never logged
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS protection (input sanitization)
- [ ] CSRF tokens validated
- [ ] Secrets rotated regularly
- [ ] Audit logs retained 1 year
- [ ] Audit logs immutable
- [ ] MFA support prepared
- [ ] Key rotation strategy documented

## Next Steps

- See [API Specifications](../api/API_SPECIFICATIONS.md)
- Review [Deployment Guide](../operations/DEPLOYMENT.md)
