from pathlib import Path
from loguru import logger


def setup_logging():
    # get the hidden directory path of the current user
    logging_dir = Path.home() / '.polyclash'

    # if the hidden directory does not exist, create it
    if not logging_dir.exists():
        logging_dir.mkdir()

    # log file path is app.log under the hidden folder
    logging_file = 'app.log'
    log_file_path = logging_dir / logging_file

    # add handler to logger
    formatter = "{time} - {level} - [{process.id}] - [{thread.id}] - {file} - {line} - {message}"
    logger.add(log_file_path, format=formatter, enqueue=True, rotation='1 day', retention='1 month', backtrace=True, diagnose=True)

    return logging_dir, logging_file, logger


logging_dir, logging_file, logger = setup_logging()
