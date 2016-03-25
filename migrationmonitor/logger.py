import logging
import settings
from logging.handlers import RotatingFileHandler


logger = logging.getLogger("migration-monitor")
logger.setLevel(logging.DEBUG)
logger.propagate = False


handler = logging.StreamHandler() \
    if getattr(settings, 'DEBUG', False) \
    else RotatingFileHandler(settings.LOG_FILE,
                             maxBytes=10 * 1024 * 1024,
                             backupCount=5)

formatter = logging.Formatter("%(levelname)s [%(asctime)-15s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def info(*args, **kwargs):
    logger.info(*args, **kwargs)


def debug(*args, **kwargs):
    logger.debug(*args, **kwargs)


def error(*args, **kwargs):
    logger.error(*args, **kwargs)
