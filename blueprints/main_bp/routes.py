from flask import Blueprint, render_template, request, jsonify
from configs.config import groq_client
from datetime import datetime
from services import user_services, metric_services, workout_services
from services.helper import logger
import json
from ast import literal_eval

routes_bp = Blueprint("routes", __name__)


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
               activity = request.form.get("activity")
               if activity not in ["Sedentary", "Lightly Active", "Active", "Extremely Active"]:
                    raise ValueError("Invalid activity level.")
          except ValueError as e:
               return jsonify({"Client-side error when inputting": str(e)}), 400

          curr_time = datetime.now()
          user_creation, success = user_services.create_user(curr_time, activity, plan)
          if success:
               user_id = user_creation["user_id"]
               metric_result, success = metric_services.create_metric(user_id, curr_time, height, weight)
               if success:
                    metric_id = metric_result["_id"]
               else:
                    return jsonify({"Server-side error": "Failed when creating user metrics"}), 500
          else:
               return jsonify({"Server-side error": "Failed when creating new user"}), 500
          
          llm_prompt = f"""You are a seasoned fitness trainer with 20+ years of experience.
                                         A client comes to you with the following body metrics:
                                         Height = {height}, Weight = {weight}, Plan = {plan}, Activity Level = {activity}
                                         Today, they want to target the following muscle groups: {workout}
                                         Based on their height, weight, and current plan, please provide them a workout routine for the day.
                                         Respond only with JSON using this format (assume completion for all generated exercises, and 
                                         assume X = # of sets, Y and Z represent start and end point for range of reps):
                                         '{{'exercise1:' '[X, Y, Z]'}}'
                                         """
          try:
               chat_completion = groq_client.chat.completions.create(
                    messages=[
                         {
                              "role": "user",
                              "content": llm_prompt
                         }
                    ], 
                    model="llama-3.3-70b-versatile",
                    response_format={"type": "json_object"}
               )
               response = chat_completion.choices[0].message.content
          except Exception as e:
               logger.error(f"LLM error {e}", exc_info=True)
               return jsonify({"LLM API Error": str(e)}), 500

          try:
               workout_dict = json.loads(response)
               if "error" in workout_dict:
                    error_message = workout_dict["error"].get("message", "Unknown LLM API error")
                    return jsonify({"LLM API Error": error_message}), 500
               workout_doc = []
               for k, v in workout_dict.items():
                    to_enter = {
                         "Exercise": "",
                         "Sets": 0,
                         "Rep Range": [0, 0]
                    }
                    try:
                         parsed_setreps = literal_eval(v.strip())

                         if isinstance(parsed_setreps, list) and len(parsed_setreps) == 3:
                              to_enter["Exercise"] = k
                              to_enter["Sets"] = parsed_setreps[0]
                              to_enter["Rep Range"] = [parsed_setreps[1], parsed_setreps[2]]
                         else:
                              logger.error(f"LLM returned unintended list when formatting exercise {k}: {v}. Parsed: {parsed_setreps}")
                              return jsonify({"LLM API Error": "Failed to parse exercises"}), 500
                    except Exception as e:
                         logger.error(f"Error {e} occurred when parsing LLM output")
                         return jsonify({"Server-side error": str(e)}), 500
                    workout_doc.append(to_enter)
               
               workout_result, success = workout_services.create_workout(user_id, datetime.now(), 
                                                                     workout, llm_prompt, response, workout_doc, "generated", None)
               if success:
                    workout_id = workout_result["_id"]
                    return jsonify({"Success": "Database input success!"}), 200
               else:
                    return jsonify({"Server-side error": "Failed when creating workout"}), 500
               
          except json.JSONDecodeError as e:
               return jsonify({"LLM error": str(e)}), 500
          except Exception as e:
               logger.critical(f"Critical error {e} occurred when creating workout")
               return jsonify({"Server-side error": str(e)}), 500
               

          
      return render_template("index.html")