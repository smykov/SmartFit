from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# Метрики для отслеживания
REQUEST_COUNT = Counter(
    'smartfit_request_count',
    'Total request count',
    ['method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram(
    'smartfit_request_latency_seconds',
    'Request latency',
    ['endpoint']
)

ACTIVE_USERS = Gauge(
    'smartfit_active_users',
    'Number of active users'
)

DIET_PLANS_GENERATED = Counter(
    'smartfit_diet_plans_generated',
    'Number of diet plans generated'
)

MESSAGE_QUEUE_SIZE = Gauge(
    'smartfit_message_queue_size',
    'Size of message queue'
)


def setup_metrics(app):
    """Настройка метрик Prometheus для FastAPI"""
    instrumentator = Instrumentator().instrument(app)

    @app.on_event("startup")
    async def _startup():
        instrumentator.expose(app)