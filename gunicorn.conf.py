# gunicorn.conf.py
# Gunicorn configuration for Render deployment with Supabase

import os
import multiprocessing

# ============================================
# Server Socket Configuration
# ============================================

# Bind to the port provided by Render
port = os.getenv('PORT', '10000')
bind = f"0.0.0.0:{port}"

# Backlog of pending connections
backlog = 2048

# ============================================
# Worker Processes
# ============================================

# Number of worker processes
# For Render free tier, use 1 worker to save memory
workers = 1

# Number of threads per worker
threads = 1

# Worker class to use
worker_class = 'sync'

# Maximum number of requests a worker will process before restarting
max_requests = 200
max_requests_jitter = 50

# Worker timeout in seconds
timeout = 120

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Keep-alive connections
keepalive = 2

# Maximum number of simultaneous clients per worker
worker_connections = 1000

# ============================================
# Logging Configuration
# ============================================

# Access log file (use '-' for stdout)
accesslog = '-'

# Error log file (use '-' for stderr)
errorlog = '-'

# Log level (debug, info, warning, error, critical)
loglevel = 'info'

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ============================================
# Process Naming
# ============================================

# Process name for psutil/htop
proc_name = 'project-management-system'

# ============================================
# Security
# ============================================

# Limit request line size
limit_request_line = 4094

# Limit request fields
limit_request_fields = 100

# Limit request field size
limit_request_field_size = 8190

# ============================================
# Development vs Production
# ============================================

# Auto-reload on code changes (set to True only for development)
reload = False

# Number of seconds to wait before restarting workers
worker_tmp_dir = '/dev/shm'

# ============================================
# Preload Application
# ============================================

# Preload the application before forking workers
# Set to False for better database connection handling
preload_app = False

# ============================================
# Daemonize
# ============================================

# Whether to daemonize the Gunicorn process
daemon = False

# ============================================
# PID File
# ============================================

# Path to PID file
pidfile = None

# ============================================
# Umask
# ============================================

# Umask to use when creating files
umask = 0

# ============================================
# User and Group
# ============================================

# Switch to this user after binding
user = None

# Switch to this group after binding
group = None

# ============================================
# Callback Functions
# ============================================

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("=" * 60)
    server.log.info("Starting Project Management System - Gunicorn Server")
    server.log.info("=" * 60)
    server.log.info(f"Binding to: {bind}")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Threads: {threads}")
    server.log.info(f"Timeout: {timeout}s")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned successfully (pid: {worker.pid})")

def worker_int(worker):
    """Called just after a worker received the SIGINT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGINT, shutting down gracefully...")

def worker_abort(worker):
    """Called just after a worker received the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGABRT, shutting down immediately...")

def worker_exit(server, worker):
    """Called when a worker exits"""
    server.log.info(f"Worker (pid: {worker.pid}) exiting, cleaning up...")

def on_exit(server):
    """Called just before the master process exits."""
    server.log.info("=" * 60)
    server.log.info("Project Management System - Gunicorn Server Shutting Down")
    server.log.info("=" * 60)

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("=" * 60)
    server.log.info("✅ Gunicorn Server is ready and accepting connections!")
    server.log.info(f"   Listening on: {bind}")
    server.log.info(f"   Workers: {workers}")
    server.log.info(f"   Threads: {threads}")
    server.log.info(f"   Timeout: {timeout}s")
    server.log.info("=" * 60)
    
    # Log database configuration (without exposing password)
    db_host = os.getenv('DB_HOST', 'localhost')
    db_type = os.getenv('DATABASE_TYPE', 'postgresql')
    server.log.info(f"📊 Database Type: {db_type}")
    server.log.info(f"📊 Database Host: {db_host}")
    server.log.info(f"📊 Database Port: {os.getenv('DB_PORT', '5432')}")
    
    # Check if running on Render
    if os.getenv('RENDER', False):
        server.log.info("🚀 Running on Render Platform")
        external_host = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')
        server.log.info(f"🌐 Service URL: https://{external_host}")
    else:
        server.log.info("💻 Running in local development mode")
    
    server.log.info("=" * 60)

def pre_request(worker, req):
    """Called just before a request is processed."""
    worker.log.debug(f"Processing request: {req.method} {req.path}")

def post_request(worker, req, environ, resp):
    """Called just after a request has been processed."""
    if resp.status_code >= 400:
        worker.log.warning(f"Request failed: {req.method} {req.path} - Status: {resp.status_code}")
    else:
        worker.log.debug(f"Request completed: {req.method} {req.path} - Status: {resp.status_code}")

# ============================================
# Error Handling
# ============================================

def on_reload(server):
    """Called just before the master process is reloaded."""
    server.log.info("Reloading Gunicorn configuration...")

# ============================================
# StatsD Configuration (Optional)
# ============================================

# StatsD host to send metrics to
statsd_host = None

# StatsD port
statsd_port = 8125

# StatsD prefix
statsd_prefix = ''

# ============================================
# Prometheus Configuration (Optional)
# ============================================

# Enable Prometheus metrics
enable_metrics = False

# Metrics port
metrics_port = 9100

# ============================================
# Environment Variables to Set
# ============================================

def post_worker_init(worker):
    """Called just after a worker has been initialized."""
    import socket
    import time
    
    # Set socket timeout
    socket.setdefaulttimeout(30)
    
    worker.log.info(f"Worker {worker.pid} initialized successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}")

# ============================================
# Main Configuration Summary
# ============================================

if __name__ == "__main__":
    print("Gunicorn Configuration Summary:")
    print(f"  bind: {bind}")
    print(f"  workers: {workers}")
    print(f"  threads: {threads}")
    print(f"  timeout: {timeout}")
    print(f"  max_requests: {max_requests}")
    print(f"  loglevel: {loglevel}")
    print(f"  proc_name: {proc_name}")
