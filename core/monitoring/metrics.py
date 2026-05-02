from prometheus_client import Counter, Histogram, Gauge, Info
import time

MESSAGES_TOTAL = Counter(
    'support_bot_messages_total',
    'Total messages processed',
    ['type', 'sender']
)

TICKETS_TOTAL = Counter(
    'support_bot_tickets_total',
    'Total tickets created',
    ['status', 'priority', 'category']
)

TICKETS_OPEN = Gauge(
    'support_bot_tickets_open',
    'Currently open tickets'
)

AI_REQUESTS_TOTAL = Counter(
    'support_bot_ai_requests_total',
    'Total AI requests',
    ['model', 'used_faq']
)

AI_TOKENS_TOTAL = Counter(
    'support_bot_ai_tokens_total',
    'Total tokens used',
    ['type']
)

AI_COST_TOTAL = Counter(
    'support_bot_ai_cost_total',
    'Total cost in USD',
    ['model']
)

AI_RESPONSE_TIME = Histogram(
    'support_bot_ai_response_time_seconds',
    'AI response time in seconds',
    ['model']
)

USER_RATINGS = Counter(
    'support_bot_user_ratings_total',
    'User ratings',
    ['rating']
)

USER_BLOCKS = Gauge(
    'support_bot_user_blocks',
    'Currently blocked users'
)

HTTP_REQUESTS_TOTAL = Counter(
    'support_bot_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

HTTP_REQUEST_TIME = Histogram(
    'support_bot_http_request_time_seconds',
    'HTTP request time in seconds',
    ['method', 'endpoint']
)

DB_CONNECTIONS = Gauge(
    'support_bot_db_connections',
    'Database connections'
)

BOT_INFO = Info(
    'support_bot',
    'Support bot information'
)

def init_bot_info():
    from config import BOT_TOKEN
    import os
    
    BOT_INFO.info({
        'version': '1.0.0',
        'python_version': os.popen('python --version').read().strip(),
        'environment': os.getenv('ENVIRONMENT', 'development')
    })

def track_message(sender_type: str, message_type: str = "text"):
    MESSAGES_TOTAL.labels(type=message_type, sender=sender_type).inc()

def track_ticket(status: str, priority: str, category: str):
    TICKETS_TOTAL.labels(status=status, priority=priority, category=category).inc()
    if status == "open":
        TICKETS_OPEN.inc()

def track_ai_request(model: str, used_faq: bool, tokens_prompt: int, tokens_completion: int, cost: float, response_time: float):
    AI_REQUESTS_TOTAL.labels(model=model, used_faq=str(used_faq)).inc()
    AI_TOKENS_TOTAL.labels(type='prompt').inc(tokens_prompt)
    AI_TOKENS_TOTAL.labels(type='completion').inc(tokens_completion)
    AI_COST_TOTAL.labels(model=model).inc(cost)
    AI_RESPONSE_TIME.labels(model=model).observe(response_time)

def track_rating(rating: str):
    USER_RATINGS.labels(rating=rating).inc()

def track_http_request(method: str, endpoint: str, status: int, duration: float):
    HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
    HTTP_REQUEST_TIME.labels(method=method, endpoint=endpoint).observe(duration)
