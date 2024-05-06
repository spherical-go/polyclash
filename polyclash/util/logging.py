import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    # create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # set the logger's level to DEBUG

    # get the hidden directory path of the current user
    hidden_dir = Path.home() / '.polyclash'

    # if the hidden directory does not exist, create it
    if not hidden_dir.exists():
        hidden_dir.mkdir()

    # log file path is app.log under the hidden folder
    log_file_path = hidden_dir / 'app.log'

    # create a file handler to write logs to a file
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1024*1024, backupCount=10)
    file_handler.setLevel(logging.DEBUG)  # 设置文件处理器的日志级别

    # create a log formatter to define the format of the log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()
