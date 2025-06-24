import glob
import json
import datetime
import os
from services.exercise_services import create_exercise
from services.helper import logger


def load_db(json_data, file_name):
    exercise_name = json_data.get("name", f"null_name_from_{os.path.basename(file_name)}")
    
    def extract_muscle_names(muscles_raw):
        extracted_names = []
        if isinstance(muscles_raw, list):
            for muscle_item in muscles_raw:
                if isinstance(muscle_item, dict) and 'name' in muscle_item:
                    extracted_names.append(muscle_item['name'])
                elif isinstance(muscle_item, str):
                    extracted_names.append(muscle_item)
        return extracted_names

    primary_muscles_transformed = extract_muscle_names(json_data.get("primaryMuscles"))
    secondary_muscles_transformed = extract_muscle_names(json_data.get("secondaryMuscles"))

    equipment = json_data.get("equipment", "unknown")
    if equipment is None:
        equipment = "unknown"

    difficulty = json_data.get("level", "any")

    instructions_raw = json_data.get("instructions")
    instructions_transformed = "No instructions available."
    if isinstance(instructions_raw, list):
        instructions_transformed = "\n".join(instructions_raw)
    elif isinstance(instructions_raw, str):
        instructions_transformed = instructions_raw

    video_url = json_data.get("videoURL", None) 
    
    is_custom = False
    created_by_user_id = None
    
    created_at = datetime.datetime.now()

    result, success = create_exercise(
        exercise_name,
        primary_muscles_transformed,
        secondary_muscles_transformed,
        equipment,
        difficulty,
        instructions_transformed,
        video_url, 
        is_custom,
        created_by_user_id,
        created_at
    )
    
    if not success:
        logger.error(f"Error creating exercise '{exercise_name}' from file {os.path.basename(file_name)}")

folder_path = '/Users/ayan/Desktop/projs/free-exercise-db/exercises'

json_files_pattern = os.path.join(folder_path, '*.json')

json_file_paths = glob.glob(json_files_pattern)

for file_path in json_file_paths:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            load_db(data, file_path)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred with {file_path}: {e}")
        
