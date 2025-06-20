# db_init.py
from configs.config import get_db_connection
import logging
from psycopg2 import Error as Psycopg2Error

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_tables():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        users_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            username VARCHAR(255) UNIQUE, 
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE,
            activity_level VARCHAR(50) NOT NULL,
            plan VARCHAR(50) NOT NULL
        );
        """

        logger.info("Creating 'users' table...")
        cur.execute(users_table_sql)
        conn.commit()
        logger.info("'users' table created successfully or already exists.")

    except Psycopg2Error as e:
        logger.error(f"Database error during table creation: {e}", exc_info=True)
        if conn:
            conn.rollback() 
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred during table creation: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        create_tables()
        logger.info("Database initialization complete.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")