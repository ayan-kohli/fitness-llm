from flask import Blueprint, render_template, request, jsonify
from configs.config import mongo_client, groq_client
routes_bp = Blueprint("routes", __name__)

metrics_db = mongo_client.bodymetrics
users_collection = metrics_db.user_info

workout_db = mongo_client.workout_history
workouts_collection = workout_db.workouts


@routes_bp.route("/", methods = ["POST", "GET"])
def create():
      if request.method == "POST":
          try:
               height = int(request.form.get("height"))
               weight = float(request.form.get("weight"))
               plan = request.form.get("plan")
               if plan not in ["Dirty Bulk", "Lean Bulk", "Standard Cut", "Aggressive Cut", "Body Recomposition","Maintain"]:
                    raise ValueError("Invalid plan type.")
               workout = request.form.get("workout")
          except ValueError as e:
               return jsonify({"error": str(e)}), 400
          
          chat_completion = groq_client.chat.completions.create(
                messages=[
                     {
                          "role": "user",
                          "content": f"""You are a seasoned fitness trainer with 20+ years of experience.
                                         A client comes to you with the following body metrics:
                                         Height = {height}, Weight = {weight}, Plan = {plan}
                                         Today, they want to target the following muscle groups: {workout}
                                         Based on their height, weight, and current plan, please provide them a workout routine for the day.
                                         Respond only with JSON using this format (assume completion for all generated exercises, and 
                                         assume X = # of sets, Y and Z represent start and end point for range of reps):
                                         '{{'exercise1:' '[X, Y, Z]'}}'
                                         """
                     }
                ], 
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
          )
          response = chat_completion.choices[0].message.content
          insertion_id = users_collection.insert_one({"Height": height, "Weight": weight, "Plan": plan}).inserted_id
          # add advanced json parsing for day 2
          workouts_collection.insert_one({"User": insertion_id, "Muscle Groups": workout, "Suggested Workout": response})
          return response
      return render_template("index.html")