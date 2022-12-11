#!/usr/local/bin/python3
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import os

log_name = os.getenv('LOG_FILENAME')
log_path = os.getenv('LOG_PATH')

def rotational_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    log_filename = os.path.join(log_path, log_name) + '.log'
    handler = ConcurrentRotatingFileHandler(log_filename, maxBytes=10*1024*1024, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = rotational_logger()