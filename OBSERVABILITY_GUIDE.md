# Observability & Monitoring Guide

This guide covers the observability features implemented in XTeam and how to use them effectively.

## Overview

XTeam implements several observability features to help monitor and debug the application in production:

1. **Structured JSON Logging** - All logs are output in JSON format for easy parsing
2. **Request ID Tracking** - Each request gets a unique ID for distributed tracing
3. **Health Check Endpoints** - Multiple endpoints for different health check scenarios
4. **Rate Limiting Metrics** - Track rate limit usage per client
5. **Token Blacklist Monitoring** - Monitor token revocation operations

## Health Check Endpoints

### `/healthz` - Liveness Probe

Lightweight endpoint that checks if the application is running. Returns 200 OK if the service is alive.

**Use case**: Kubernetes liveness probes, basic uptime monitoring

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-01T12:34:56.789Z"
}
```

**Configuration**:
```yaml
# Kubernetes example
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### `/readyz` - Readiness Probe

Comprehensive endpoint that checks all critical dependencies (database, Redis). Returns 200 OK only if all dependencies are healthy.

**Use case**: Kubernetes readiness probes, load balancer health checks

**Response** (healthy):
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "checks": {
    "database": "ok",
    "redis": "ok"
  },
  "duration_ms": 45.23
}
```

**Response** (unhealthy - 503):
```json
{
  "status": "unhealthy",
  "version": "0.1.0",
  "environment": "production",
  "checks": {
    "database": "error: connection refused",
    "redis": "ok"
  },
  "duration_ms": 5001.12
}
```

**Configuration**:
```yaml
# Kubernetes example
readinessProbe:
  httpGet:
    path: /readyz
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 10
  failureThreshold: 3
```

### `/health` - Legacy Endpoint

Simple health check for backwards compatibility.

## Structured Logging

All logs are output in JSON format with consistent fields.

### Log Format

```json
{
  "timestamp": "2025-11-01T12:34:56.789Z",
  "logger": "app.main",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "path": "/api/v1/projects",
  "status_code": 200,
  "duration_ms": 123.45
}
```

### Key Log Fields

- **timestamp**: ISO 8601 timestamp
- **logger**: Module that generated the log
- **level**: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **message**: Human-readable message
- **request_id**: Unique identifier for the request (for tracing)
- **method**: HTTP method
- **path**: Request path
- **status_code**: HTTP response status code
- **duration_ms**: Request duration in milliseconds

### Configuration

Logging is automatically configured on application startup. To customize:

```python
# In app/middleware/logging.py
from pythonjsonlogger import jsonlogger

# Customize log format
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={"asctime": "timestamp"}
)
```

### Log Aggregation

Structured JSON logs can be easily parsed by log aggregation systems:

#### ELK Stack (Elasticsearch, Logstash, Kibana)

```conf
# Logstash configuration
input {
  file {
    path => "/var/log/xteam/*.log"
    codec => "json"
  }
}

filter {
  json {
    source => "message"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "xteam-%{+YYYY.MM.dd}"
  }
}
```

#### CloudWatch Logs

```json
{
  "log_group_name": "/aws/ecs/xteam-backend",
  "log_stream_name": "backend/{container_id}",
  "json_format": true
}
```

#### Datadog

```yaml
logs:
  - type: docker
    service: xteam-backend
    source: python
    sourcecategory: sourcecode
    log_processing_rules:
      - type: auto_multi_line_detection
        name: json_log_lines
```

## Request ID Tracking

Every request gets a unique request ID for distributed tracing.

### How It Works

1. Client sends request with optional `X-Request-ID` header
2. If not provided, middleware generates a UUID
3. Request ID is included in all logs for that request
4. Request ID is returned in `X-Request-ID` response header

### Usage

#### Client-side

```javascript
// Provide your own request ID
fetch('/api/v1/projects', {
  headers: {
    'X-Request-ID': 'my-custom-request-id-123'
  }
});

// Or let the server generate one
const response = await fetch('/api/v1/projects');
const requestId = response.headers.get('X-Request-ID');
console.log('Request ID:', requestId);
```

#### Server-side

```python
from app.middleware.request_id import get_request_id

