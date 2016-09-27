import logging
from logging.handlers import RotatingFileHandler

import colorlog

from migrationmonitor import settings


logger = logging.getLogger("migration-monitor")


def info(*args, **kwargs):
    """Log info"""
    logger.info(*args, **kwargs)


def debug(*args, **kwargs):
    """Log debug"""
    logger.debug(*args, **kwargs)


def error(*args, **kwargs):
    """Log error"""
    logger.error(*args, **kwargs)


logger.setLevel(logging.DEBUG)
logger.propagate = False

_debug = getattr(settings, 'DEBUG', False)

handler = logging.StreamHandler() if _debug \
    else RotatingFileHandler(settings.LOG_FILE,
                             maxBytes=10 * 1024 * 1024,
                             backupCount=5)

formatter = \
    colorlog.ColoredFormatter("%(log_color)s%(levelname)s"
                              "[%(asctime)-15s] %(message)s") \
    if _debug \
    else logging.Formatter("%(levelname)s [%(asctime)-15s] %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)
