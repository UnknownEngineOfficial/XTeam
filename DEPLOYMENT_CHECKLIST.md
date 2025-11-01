# Production Deployment Checklist

Use this checklist before deploying XTeam to production.

## Security

- [ ] Change `SECRET_KEY` to a strong, random value (32+ characters)
- [ ] Use strong database password (`POSTGRES_PASSWORD`)
- [ ] Enable HTTPS/SSL (`ssl_certfile`, `ssl_keyfile`)
- [ ] Restrict CORS origins to your actual domains
- [ ] Set `DEBUG=false` in production
- [ ] Review and restrict `CORS_ALLOW_METHODS` and `CORS_ALLOW_HEADERS`
- [ ] Enable rate limiting (`rate_limit_enabled=true`)
- [ ] Configure rate limit per minute (`rate_limit_requests_per_minute`)
- [ ] Enable token blacklist with Redis for logout/revocation
- [ ] Store secrets in secure secret management (AWS Secrets Manager, Azure Key Vault, etc.)
- [ ] Ensure API keys (OpenAI, etc.) are never committed to git
- [ ] Review and update `TrustedHostMiddleware` allowed hosts
- [ ] Enable and configure Sentry for error tracking (`SENTRY_DSN`)
- [ ] Review WebSocket authentication requirements
- [ ] Reduce access token expiration time for enhanced security (default: 30 min)

## Database

- [ ] Use PostgreSQL in production (not SQLite)
- [ ] Set up database backups (automated daily backups)
- [ ] Configure connection pooling appropriately (`database_pool_size`, `database_max_overflow`)
- [ ] Run all Alembic migrations: `alembic upgrade head`
- [ ] Test database failover/recovery procedures
- [ ] Set up read replicas if needed for scaling
- [ ] Enable database encryption at rest
- [ ] Configure database access restrictions (firewall rules)

## Redis

- [ ] Use Redis with persistence enabled
- [ ] Set up Redis backups
- [ ] Configure Redis password protection
- [ ] Use separate Redis instances/databases for different purposes (cache, queue, sessions, token blacklist)
- [ ] Consider Redis Cluster for high availability
- [ ] Configure Redis memory limits and eviction policies
- [ ] Monitor Redis memory usage and connection count

## Infrastructure

- [ ] Use a production-grade container orchestration (Kubernetes, ECS, etc.)
- [ ] Set up load balancing
- [ ] Configure auto-scaling based on metrics
- [ ] Set up health checks (`/healthz`) and readiness probes (`/readyz`)
- [ ] Configure resource limits (CPU, memory) for containers
- [ ] Set up monitoring and alerting (Prometheus, Grafana, CloudWatch, etc.)
- [ ] Configure structured JSON log aggregation (ELK stack, CloudWatch Logs, etc.)
- [ ] Set up CDN for frontend assets (CloudFront, Cloudflare, etc.)
- [ ] Configure DNS with proper TTL values
- [ ] Enable distributed tracing with request IDs

## Application Configuration

- [ ] Set `ENVIRONMENT=production`
- [ ] Disable API docs in production (`docs_url=None`, `redoc_url=None`)
- [ ] Configure appropriate log levels (`LOG_LEVEL=WARNING` or `ERROR`)
- [ ] Set reasonable timeout values for external API calls
- [ ] Configure retry policies for external services
- [ ] Set up proper file upload limits (`max_upload_size_mb`)
- [ ] Configure workspace cleanup schedules
- [ ] Set appropriate token expiration times

## Celery/Worker Configuration

- [ ] Set up multiple worker instances for redundancy
- [ ] Configure worker concurrency based on workload
- [ ] Set up Celery Beat for scheduled tasks
- [ ] Configure task retry policies
- [ ] Set appropriate task time limits
- [ ] Monitor worker health and queue lengths
- [ ] Set up dead letter queue for failed tasks

## CI/CD

- [ ] Set up automated testing in CI pipeline with coverage threshold
- [ ] Configure automated security scanning (pip-audit, Trivy, Snyk, Dependabot, etc.)
- [ ] Set up automated Docker image building
- [ ] Configure image vulnerability scanning with Trivy
- [ ] Run Alembic migration checks in CI
- [ ] Implement blue-green or canary deployments
- [ ] Set up staging environment with migration gates
- [ ] Set up production environment with manual approval
- [ ] Set up rollback procedures
- [ ] Test deployment pipeline in staging environment
- [ ] Configure smoke tests for post-deployment validation

## Monitoring & Observability

