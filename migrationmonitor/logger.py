import logging
import colorlog
import settings
from logging.handlers import RotatingFileHandler


logger = logging.getLogger("migration-monitor")
logger.setLevel(logging.DEBUG)
logger.propagate = False

debug = getattr(settings, 'DEBUG', False)

handler = logging.StreamHandler() if debug \
    else RotatingFileHandler(settings.LOG_FILE,
                             maxBytes=10 * 1024 * 1024,
                             backupCount=5)

formatter = \
    colorlog.ColoredFormatter("%(log_color)s%(levelname)s [%(asctime)-15s] %(message)s") \
    if debug \
    else logging.Formatter("%(levelname)s [%(asctime)-15s] %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)


def info(*args, **kwargs):
    logger.info(*args, **kwargs)


def debug(*args, **kwargs):
    logger.debug(*args, **kwargs)


def error(*args, **kwargs):
    logger.error(*args, **kwargs)
