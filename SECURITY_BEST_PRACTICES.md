# Security Best Practices

This document outlines security best practices implemented in XTeam and recommendations for secure deployment.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Token Management](#token-management)
3. [Rate Limiting](#rate-limiting)
4. [Input Validation](#input-validation)
5. [Secure Communication](#secure-communication)
6. [Database Security](#database-security)
7. [Secrets Management](#secrets-management)
8. [Security Headers](#security-headers)
9. [Monitoring & Logging](#monitoring--logging)
10. [Incident Response](#incident-response)

## Authentication & Authorization

### JWT Token-Based Authentication

XTeam uses JWT (JSON Web Tokens) for stateless authentication.

#### Access Tokens

- **Purpose**: Short-lived tokens for API authentication
- **Default Expiration**: 30 minutes
- **Claims**: `sub` (user ID), `exp` (expiration)
- **Algorithm**: HS256 (HMAC with SHA-256)

#### Refresh Tokens

- **Purpose**: Long-lived tokens for obtaining new access tokens
- **Default Expiration**: 7 days
- **Usage**: Exchange for new access token when current expires

### Token Revocation

Implements Redis-based token blacklist for immediate token revocation:

```python
# Logout endpoint revokes current token
POST /api/v1/auth/logout
Authorization: Bearer <token>

# Token is added to blacklist for remaining lifetime
# Subsequent requests with revoked token will be rejected
```

### WebSocket Authentication

WebSocket connections require JWT authentication:

```javascript
// Connect with token in query parameter
const ws = new WebSocket(`wss://api.example.com/ws?token=${accessToken}`);

// Connection is rejected if:
// - Token is missing
// - Token is invalid or expired
// - Token is revoked
// - User is inactive
```

### Best Practices

1. **Use Strong Secret Keys**
   ```bash
   # Generate secure secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Rotate Secret Keys Periodically**
   - Plan for key rotation strategy
   - Support multiple valid keys during rotation

3. **Short Access Token Lifetime**
   - Default: 30 minutes
   - For high-security: 5-15 minutes
   - Use refresh tokens for long sessions

4. **Secure Token Storage**
   - Never store tokens in localStorage (XSS vulnerable)
   - Use httpOnly cookies or sessionStorage
   - Clear tokens on logout

5. **Implement Token Refresh Flow**
   ```javascript
   // Automatically refresh tokens before expiration
   async function refreshToken() {
     const response = await fetch('/api/v1/auth/refresh', {
       method: 'POST',
       body: JSON.stringify({ refresh_token: currentRefreshToken })
     });
     const { access_token } = await response.json();
     return access_token;
   }
   ```

## Token Management

### Token Blacklist

Redis-based token revocation system:

#### Features

- **Individual Token Revocation**: Revoke specific tokens (logout)
- **User-Level Revocation**: Revoke all tokens for a user (password change, security breach)
- **Automatic Cleanup**: Expired tokens automatically removed by Redis TTL

#### Usage

```python
from app.core.token_blacklist import token_blacklist

# Revoke specific token
await token_blacklist.revoke_token(token, expires_in_seconds=3600)

# Revoke all user tokens
await token_blacklist.revoke_all_user_tokens(user_id)

# Check if token is revoked
is_revoked = await token_blacklist.is_token_revoked(token)
```

### Best Practices

1. **Revoke Tokens on Password Change**
   ```python
   # After password change
   await token_blacklist.revoke_all_user_tokens(user.id)
   ```

2. **Revoke Tokens on Security Events**
   - Suspicious login activity
   - Account compromise detected
   - User requests security review

3. **Monitor Token Operations**
   - Track revocation rate
   - Alert on unusual patterns
   - Log all security-related token operations

## Rate Limiting

Token bucket algorithm limits requests per client IP.

### Configuration

```python
# In .env or settings
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### How It Works

1. Each client IP gets a token bucket
2. Bucket capacity = requests per minute
3. Tokens refill at constant rate
4. Request consumes 1 token
5. Request rejected if no tokens available

### Exempt Endpoints

Health check endpoints are exempt from rate limiting:
- `/health`
- `/healthz`
- `/readyz`

### Custom Rate Limits

For different rate limits on specific endpoints:

```python
from fastapi import Depends
from app.api.deps import check_rate_limit

@router.post("/expensive-operation")
async def expensive_operation(
    user: User = Depends(check_rate_limit)  # Per-user rate limit
):
    ...
```

### Best Practices

1. **Different Limits for Different Endpoints**
   - Auth endpoints: 5 requests/minute
   - Read operations: 60 requests/minute
   - Write operations: 30 requests/minute
   - Expensive operations: 5 requests/minute

2. **Return Informative Headers**
   ```
   X-RateLimit-Limit: 60
   X-RateLimit-Remaining: 45
   Retry-After: 30
   ```

3. **Monitor Rate Limit Hits**
   - Track clients hitting limits
   - Detect potential abuse
   - Adjust limits based on usage patterns

## Input Validation

### Pydantic Models

All input validated using Pydantic models:

```python
from pydantic import BaseModel, EmailStr, constr, Field

class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    username: constr(min_length=3, max_length=50)  # Length constraints
    password: constr(min_length=8)  # Minimum password length
    full_name: str = Field(..., max_length=100)
```

### SQL Injection Prevention

Using SQLAlchemy ORM with parameterized queries:

```python
# Safe - parameterized query
stmt = select(User).where(User.email == user_input)
result = await db.execute(stmt)

# Never do this - SQL injection vulnerable
query = f"SELECT * FROM users WHERE email = '{user_input}'"
```

### File Upload Security

```python
# Validate file types
ALLOWED_EXTENSIONS = {'.py', '.js', '.ts', '.json', '.md'}

# Validate file size
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB

# Sanitize filenames
import os
from werkzeug.utils import secure_filename

safe_filename = secure_filename(uploaded_file.filename)
```

## Secure Communication

### HTTPS/TLS

Always use HTTPS in production:

```python
# In production config
SSL_CERTFILE=/path/to/cert.pem
SSL_KEYFILE=/path/to/key.pem
```

### CORS Configuration

Restrict CORS origins in production:

```python
# Development
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Production
CORS_ORIGINS=https://app.example.com,https://www.example.com
```

### Trusted Hosts

Configure trusted hosts in production:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["example.com", "*.example.com"]
)
```

## Database Security

### Connection Security

```python
# Use SSL for database connections
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

### Password Hashing

Using bcrypt with appropriate cost factor:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor (higher = more secure, slower)
)
```

### Sensitive Data

1. **Never log sensitive data**
   ```python
   # Bad
   logger.info(f"User password: {password}")
   
   # Good
   logger.info("User authentication successful")
   ```

2. **Encrypt sensitive fields**
   ```python
   # Use database-level encryption for PII
   # Or application-level encryption
   from cryptography.fernet import Fernet
   ```

3. **Use parameterized queries**
   - Always use ORM or prepared statements
   - Never concatenate user input into queries

## Secrets Management

### Environment Variables

Never commit secrets to version control:

```bash
# .gitignore
.env
.env.local
.env.*.local
*.pem
*.key
secrets/
```

### Secret Storage Options

1. **AWS Secrets Manager**
   ```python
   import boto3
   
   client = boto3.client('secretsmanager')
   secret = client.get_secret_value(SecretId='prod/xteam/db')
   ```

2. **Azure Key Vault**
   ```python
   from azure.keyvault.secrets import SecretClient
   
   client = SecretClient(vault_url, credential)
   secret = client.get_secret("database-password")
   ```

3. **HashiCorp Vault**
   ```python
   import hvac
   
   client = hvac.Client(url='https://vault.example.com')
   secret = client.secrets.kv.v2.read_secret_version(path='xteam/db')
   ```

### API Keys

1. **Rotate regularly** - Change API keys every 90 days
2. **Use separate keys per environment** - dev, staging, production
3. **Limit key scope** - Use minimum required permissions
4. **Monitor key usage** - Alert on unusual patterns

## Security Headers

Implement security headers:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
```

## Monitoring & Logging

### Security Event Logging

Log all security-relevant events:

```python
# Authentication failures
logger.warning(
    "Authentication failed",
    extra={
        "email": email,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }
)

# Token revocation
logger.info(
    "Token revoked",
    extra={
        "user_id": user_id,
        "reason": "user_logout"
    }
)

# Rate limit exceeded
logger.warning(
    "Rate limit exceeded",
    extra={
        "client_ip": client_ip,
        "endpoint": request.url.path
    }
)
```

### Security Alerts

Set up alerts for:

- Multiple failed login attempts
- Unusual number of token revocations
- Rate limit violations
- Database connection from unusual IP
- Privilege escalation attempts

## Incident Response

### Security Incident Checklist

1. **Detect & Assess**
   - Identify the incident scope
   - Determine affected users/systems
   - Assess potential data exposure

2. **Contain**
   - Revoke compromised tokens
   - Disable affected accounts
   - Block malicious IPs
   - Isolate affected systems

3. **Eradicate**
   - Remove malicious code/access
   - Patch vulnerabilities
   - Update credentials

4. **Recover**
   - Restore from backups if needed
   - Verify system integrity
   - Gradually restore services

5. **Post-Incident**
   - Document incident
   - Update security measures
   - Notify affected users
   - Review and improve processes

### Quick Response Commands

```bash
# Revoke all tokens for a user
curl -X POST http://localhost:8000/api/v1/admin/revoke-user-tokens \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"user_id": "compromised-user-id"}'

# Block IP address (at firewall/load balancer level)
# AWS WAF example
aws wafv2 update-ip-set --name blocked-ips --id xxx --addresses 1.2.3.4/32

# Check recent authentication failures
grep "Authentication failed" /var/log/xteam/backend.log | tail -100
```

## Security Checklist

### Pre-Deployment

- [ ] All secrets are stored securely (not in code)
- [ ] Strong secret key configured (32+ characters)
- [ ] HTTPS/TLS enabled
- [ ] CORS origins restricted to production domains
- [ ] Rate limiting enabled
- [ ] Token expiration times appropriate
- [ ] Database connections use SSL
- [ ] Security headers configured
- [ ] Input validation on all endpoints
- [ ] Dependencies scanned for vulnerabilities

### Post-Deployment

- [ ] Monitor authentication failures
- [ ] Monitor rate limit violations
- [ ] Set up security alerts
- [ ] Test token revocation
- [ ] Verify health check endpoints
- [ ] Review access logs regularly
- [ ] Schedule security audits
- [ ] Keep dependencies updated

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