- [ ] Set up application performance monitoring (APM)
- [ ] Configure error tracking (Sentry, Rollbar, etc.)
- [ ] Set up uptime monitoring (Pingdom, UptimeRobot, etc.)
- [ ] Configure alerting for critical metrics
- [ ] Set up dashboard for key metrics
- [ ] Enable distributed tracing with request IDs
- [ ] Monitor API rate limits and quotas
- [ ] Track and alert on high error rates
- [ ] Monitor `/healthz` and `/readyz` endpoint responses
- [ ] Set up log parsing for structured JSON logs
- [ ] Configure alerts for 5xx errors and high latency
- [ ] Monitor Redis connection health and memory usage
- [ ] Track token blacklist size and operations

## Performance

- [ ] Enable and test caching strategies
- [ ] Optimize database queries (add indexes, analyze slow queries)
- [ ] Set up database query monitoring
- [ ] Enable response compression (gzip)
- [ ] Optimize Docker image sizes
- [ ] Configure appropriate worker counts
- [ ] Test under expected load (load testing)
- [ ] Set up CDN for static assets

## Backup & Recovery

- [ ] Set up automated database backups
- [ ] Test database restore procedures
- [ ] Back up uploaded files and workspaces
- [ ] Document disaster recovery procedures
- [ ] Set up point-in-time recovery for database
- [ ] Store backups in different region/availability zone
- [ ] Test full system recovery from backups

## Compliance & Legal

- [ ] Review data privacy requirements (GDPR, CCPA, etc.)
- [ ] Set up data retention policies
- [ ] Configure audit logging for sensitive operations
- [ ] Ensure proper data encryption (at rest and in transit)
- [ ] Document data processing agreements
- [ ] Set up user data export functionality
- [ ] Implement data deletion procedures

## Documentation

- [ ] Update README with production setup instructions
- [ ] Document environment variables and their purposes
- [ ] Create runbooks for common operations
- [ ] Document incident response procedures
- [ ] Create architecture diagrams
- [ ] Document API rate limits and quotas
- [ ] Create user documentation

## Testing

- [ ] Run full test suite and ensure all tests pass
- [ ] Perform security testing (OWASP Top 10)
- [ ] Conduct load testing
- [ ] Test database migrations on production-like data
- [ ] Test backup and restore procedures
- [ ] Test failover scenarios
- [ ] Perform user acceptance testing (UAT)
- [ ] Test WebSocket connections under load

## Pre-Deployment

- [ ] Create production environment in cloud provider
- [ ] Set up all required environment variables
- [ ] Configure DNS records
- [ ] Set up SSL certificates
- [ ] Test entire deployment process in staging
- [ ] Prepare rollback plan
- [ ] Schedule maintenance window if needed
- [ ] Notify users of deployment (if applicable)

## Post-Deployment

- [ ] Verify all services are healthy
- [ ] Check application logs for errors
- [ ] Test critical user flows
- [ ] Monitor error rates and performance metrics
- [ ] Verify database migrations completed
- [ ] Test WebSocket connections
- [ ] Verify scheduled tasks are running
- [ ] Check that monitoring and alerting are active
- [ ] Update documentation with any changes
- [ ] Announce successful deployment

## Ongoing Maintenance

- [ ] Set up regular dependency updates
- [ ] Schedule regular security audits
- [ ] Review and optimize database performance monthly
- [ ] Review logs and errors weekly
- [ ] Update documentation as needed
- [ ] Review and update monitoring alerts
- [ ] Perform regular disaster recovery drills
- [ ] Review and update scaling policies

## Cost Optimization

- [ ] Review cloud resource usage
- [ ] Set up cost alerts
- [ ] Optimize instance sizes based on actual usage
- [ ] Use reserved instances or savings plans
- [ ] Review and clean up unused resources
- [ ] Optimize database storage
- [ ] Review API usage and costs (OpenAI, etc.)

---

**Note**: This checklist should be reviewed and updated regularly. Not all items may apply to your specific deployment.

## Docker-Specific Considerations

### Migration Locks (Multi-Instance Deployments)

When deploying multiple backend instances, be aware that the startup script runs migrations on every container start. For production:

**Option 1: Init Container (Kubernetes)**
```yaml
initContainers:
- name: migrations
  image: your-backend-image
  command: ["alembic", "upgrade", "head"]
  env: [... same env as main container ...]
```

**Option 2: Separate Migration Job**
Run migrations as a separate one-time job before rolling out new containers.

**Option 3: Migration Locks**
Alembic supports advisory locks in PostgreSQL to prevent concurrent migrations. This is handled automatically by PostgreSQL's advisory locks.

