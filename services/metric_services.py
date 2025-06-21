from configs.config import get_db_connection
from services.helper import db_operation_failed, check_row_count, logger
from psycopg2 import Error as Psycopg2Error
import uuid
from datetime import datetime

def create_metric(user_id, timestamp, height, weight):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                insert_sql = """
                INSERT INTO metrics (user_id, height, weight, recorded_at)
                VALUES (%s, %s, %s, %s)
                RETURNING metric_id;
                """
                cur.execute(insert_sql, (user_id, height, weight, timestamp))
                created_metric_id = cur.fetchone()[0]
                conn.commit()
                return {"_id": str(created_metric_id)}, True
    except Psycopg2Error as e:
        return db_operation_failed(e, "create metric")
    except Exception as e:
        logger.critical(f"Unexpected error when creating metric: {e}", exc_info=True)
        return None, False

def read_latest_height(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                select_sql = """
                SELECT metric_id, user_id, height, weight, recorded_at
                FROM metrics WHERE user_id = %s
                ORDER BY recorded_at DESC LIMIT 1;
                """
                cur.execute(select_sql, (user_id,))
                latest_doc = cur.fetchone()
                if latest_doc:
                    columns = [desc[0] for desc in cur.description]
                    metric_dict = dict(zip(columns, latest_doc))

                    if 'metric_id' in metric_dict and isinstance(metric_dict['metric_id'], uuid.UUID):
                        metric_dict['metric_id'] = str(metric_dict['metric_id'])
                    if 'user_id' in metric_dict and isinstance(metric_dict['user_id'], uuid.UUID):
                        metric_dict['user_id'] = str(metric_dict['user_id'])
                    if 'recorded_at' in metric_dict and isinstance(metric_dict['recorded_at'], datetime):
                        metric_dict['recorded_at'] = metric_dict['recorded_at'].isoformat()
                    return metric_dict, True
                return None, False
    except Psycopg2Error as e:
        return db_operation_failed(e, "read latest height")
    except Exception as e:
        logger.critical(f"Unexpected error in read_latest_height: {e}", exc_info=True)
        return None, False

def read_latest_weight(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                select_sql = """
                SELECT metric_id, user_id, height, weight, recorded_at
                FROM metrics WHERE user_id = %s
                ORDER BY recorded_at DESC LIMIT 1;
                """
                cur.execute(select_sql, (user_id,))
                latest_doc = cur.fetchone()
                if latest_doc:
                    columns = [desc[0] for desc in cur.description]
                    metric_dict = dict(zip(columns, latest_doc))

                    if 'metric_id' in metric_dict and isinstance(metric_dict['metric_id'], uuid.UUID):
                        metric_dict['metric_id'] = str(metric_dict['metric_id'])
                    if 'user_id' in metric_dict and isinstance(metric_dict['user_id'], uuid.UUID):
                        metric_dict['user_id'] = str(metric_dict['user_id'])
                    if 'recorded_at' in metric_dict and isinstance(metric_dict['recorded_at'], datetime):
                        metric_dict['recorded_at'] = metric_dict['recorded_at'].isoformat()
                    return metric_dict, True
                return None, False
    except Psycopg2Error as e:
        return db_operation_failed(e, "read latest weight")
    except Exception as e:
        logger.critical(f"Unexpected error in read_latest_weight: {e}", exc_info=True)
        return None, False

def update_height(user_id, new_height, timestamp):
    result, success = read_latest_weight(user_id)
    current_weight = result.get("weight") if result else None
    if not success:
        return None, False
    return create_metric(user_id, timestamp, new_height, current_weight)

def update_weight(user_id, new_weight, timestamp):
    result, success = read_latest_height(user_id)
    current_height = result.get("height") if result else None
    if not success:
        return None, False
    return create_metric(user_id, timestamp, current_height, new_weight)

def delete_user_metrics(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                delete_sql = "DELETE FROM metrics WHERE user_id = %s;"
                cur.execute(delete_sql, (user_id,))
                conn.commit()
                return check_row_count(cur.rowcount), True
    except Psycopg2Error as e:
        return db_operation_failed(e, "delete user metrics")
    except Exception as e:
        logger.critical(f"Unexpected error when deleting user metrics: {e}", exc_info=True)
        return False, False