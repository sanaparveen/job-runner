"""
Script runs both jobrunner flows in a single process.
"""
import datetime
import logging
from pathlib import Path
import os
import sys
import time
import threading

# temp workaround for not having PYTHONPATH in the service config
sys.path.insert(0, "./lib")

from .log_utils import configure_logging, set_log_context
from . import config


from . import run
from . import sync

log = logging.getLogger(__name__)


def main():
    """Run the main run loop after starting the sync loop in a thread."""
    # extra space to align with other thread's "sync" label.
    threading.current_thread().name = "run "
    fmt = "{asctime} {threadName} {message} {tags}"
    configure_logging(fmt)

    # load any env file
    path = Path(os.environ.get("ENVPATH", ".env"))
    if path.exists():
        log.info(f"Loading environment variables from {path}")
        env = parse_env(path.read_text())
        if env:
            os.environ.update(env)

    try:
        log.info("jobrunner.service started")
        # daemon=True means this thread will be automatically join()ed when the
        # process exits
        thread = threading.Thread(target=sync_wrapper, daemon=True)
        thread.name = 'sync'
        thread.start()
        run.main()
    except KeyboardInterrupt:
        log.info("jobrunner.service stopped")


def sync_wrapper():
    with set_log_context(prefix="sync"):
        sync.main()


def parse_env(contents):
    """Parse a simple environment file."""
    env = {}
    for line in contents.split("\n"):
        line = line.strip()
        if not line or line[0] == "#":
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


if __name__ == "__main__":
    main()
