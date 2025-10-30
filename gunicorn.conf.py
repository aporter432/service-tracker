"""
Gunicorn configuration file for ORBCOMM Service Tracker
Documentation: https://docs.gunicorn.org/en/stable/settings.html
"""

import multiprocessing
import os

# Server socket
bind = f"{os.environ.get('HOST', '0.0.0.0')}:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.environ.get("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "gevent"  # Async worker for better concurrency
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = (
    50  # Add randomness to max_requests to prevent all workers restarting at once
)
timeout = 120  # 2 minutes
keepalive = 5

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = os.environ.get("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "orbcomm-tracker"


# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    print(f"Starting Gunicorn server with {workers} workers")


def on_reload(server):
    """Called to recycle workers during a reload."""
    print("Reloading workers...")


def when_ready(server):
    """Called just after the server is started."""
    print(f"Server is ready. Listening on {bind}")


def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker spawned (pid: {worker.pid})")


def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    print(f"Worker received INT or QUIT signal (pid: {worker.pid})")


def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"Worker aborted (pid: {worker.pid})")


# SSL (for production with certificates)
keyfile = os.environ.get("SSL_KEYFILE")
certfile = os.environ.get("SSL_CERTFILE")

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Development settings (override in production)
if os.environ.get("FLASK_ENV") == "development":
    reload = True
    reload_extra_files = []
    workers = 2
    loglevel = "debug"