# In any handler
def my_handler():
    request_id = get_request_id()
    logger.info(f"Processing request {request_id}")
```

### Tracing Across Services

Use request IDs to trace requests across multiple services:

1. Frontend includes request ID in all API calls
2. Backend includes request ID in logs and passes to other services
3. Search logs by request ID to see the complete flow

## Rate Limiting

Token bucket algorithm with per-client tracking.

### Configuration

```python
# In app/core/config.py
class Settings:
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
```

### Response Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
```

When rate limit is exceeded (429 response):

```
Retry-After: 30
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
```

### Monitoring

Track rate limit metrics:

- Number of rate limited requests per minute
- Clients hitting rate limits frequently
- Rate limit remaining average across all clients

### Prometheus Metrics Example

```python
# Add to your monitoring setup
from prometheus_client import Counter, Histogram

rate_limit_exceeded = Counter(
    'rate_limit_exceeded_total',
    'Total number of rate limit exceeded responses',
    ['client_ip']
)

rate_limit_remaining = Histogram(
    'rate_limit_remaining',
    'Rate limit tokens remaining',
    ['client_ip']
)
```

## Monitoring Best Practices

### Key Metrics to Monitor

1. **Availability**
   - `/healthz` uptime (should be 99.9%+)
   - `/readyz` success rate
   
2. **Performance**
   - Request duration (p50, p95, p99)
   - Database query duration
   - Redis operation duration
   
3. **Errors**
   - 5xx error rate (should be < 0.1%)
   - 4xx error rate by endpoint
   - Failed health checks
   
4. **Security**
   - Rate limit exceeded count
   - Authentication failures
   - Token revocations
   
5. **Resources**
   - CPU usage
   - Memory usage
   - Database connections
   - Redis memory usage

### Alert Thresholds

Recommended alert thresholds:

```yaml
# Example Prometheus alerting rules
groups:
  - name: xteam_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        annotations:
          summary: "High 5xx error rate"
          
      - alert: HealthCheckFailing
        expr: up{job="xteam-backend"} == 0
        for: 2m
        annotations:
          summary: "Backend health check failing"
          
      - alert: HighLatency
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 10m
        annotations:
          summary: "95th percentile latency above 2s"
          
      - alert: DatabaseConnectionIssues
        expr: readyz_check{check="database"} == 0
        for: 1m
        annotations:
          summary: "Database connection issues detected"
```

### Dashboard Setup

Create dashboards for:

1. **Overview Dashboard**
   - Request rate
   - Error rate
   - Average latency
   - Health check status
   
2. **Performance Dashboard**
   - Request duration by endpoint
   - Database query duration
   - Cache hit rate
   
3. **Security Dashboard**
   - Rate limit violations
   - Authentication failures
   - Token operations
   
4. **Infrastructure Dashboard**
   - CPU/Memory usage
   - Network I/O
   - Disk usage

## Troubleshooting

### Finding Logs for a Specific Request

```bash
# Using request ID
grep "550e8400-e29b-41d4-a716-446655440000" /var/log/xteam/backend.log

# Using jq for JSON parsing
cat /var/log/xteam/backend.log | jq 'select(.request_id == "550e8400...")'

# In Elasticsearch
GET /xteam-*/_search
{
  "query": {
    "match": {
      "request_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  }
}
```

### Debugging Health Check Failures

```bash
# Check /readyz response
curl -v http://localhost:8000/readyz

# Check individual dependencies
curl http://localhost:8000/readyz | jq '.checks'

# Check logs for errors
cat /var/log/xteam/backend.log | jq 'select(.message | contains("health check"))'
```

### Monitoring Rate Limit Usage

```bash
# Check current rate limit headers
curl -I http://localhost:8000/api/v1/projects

# Monitor rate limit exceeded errors
cat /var/log/xteam/backend.log | jq 'select(.status_code == 429)'
```

## Further Reading

- [The Twelve-Factor App - Logs](https://12factor.net/logs)
- [Google SRE Book - Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Structured Logging with Python](https://github.com/madzak/python-json-logger)
