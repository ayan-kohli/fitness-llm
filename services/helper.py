import logging
from psycopg2 import Error as Psycopg2Error

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def db_operation_failed(e, operation_name):
    logger.error(f"Database error during {operation_name}: {e}", exc_info=True)
    return None, False

def check_row_count(row_count):
    return row_count > 0
