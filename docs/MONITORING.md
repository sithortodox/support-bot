# Monitoring Configuration

## Prometheus Metrics

Available at: `GET /metrics`

### Bot Metrics
- `support_bot_messages_total` - Total messages by type and sender
- `support_bot_tickets_total` - Total tickets by status, priority, category
- `support_bot_tickets_open` - Currently open tickets gauge
- `support_bot_user_ratings_total` - User ratings counter
- `support_bot_user_blocks` - Blocked users gauge

### AI Metrics
- `support_bot_ai_requests_total` - AI requests by model and FAQ usage
- `support_bot_ai_tokens_total` - Tokens by type (prompt/completion)
- `support_bot_ai_cost_total` - Estimated cost in USD
- `support_bot_ai_response_time_seconds` - AI response time histogram

### HTTP Metrics
- `support_bot_http_requests_total` - HTTP requests by method, endpoint, status
- `support_bot_http_request_time_seconds` - HTTP request time histogram

### Database Metrics
- `support_bot_db_connections` - Database connections gauge

## Health Checks

### `/health` - Full Health Check
Checks:
- Database connection
- Redis connection
- OpenAI configuration
- System info

Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "openai": "configured"
  }
}
```

### `/ready` - Readiness Check
Kubernetes readiness probe.
Returns 200 if service is ready to accept traffic.

### `/live` - Liveness Check
Kubernetes liveness probe.
Returns 200 if service is alive.

## Logging

### Log Files
- `logs/support_bot.log` - All logs (rotating, 10MB, 5 backups)
- `logs/errors.log` - Errors only (rotating, 10MB, 5 backups)
- `logs/ai.log` - AI-specific logs (rotating, 10MB, 5 backups)

### Log Format
```
%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s
```

### Log Levels
- **DEBUG** - Detailed diagnostic information
- **INFO** - General operational information
- **WARNING** - Warning conditions (slow requests, high usage)
- **ERROR** - Error conditions
- **CRITICAL** - Critical conditions (service failures)

### Slow Request Detection
Requests slower than 1.0 seconds are logged as warnings.

## Alembic Migrations

### Setup
```bash
# Initialize
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Configuration
- Config: `alembic.ini`
- Migrations: `alembic/versions/`
- Database URL from `DATABASE_URL` env var

## Alerting

### Thresholds
- Response time: > 5 seconds
- Error rate: > 10%
- Open tickets: > 100
- AI cost daily: > $10
- Negative sentiment: < 0.3

### Alert Severities
- **INFO** - Informational alerts
- **WARNING** - Warning conditions
- **CRITICAL** - Critical conditions

### Webhook Notifications
Configure `webhook_url` in alerter config for external notifications.

## Grafana Dashboard

### Recommended Panels
1. **Request Rate** - `rate(support_bot_http_requests_total[5m])`
2. **Error Rate** - `rate(support_bot_http_requests_total{status=~"5.."}[5m])`
3. **Response Time** - `histogram_quantile(0.95, support_bot_http_request_time_seconds_bucket)`
4. **Open Tickets** - `support_bot_tickets_open`
5. **AI Cost** - `increase(support_bot_ai_cost_total[24h])`
6. **User Satisfaction** - `support_bot_user_ratings_total{rating="positive"}`

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'support-bot'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Docker Compose Monitoring Stack

Add to `docker-compose.yml`:
```yaml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Best Practices

1. **Monitor regularly** - Check metrics dashboard daily
2. **Set up alerts** - Configure alerting for critical thresholds
3. **Review logs** - Check error logs regularly
4. **Optimize queries** - Monitor slow requests
5. **Track costs** - Monitor AI token usage and costs
6. **Backup database** - Regular backups before migrations
