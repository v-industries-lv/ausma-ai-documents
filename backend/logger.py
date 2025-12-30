import os
import logging
import sys
from logging.handlers import TimedRotatingFileHandler


def logger_setup():
    LOG_DIR = 'logs'
    LOG_FILE = os.path.join(LOG_DIR, 'info.log')

    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger('llm_logger')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(filename)s:%(lineno)-3d (%(thread)d) - %(levelname)-7s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    tr_fh = TimedRotatingFileHandler(LOG_FILE, when="midnight", backupCount=30)
    tr_fh.suffix = "%Y%m%d"
    tr_fh.setFormatter(formatter)
    logger.addHandler(tr_fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    return logger

logger = logger_setup()