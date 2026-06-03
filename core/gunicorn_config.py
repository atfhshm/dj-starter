"""Gunicorn configuration for serving the Django ASGI app with uvicorn workers.

Run with:
    gunicorn -c core/gunicorn_config.py

Only deviations from gunicorn's defaults live here.
Settings reference: https://docs.gunicorn.org/en/stable/settings.html
"""

import multiprocessing
import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

ENV = environ.Env()
ENV.read_env(BASE_DIR / ".env")

wsgi_app = "core.asgi:application"
worker_class = "core.worker.ASGIWorker"

# WEB_CONCURRENCY is the conventional knob (most PaaS platforms set it).
workers = ENV.int("WEB_CONCURRENCY", default=multiprocessing.cpu_count() * 2 + 1)

bind = ENV.str("GUNICORN_BIND", default="0.0.0.0:8000")
loglevel = ENV.str("GUNICORN_LOGLEVEL", default="info")

# Load the app before forking: copy-on-write memory savings and fail-fast
# imports, at the cost of `kill -HUP` no longer picking up code changes.
preload_app = True

# Recycle workers after this many requests (± jitter) to curb slow memory leaks.
max_requests = 1000
max_requests_jitter = 100

# Seconds without a heartbeat before the master kills a worker. The uvicorn
# worker heartbeats from its event loop, so long requests don't trip this —
# it only fires when the loop itself is blocked or the process hangs.
timeout = ENV.int("GUNICORN_TIMEOUT", default=60)

# Gunicorn defaults to 2s; keep this above the load balancer's idle timeout
# (e.g. 75 > ALB's 60) so the LB never reuses a connection we're closing.
keepalive = 75

# Gunicorn doesn't log access at all by default; "-" = stdout.
accesslog = "-"
capture_output = True

# Safe because gunicorn only runs behind nginx/Caddy, which overwrite
# the X-Forwarded-* headers; set to the proxy IP if that ever changes.
forwarded_allow_ips = ENV.str("GUNICORN_FORWARDED_ALLOW_IPS", default="*")

# Keep worker heartbeat tmpfiles in shared memory — avoids workers stalling
# on blocking disk I/O in containers (/dev/shm is Linux-only).
if os.path.exists("/dev/shm"):
    worker_tmp_dir = "/dev/shm"
