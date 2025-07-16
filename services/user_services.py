from configs.config import get_db_connection
import uuid
from datetime import datetime
from services.helper import db_operation_failed, check_row_count, logger
from psycopg2 import Error as Psycopg2Error

def create_user(timestamp, activity, plan, username="", passhash=""):
    user_id = str(uuid.uuid4())
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                insert_sql = """
                INSERT INTO users (user_id, username, password_hash, created_at, updated_at, activity_level, plan)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING user_id;
                """
                cur.execute(insert_sql, (user_id, username, passhash, timestamp, None, activity, plan))
                created_user_id = cur.fetchone()
                if created_user_id is None:
                    return None, False
                created_user_id = created_user_id[0]
                conn.commit()
                return {"user_id": str(created_user_id)}, True
    except Psycopg2Error as e:
        return db_operation_failed(e, "create user")
    except Exception as e:
        logger.critical(f"Unexpected error when creating user: {e}", exc_info=True)
        return None, False

def read_user(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                select_sql = "SELECT user_id, username, password_hash, created_at, updated_at, activity_level, plan FROM users WHERE user_id = %s;"
                cur.execute(select_sql, (user_id,))
                user_data = cur.fetchone()
                if user_data is None or cur.description is None:
                    return None, False
                columns = [desc[0] for desc in cur.description]
                user_dict = dict(zip(columns, user_data))
                if 'user_id' in user_dict and isinstance(user_dict['user_id'], uuid.UUID):
                    user_dict['user_id'] = str(user_dict['user_id'])
                if 'created_at' in user_dict and isinstance(user_dict['created_at'], datetime):
                    user_dict['created_at'] = user_dict['created_at'].isoformat()
                if 'updated_at' in user_dict and isinstance(user_dict['updated_at'], datetime):
                    user_dict['updated_at'] = user_dict['updated_at'].isoformat()
                return user_dict, True
    except Psycopg2Error as e:
        return db_operation_failed(e, "read user")
    except Exception as e:
        logger.critical(f"Unexpected error when reading user: {e}", exc_info=True)
        return None, False

def update_username(user_id, new_user, timestamp):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                update_sql = "UPDATE users SET username = %s, updated_at = %s WHERE user_id = %s;"
                cur.execute(update_sql, (new_user, timestamp, user_id))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "update username")
    except Exception as e:
        logger.critical(f"Unexpected error when updating username: {e}", exc_info=True)
        return False, False

def update_password(user_id, new_hash, timestamp):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                update_sql = "UPDATE users SET password_hash = %s, updated_at = %s WHERE user_id = %s;"
                cur.execute(update_sql, (new_hash, timestamp, user_id))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "update password")
    except Exception as e:
        logger.critical(f"Unexpected error when updating password: {e}", exc_info=True)
        return False, False

def update_activity(user_id, new_level, timestamp):
    if new_level not in ["Sedentary", "Lightly Active", "Active", "Extremely Active"]:
        logger.error("Invalid activity level provided")
        raise ValueError("Invalid activity level")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                update_sql = "UPDATE users SET activity_level = %s, updated_at = %s WHERE user_id = %s;"
                cur.execute(update_sql, (new_level, timestamp, user_id))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "update activity level")
    except Exception as e:
        logger.critical(f"Unexpected error when updating activity level: {e}", exc_info=True)
        return False, False

def update_plan(user_id, new_plan, timestamp):
    if new_plan not in ["Dirty Bulk", "Lean Bulk", "Standard Cut", "Aggressive Cut", "Body Recomposition", "Maintain"]:
        logger.error("Invalid plan provided")
        raise ValueError("Invalid plan")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                update_sql = "UPDATE users SET plan = %s, updated_at = %s WHERE user_id = %s;"
                cur.execute(update_sql, (new_plan, timestamp, user_id))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "update plan")
    except Exception as e:
        logger.critical(f"Unexpected error when updating plan: {e}", exc_info=True)
        return False, False

def delete_user(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                delete_sql = "DELETE FROM users WHERE user_id = %s;"
                cur.execute(delete_sql, (user_id,))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "delete user")
    except Exception as e:
        logger.critical(f"Unexpected error when deleting user: {e}", exc_info=True)
        return False, False