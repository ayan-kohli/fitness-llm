from configs.config import mongo_client
from uuid import uuid4
from .helper import *

fitsense_db = mongo_client.fitsense
user_info = fitsense_db.user_info

def create_user(timestamp, activity, plan, user="", passhash=""):
    UNIQUE_ID = str(uuid4())
    doc = {
        "user_id": UNIQUE_ID, 
        "Username": user, 
        "Password": passhash, 
        "Date Created": timestamp,
        "Updated At": None, 
        "Activity Level": activity,
        "Plan": plan
    }
    result, success = generic_db_error_handling(user_info.insert_one, doc)
    if success:
        return {"_id": result.inserted_id, "user_id": UNIQUE_ID}, True
    else:
        return None, False

def get_user_query(user_id):
    return {"user_id": user_id}

def read_user(user_id):
    result, success = generic_db_error_handling(user_info.find_one, get_user_query(user_id))
    if result:
        return result, success
    else:
        return None, False

def update_username(user_id, new_user, timestamp):
    new_value = {"$set": {
        "Username": new_user,
        "Updated At": timestamp
    }}
    result, success = generic_db_error_handling(user_info.update_one, get_user_query(user_id), new_value)
    if result:
        return check_update_result(result), success
    else:
        return False, False

def update_password(user_id, new_hash, timestamp):
    new_value = {"$set": {
        "Password": new_hash,
        "Updated At": timestamp
    }}
    result, success = generic_db_error_handling(user_info.update_one, get_user_query(user_id), new_value)
    if result:
        return check_update_result(result), success
    else:
        return False, False

def update_activity(user_id, new_level, timestamp):
    if new_level not in ["Sedentary", "Lightly Active", "Active", "Extremely Active"]:
        raise ValueError("Invalid activity level")
    
    new_value = {"$set": {
        "Activity Level": new_level,
        "Updated At": timestamp
    }}
    result, success = generic_db_error_handling(user_info.update_one, get_user_query(user_id), new_value)
    if result:
        return check_update_result(result), success
    else:
        return False, False
    
def update_plan(user_id, new_plan, timestamp):
    if new_plan not in ["Dirty Bulk", "Lean Bulk", "Standard Cut", "Aggressive Cut", "Body Recomposition", "Maintain"]:
        raise ValueError("Invalid plan")

    new_value = {"$set": {
        "Plan": new_plan,
        "Updated At": timestamp
    }}
    result, success = generic_db_error_handling(user_info.update_one, get_user_query(user_id), new_value)
    if result:
        return check_update_result(result), success
    else:
        return False, False

def delete_user(user_id):
    result, success = generic_db_error_handling(user_info.delete_one, get_user_query(user_id))
    if result:
        return result.deleted_count > 0, success
    else:
        return False, False