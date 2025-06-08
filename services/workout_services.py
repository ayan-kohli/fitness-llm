from configs.config import mongo_client
from pymongo import DESCENDING
from helper import *

fitsense_db = mongo_client.fitsense
workout_queries = fitsense_db.workout_queries

def create_workout(user_id, date_generated, muscle_groups_targeted, llm_prompt, llm_raw_out, parsed_workout, status, completed_on):
    doc = {
        "user_id": user_id, 
        "Date Generated": date_generated, 
        "Muscle Groups Targeted": muscle_groups_targeted, 
        "LLM Prompt": llm_prompt,
        "LLM Raw Output": llm_raw_out, 
        "Parsed Workout": parsed_workout,
        "Status": status,
        "Completed On": completed_on
    }
    result, success = generic_db_error_handling(workout_queries.insert_one, doc)
    if success:
        return {"_id": result.inserted_id}, True
    else:
        return None, False

def read_workout_by_id(workout_id):
    result, success = generic_db_error_handling(workout_queries.find_one, get_workout_query(workout_id))
    if result:
        return result, success
    else:
        return None, False

def read_workouts_for_user(user_id):
    result, success = generic_db_error_handling(workout_queries.find, get_user_query(user_id), 
                                                sort=[("Date Generated", DESCENDING)])
    if result:
        return result.to_list, success
    else:
        return [], False

def read_latest_workout_for_user(user_id):
    cursor, success = generic_db_error_handling(workout_queries.find, get_user_query(user_id), 
                                                sort=[("Date Generated", DESCENDING)], 
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

def complete_workout(workout_id, timestamp):
    new_value = {"$set": {
        "Status": "completed",
        "Completed On": timestamp
    }}
    result, success = generic_db_error_handling(workout_queries.update_one, get_workout_query(workout_id), new_value)
    if result:
        return check_update_result(result), success
    else:
        return False, False

def delete_workout_by_id(workout_id):
    result, success = generic_db_error_handling(workout_queries.delete_one, get_workout_query(workout_id))
    if result:
        return result.deleted_count > 0, success
    else:
        return False, False

def delete_user_workouts(user_id):
    result, success = generic_db_error_handling(workout_queries.delete_many, get_user_query(user_id))
    if result and success:
        return result.deleted_count > 0, success
    else:
        return False, False