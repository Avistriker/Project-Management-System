# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:10000"
backlog = 2048

# Worker processes
workers = 1  # For free tier on Render
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Increased timeout to 2 minutes
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "project_management_system"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (not needed for now)
# keyfile = None
# certfile = None

# Server hooks
def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    server.log.info("Worker %s spawned (pid: %s)", worker.id, worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("Worker received SIGABRT signal")
