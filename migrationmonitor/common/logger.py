import logging
from logging.handlers import RotatingFileHandler

import colorlog

from migrationmonitor import settings


LOGGER = logging.getLogger("migration-monitor")


def info(*args, **kwargs):
    """Log info"""
    LOGGER.info(*args, **kwargs)


def debug(*args, **kwargs):
    """Log debug"""
    LOGGER.debug(*args, **kwargs)


def error(*args, **kwargs):
    """Log error"""
    LOGGER.error(*args, **kwargs)

def _configure_logger():
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.propagate = False

    _debug = getattr(settings, 'DEBUG', False)

    handler = logging.StreamHandler() if _debug \
        else RotatingFileHandler(settings.LOG_FILE,
                                 maxBytes=10 * 1024 * 1024,
                                 backupCount=5)

    formatter = \
        colorlog.ColoredFormatter("%(log_color)s%(levelname)s [%(asctime)-15s] %(message)s") \
        if _debug \
        else logging.Formatter("%(levelname)s [%(asctime)-15s] %(message)s")

    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)

_configure_logger()
