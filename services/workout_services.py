from configs.config import get_db_connection
from services.helper import db_operation_failed, check_row_count, logger
from psycopg2 import Error as Psycopg2Error
import uuid
from datetime import datetime
import json

def create_workout(user_id, date_generated, muscle_groups_targeted, llm_prompt, llm_raw_out, parsed_workout, status, completed_on):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                insert_sql = """
                INSERT INTO workouts (
                    user_id, muscles_targeted, llm_prompt, llm_raw,
                    parsed_workout, date_generated, status, completed_on
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING workout_id;
                """
                cur.execute(insert_sql, (
                    user_id, muscle_groups_targeted, llm_prompt, llm_raw_out,
                    json.dumps(parsed_workout), date_generated, status, completed_on
                ))
                created_workout_id = cur.fetchone()[0]
                conn.commit()
                return {"_id": str(created_workout_id)}, True
    except Psycopg2Error as e:
        return db_operation_failed(e, "create workout")
    except Exception as e:
        logger.critical(f"Unexpected error when creating workout: {e}", exc_info=True)
        return None, False

def read_workout_by_id(workout_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                select_sql = """
                SELECT workout_id, user_id, muscles_targeted, llm_prompt, llm_raw,
                       parsed_workout, date_generated, status, completed_on
                FROM workouts WHERE workout_id = %s;
                """
                cur.execute(select_sql, (workout_id,))
                workout_data = cur.fetchone()
                if workout_data:
                    columns = [desc[0] for desc in cur.description]
                    workout_dict = dict(zip(columns, workout_data))
                    
                    if 'workout_id' in workout_dict and isinstance(workout_dict['workout_id'], uuid.UUID):
                        workout_dict['workout_id'] = str(workout_dict['workout_id'])
                    if 'user_id' in workout_dict and isinstance(workout_dict['user_id'], uuid.UUID):
                        workout_dict['user_id'] = str(workout_dict['user_id'])
                    if 'date_generated' in workout_dict and isinstance(workout_dict['date_generated'], datetime):
                        workout_dict['date_generated'] = workout_dict['date_generated'].isoformat()
                    if 'completed_on' in workout_dict and isinstance(workout_dict['completed_on'], datetime):
                        workout_dict['completed_on'] = workout_dict['completed_on'].isoformat()

                    return workout_dict, True
                return None, False
    except Psycopg2Error as e:
        return db_operation_failed(e, "read workout by id")
    except Exception as e:
        logger.critical(f"Unexpected error when reading workout by id: {e}", exc_info=True)
        return None, False

def read_workouts_for_user(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                select_sql = """
                SELECT workout_id, user_id, muscles_targeted, llm_prompt, llm_raw,
                       parsed_workout, date_generated, status, completed_on
                FROM workouts WHERE user_id = %s
                ORDER BY date_generated DESC;
                """
                cur.execute(select_sql, (user_id,))
                workouts_data = cur.fetchall()
                
                result_list = []
                columns = [desc[0] for desc in cur.description]
                for row in workouts_data:
                    workout_dict = dict(zip(columns, row))
                    if 'workout_id' in workout_dict and isinstance(workout_dict['workout_id'], uuid.UUID):
                        workout_dict['workout_id'] = str(workout_dict['workout_id'])
                    if 'user_id' in workout_dict and isinstance(workout_dict['user_id'], uuid.UUID):
                        workout_dict['user_id'] = str(workout_dict['user_id'])
                    if 'date_generated' in workout_dict and isinstance(workout_dict['date_generated'], datetime):
                        workout_dict['date_generated'] = workout_dict['date_generated'].isoformat()
                    if 'completed_on' in workout_dict and isinstance(workout_dict['completed_on'], datetime):
                        workout_dict['completed_on'] = workout_dict['completed_on'].isoformat()
                    result_list.append(workout_dict)
                return result_list, True
    except Psycopg2Error as e:
        return db_operation_failed(e, "read workouts for user")
    except Exception as e:
        logger.critical(f"Unexpected error when reading workouts for user: {e}", exc_info=True)
        return [], False

def read_latest_workout_for_user(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                select_sql = """
                SELECT workout_id, user_id, muscles_targeted, llm_prompt, llm_raw,
                       parsed_workout, date_generated, status, completed_on
                FROM workouts WHERE user_id = %s
                ORDER BY date_generated DESC LIMIT 1;
                """
                cur.execute(select_sql, (user_id,))
                latest_doc = cur.fetchone()
                if latest_doc:
                    columns = [desc[0] for desc in cur.description]
                    workout_dict = dict(zip(columns, latest_doc))

                    if 'workout_id' in workout_dict and isinstance(workout_dict['workout_id'], uuid.UUID):
                        workout_dict['workout_id'] = str(workout_dict['workout_id'])
                    if 'user_id' in workout_dict and isinstance(workout_dict['user_id'], uuid.UUID):
                        workout_dict['user_id'] = str(workout_dict['user_id'])
                    if 'date_generated' in workout_dict and isinstance(workout_dict['date_generated'], datetime):
                        workout_dict['date_generated'] = workout_dict['date_generated'].isoformat()
                    if 'completed_on' in workout_dict and isinstance(workout_dict['completed_on'], datetime):
                        workout_dict['completed_on'] = workout_dict['completed_on'].isoformat()

                    return workout_dict, True
                return None, False
    except Psycopg2Error as e:
        return db_operation_failed(e, "read latest workout for user")
    except Exception as e:
        logger.critical(f"Unexpected error when reading latest workout for user: {e}", exc_info=True)
        return None, False

def complete_workout(workout_id, timestamp):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                update_sql = """
                UPDATE workouts SET status = %s, completed_on = %s
                WHERE workout_id = %s;
                """
                cur.execute(update_sql, ("completed", timestamp, workout_id))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "complete workout")
    except Exception as e:
        logger.critical(f"Unexpected error when completing workout: {e}", exc_info=True)
        return False, False

def delete_workout_by_id(workout_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                delete_sql = "DELETE FROM workouts WHERE workout_id = %s;"
                cur.execute(delete_sql, (workout_id,))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "delete workout by id")
    except Exception as e:
        logger.critical(f"Unexpected error when deleting workout by id: {e}", exc_info=True)
        return False, False

def delete_user_workouts(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                delete_sql = "DELETE FROM workouts WHERE user_id = %s;"
                cur.execute(delete_sql, (user_id,))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "delete user workouts")
    except Exception as e:
        logger.critical(f"Unexpected error when deleting user workouts: {e}", exc_info=True)
        return False, False