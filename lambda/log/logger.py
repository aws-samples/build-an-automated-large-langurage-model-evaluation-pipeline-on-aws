import logging

def app_logger(level=logging.INFO):
    logging.basicConfig(
        filename='eval.log',
        format='%(asctime)s - %(name)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=level
    )
    return logging.getLogger(__name__)

logger = app_logger()