import glob
import json
import datetime
import os
from services.exercise_services import create_exercise
from services.helper import logger


def load_db(json_data, f):
    exercise_name = json_data.get("name", f"null from {f}")
    primary_muscles = json_data.get("primaryMuscles", None)
    secondary_muscles = json_data.get("secondaryMuscles", None)
    equipment = json_data.get("equipment", "unknown")
    if equipment is None:
        equipment = "unknown"
    difficulty = json_data.get("level", "any")
    instructions = json_data.get("instructions", "No instructions available")
    custom = False
    created_at = str(datetime.datetime.now())
    
    result, success = create_exercise(exercise_name, primary_muscles, secondary_muscles, equipment, difficulty, instructions, None, custom, None, created_at)
    
    if not success:
        logger.error("Error when creating exercise")
        
    
    


folder_path = '/Users/ayan/Desktop/projs/free-exercise-db/exercises'

json_files_pattern = os.path.join(folder_path, '*.json')

json_file_paths = glob.glob(json_files_pattern)

for file_path in json_file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            load_db(data, f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred with {file_path}: {e}")
        
