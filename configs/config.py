from pymongo import MongoClient
from groq import Groq
import os 
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
      raise ValueError("Mongo connection string not properly initialized, please try again")

mongo_client = MongoClient(mongo_uri)

groq_api = os.getenv("GROK_API")
if not groq_api:
      raise ValueError("Grok API key not properly initialized, please try again")

groq_client = Groq(api_key=groq_api)