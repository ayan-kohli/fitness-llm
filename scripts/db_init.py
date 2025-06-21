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
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
        
        workout_table_sql = """
        CREATE TABLE IF NOT EXISTS workouts (
            workout_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            muscles_targeted VARCHAR(255), 
            llm_prompt TEXT,
            llm_raw TEXT,
            parsed_workout JSONB,
            date_generated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) NOT NULL,
            completed_on TIMESTAMP WITH TIME ZONE
        );
        """

        logger.info("Creating 'workouts' table...")
        cur.execute(workout_table_sql)
        conn.commit()
        logger.info("'workouts' table created successfully or already exists.")
        
        metrics_table_sql = """
        CREATE TABLE IF NOT EXISTS metrics (
            metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            height NUMERIC(5,2) NOT NULL, 
            weight NUMERIC(5,2) NOT NULL,
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """

        logger.info("Creating 'metrics' table...")
        cur.execute(metrics_table_sql)
        conn.commit()
        logger.info("'metrics' table created successfully or already exists.")
        
        exercises_table_sql = """
        CREATE TABLE IF NOT EXISTS exercises (
            exercise_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            exercise_name VARCHAR(255) UNIQUE,
            primary_muscle_group VARCHAR(255) NOT NULL,
            secondary_muscle_group VARCHAR(255), 
            equipment VARCHAR(255) NOT NULL,
            difficulty VARCHAR(100),
            instructions TEXT,
            video_url TEXT,
            custom BOOLEAN NOT NULL,
            user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT custom_then_user_id 
                CHECK ((NOT custom) OR (user_id IS NOT NULL))
        );
        """

        logger.info("Creating 'exercises' table...")
        cur.execute(exercises_table_sql)
        conn.commit()
        logger.info("'exercises' table created successfully or already exists.")


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