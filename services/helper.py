from pymongo.errors import PyMongoError
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generic_db_error_handling(db_callable, *args, **kwargs):
    try:
        operation_result = db_callable(*args, **kwargs)
        return operation_result, True
    except PyMongoError as pye:
        logger.error(f"Database error {pye} when trying to create user", exc_info=True)
        return None, False 
    except Exception as e:
        logger.critical(f"Unexpected error {e} when creating user")
        return None, False  
    
def get_user_query(user_id):
    return {"user_id": user_id}