from flask import Flask, render_template, jsonify, request, redirect
from pymongo import MongoClient
import os 
from dotenv import load_dotenv
from datetime import datetime
from groq import Groq

load_dotenv()
app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
      raise ValueError("Mongo connection string not properly initialized, please try again")

client = MongoClient(mongo_uri)
db = client.bodymetrics
users_collection = db.user_info

groq_api = os.getenv("GROK_API")
if not groq_api:
      raise ValueError("Grok API key not properly initialized, please try again")

client = Groq(api_key=groq_api)

@app.route("/", methods = ["POST", "GET"])
def create():
      if request.method == "POST":
           height = request.form.get("height")
           weight = request.form.get("weight")
           plan = request.form.get("plan")
           workout = request.form.get("workout")
           users_collection.insert_one({"Height": height, "Weight": weight, "Plan": plan})
           chat_completion = client.chat.completions.create(
                messages=[
                     {
                          "role": "user",
                          "content": f"""You are a seasoned fitness trainer with 20+ years of experience.
                                         A client comes to you with the following body metrics:
                                         Height = {height}, Weight = {weight}, Plan = {plan}
                                         Today, they want to target the following muscle groups: {workout}
                                         Based on their height, weight, and current plan, please provide them a workout routine for the day.
                                         You must provide it in the following format:
                                         EXERCISE. NUMBER OF SETS sets. TARGET NUMBER OF REPS reps. NEWLINE
                                         Each exercise must be followed by a newline. Keep the formatting as simple and as clean as possible."""
                     }
                ], 
                model="llama-3.3-70b-versatile"
           )
           return chat_completion.choices[0].message.content
      return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
