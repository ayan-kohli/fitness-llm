from configs.config import mongo_client
from .helper import *

fitsense_db = mongo_client.fitsense
exercises = fitsense_db.exercises

def create_exercise(name, primary_muscle_group, secondary_muscle_group, equipment, difficulty, instructions, video_url, is_custom, user_id_custom, created_at):
    doc = {
        "Name": name, 
        "Primary Muscle Group Targeted": primary_muscle_group, 
        "Secondary Muscle Groups Targeted": secondary_muscle_group, 
        "Equipment": equipment,
        "Difficulty": difficulty, 
        "Instructions": instructions,
        "Video URL": video_url,
        "Custom": is_custom,
        "User ID (if custom)": user_id_custom,
        "Date Generated": created_at, 
    }
    result, success = generic_db_error_handling(exercises.insert_one, doc)
    if success:
        return {"_id": result.inserted_id}, True
    else:
        return None, False

def read_exercise_by_name(name):
    result, success = generic_db_error_handling(exercises.find_one, {"Name": name})
    if result:
        return result, success
    else:
        return None, False
