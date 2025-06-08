from configs.config import mongo_client
from pymongo import DESCENDING
from helper import *

fitsense_db = mongo_client.fitsense
metrics_info = fitsense_db.metrics_info

def create_metric(user_id, timestamp, height, weight):
    doc = {
        "user_id": user_id, 
        "Height": height,
        "Weight": weight,
        "Recorded At": timestamp,
        
    }
    result, success = generic_db_error_handling(metrics_info.insert_one, doc)
    if result and success:
        return {"_id": result.inserted_id, "user_id": user_id}, True
    else:
        return None, False

def read_latest_height(user_id):
    cursor, success = generic_db_error_handling(metrics_info.find, get_user_query(user_id), 
                                                sort=[("Recorded At", DESCENDING)], 
                                                limit=1)
    if cursor and success:
        try:
            latest_doc = next(cursor, None)
            if latest_doc:
                return latest_doc, True 
            else:
                return None, False 
        except Exception as e:
            logger.error(f"Error processing cursor in read_latest_height: {e}", exc_info=True)
            return None, False
    else: 
        return None, False

def read_latest_weight(user_id):
    cursor, success = generic_db_error_handling(metrics_info.find, get_user_query(user_id), 
                                                sort=[("Recorded At", DESCENDING)], 
                                                limit=1)
    if cursor and success:
        try:
            latest_doc = next(cursor, None)
            if latest_doc:
                return latest_doc, True 
            else:
                return None, False 
        except Exception as e:
            logger.error(f"Error processing cursor in read_latest_weight: {e}", exc_info=True)
            return None, False
    else: 
        return None, False

def update_height(user_id, new_height, timestamp):
    result, success = read_latest_weight(user_id)
    current_weight = result.get("Weight") if result else None
    if not success:
        return None, False
    return create_metric(user_id, timestamp, new_height, current_weight)

def update_weight(user_id, new_weight, timestamp):
    result, success = read_latest_height(user_id)
    current_height = result.get("Height") if result else None
    if not success:
        return None, False
    return create_metric(user_id, timestamp, current_height, new_weight)

def delete_user_metrics(user_id):
    result, success = generic_db_error_handling(metrics_info.delete_many, get_user_query(user_id))
    if result and success:
        return result.deleted_count > 0, success
    else:
        return False, False