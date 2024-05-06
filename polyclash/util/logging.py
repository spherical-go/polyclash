
def setup_logging():
    import sys
    from pathlib import Path
    from loguru import logger

    # get the hidden directory path of the current user
    logging_dir = Path.home() / '.polyclash'

    # if the hidden directory does not exist, create it
    if not logging_dir.exists():
        logging_dir.mkdir()

    # log file path is app.log under the hidden folder
    logging_file = 'app.log'
    log_file_path = logging_dir / logging_file

    # add handler to logger
    logger.add(log_file_path, enqueue=True, rotation='1 day', retention='1 month', backtrace=True, level='DEBUG')
    logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")

    return logging_dir, logging_file, logger


logging_dir, logging_file, logger = setup_logging()