import logging

from app.logging_config import setup_logging


setup_logging()

logger = logging.getLogger(__name__)


logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")