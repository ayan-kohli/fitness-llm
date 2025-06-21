from configs.config import get_db_connection
from services.helper import db_operation_failed, check_row_count, logger
from psycopg2 import Error as Psycopg2Error
import uuid
from datetime import datetime

def create_exercise(name, primary_muscle_group, secondary_muscle_group, equipment, difficulty, instructions, video_url, is_custom, user_id_custom, created_at):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                insert_sql = """
                INSERT INTO exercises (
                    exercise_name, primary_muscle_group, secondary_muscle_group,
                    equipment, difficulty, instructions, video_url,
                    custom, user_id, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING exercise_id;
                """
                # user_id_custom should be None if not custom, otherwise the actual UUID string
                cur.execute(insert_sql, (
                    name, primary_muscle_group, secondary_muscle_group,
                    equipment, difficulty, instructions, video_url,
                    is_custom, user_id_custom, created_at
                ))
                created_exercise_id = cur.fetchone()[0]
                conn.commit()
                return {"_id": str(created_exercise_id)}, True
    except Psycopg2Error as e:
        return db_operation_failed(e, "create exercise")
    except Exception as e:
        logger.critical(f"Unexpected error when creating exercise: {e}", exc_info=True)
        return None, False

def read_exercise_by_name(name):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                select_sql = """
                SELECT exercise_id, exercise_name, primary_muscle_group, secondary_muscle_group,
                       equipment, difficulty, instructions, video_url,
                       custom, user_id, created_at
                FROM exercises WHERE exercise_name = %s;
                """
                cur.execute(select_sql, (name,))
                exercise_data = cur.fetchone()
                if exercise_data:
                    columns = [desc[0] for desc in cur.description]
                    exercise_dict = dict(zip(columns, exercise_data))

                    if 'exercise_id' in exercise_dict and isinstance(exercise_dict['exercise_id'], uuid.UUID):
                        exercise_dict['exercise_id'] = str(exercise_dict['exercise_id'])
                    if 'user_id' in exercise_dict and isinstance(exercise_dict['user_id'], uuid.UUID):
                        exercise_dict['user_id'] = str(exercise_dict['user_id'])
                    if 'created_at' in exercise_dict and isinstance(exercise_dict['created_at'], datetime):
                        exercise_dict['created_at'] = exercise_dict['created_at'].isoformat()
                    return exercise_dict, True
                return None, False
    except Psycopg2Error as e:
        return db_operation_failed(e, "read exercise by name")
    except Exception as e:
        logger.critical(f"Unexpected error when reading exercise by name: {e}", exc_info=True)
        return None, False

# No other exercise functions were provided in your initial codebase,
# so only create and read by name are implemented.