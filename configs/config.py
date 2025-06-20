from pymongo import MongoClient
from groq import Groq
import os 
from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error as Psycopg2Error
from services.helper import logger

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
      raise ValueError("Mongo connection string not properly initialized, please try again")

mongo_client = MongoClient(mongo_uri)

groq_api = os.getenv("GROK_API")
if not groq_api:
      raise ValueError("Grok API key not properly initialized, please try again")

groq_client = Groq(api_key=groq_api)

PG_URI = os.getenv("DATABASE_URL")
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(PG_URI)
        return conn
    except Psycopg2Error as e:
        logger.error(f"PostgreSQL connection error: {e}", exc_info=True)
        raise ConnectionError(f"Failed to connect to PostgreSQL: {e}") from e