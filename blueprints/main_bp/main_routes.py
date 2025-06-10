from flask import Blueprint, render_template, request, jsonify
from configs.config import groq_client
from datetime import datetime
from services import user_services, metric_services, workout_services
from services.helper import logger
import json
from ast import literal_eval
from bcrypt import gensalt, hashpw
from blueprints.llm_bp.llm_routes import create_workout
import requests

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
          
          try:
               llm_response = requests.post(url="http://127.0.0.1:5000/generate", json = {
                    "height": height,
                    "weight": weight,
                    "plan": plan,
                    "workout": workout,
                    "activity": activity
               })
               llm_response.raise_for_status()
               response_data = llm_response.json()
               response = response_data.get("llm_response")
               llm_prompt = response_data.get("llm_prompt")       
          except requests.RequestException as e:
               logger.error(f"LLM error {e}", exc_info=True)
               if e.response is not None:
                    return jsonify({"LLM API Error": f"Request failed with status {e.response.status_code}: {e.response.text}"}), e.response.status_code
               else:
                    return jsonify({"LLM API Error": f"Connection failed: {str(e)}"}), 500

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
                              try: 
                                   sets = int(parsed_setreps[0])
                                   rep_min = int(parsed_setreps[1])
                                   rep_max = int(parsed_setreps[2])

                                   to_enter["Exercise"] = k
                                   to_enter["Sets"] = sets
                                   to_enter["Rep Range"] = [rep_min, rep_max]
                              except ValueError as ve:
                                   logger.error(f"LLM output values were not convertible to int for exercise {k}: {v}. Error: {ve}", exc_info=True)
                                   return jsonify({"LLM Parsing Error": "AI did not return numeric values"}), 500
                         else:
                              logger.error(f"LLM returned unintended list when formatting exercise {k}: {v}. Parsed: {parsed_setreps}")
                              return jsonify({"LLM API Error": "Failed to parse exercises"}), 500
                    except (ValueError, SyntaxError) as e:
                         logger.error(f"Error {e} occurred when parsing LLM output")
                         return jsonify({"LLM Parsing Error": "Could not parse exercises"}), 500
                    except Exception as e:
                         logger.error(f"Unexpected error {e} when parsing LLM", exc_info=True)
                         return jsonify({"Server-side error": "An unexpected error occurred when parsing exercises"}), 500

                    workout_doc.append(to_enter)
               
               workout_result, success = workout_services.create_workout(user_id, curr_time, 
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

@routes_bp.route("/users/<user_id>", methods=["GET"])
def read_user(user_id):
     result, success = user_services.read_user(user_id)
     if result and success:
          if "_id" in result:
               result["_id"] = str(result["_id"])
          if "Date Created" in result and result["Date Created"] is not None and isinstance(result["Date Created"], datetime):
               result["Date Created"] = result["Date Created"].isoformat() 
          if "Updated At" in result and result["Updated At"] is not None and isinstance(result["Updated At"], datetime):
               result["Updated At"] = result["Updated At"].isoformat() 
          return jsonify({"User Info": result}), 200
     else:
          return jsonify({"Database error": "User not found"}), 404

@routes_bp.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
     try:
          data = request.json
          if not data:
               return jsonify({"Client-side error": "Invalid or empty JSON data"}), 400
     except json.JSONDecodeError as e:
          logger.error(f"JSON decode error: {e}", exc_info=True)
          return jsonify({"Client-side error when inputting JSON data": str(e)}), 400

     result, success = user_services.read_user(user_id)
     if not success or result is None:
          return jsonify({"Database error": "User not found"}), 404

     updated_fields = {}
     timestamp = datetime.now()

     if "username" in data:
        new_username = data["username"]
        result, success = user_services.update_username(user_id, new_username, timestamp)
        if result and success:
             updated_fields["username"] = new_username
        elif success and not result:
          pass
        else:
             return jsonify({"Server-side error": "Could not process username"}), 500
     
     if "activity" in data:
        new_activity = data["activity"]
        result, success = user_services.update_activity(user_id, new_activity, timestamp)
        if result and success:
             updated_fields["activity"] = new_activity
        elif success and not result:
          pass
        else:
             return jsonify({"Server-side error": "Could not process activity"}), 500
     
     if "plan" in data:
        new_plan = data["plan"]
        result, success = user_services.update_plan(user_id, new_plan, timestamp)
        if result and success:
             updated_fields["plan"] = new_plan
        elif success and not result:
          pass
        else:
             return jsonify({"Server-side error": "Could not process plan"}), 500
     
     if "password" in data:
        new_password = data["password"]
        hash_salt = gensalt()
        pass_hash = str(hashpw(new_password, hash_salt))

        result, success = user_services.update_password(user_id, pass_hash, timestamp)
        if result and success:
             updated_fields["password"] = pass_hash
        elif success and not result:
          pass
        else:
             return jsonify({"Server-side error": "Could not process password"}), 500
     
     if updated_fields: 
        return jsonify({"updated_fields": updated_fields}), 200
     else:
        return jsonify({"message": "No valid fields provided or no changes detected"}), 200 

@routes_bp.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
	result, success = user_services.read_user(user_id)
	if not success or result is None:
		return jsonify({"Database error": "User not found"}), 404

	result, success = user_services.delete_user(user_id)
	if not success:
		return jsonify({"Database error": "Could not delete user"}), 500

	result, success = metric_services.delete_user_metrics(user_id)
	if not success:
		logger.error(f"Failed to delete metrics for user {user_id}. User record might be deleted, but metrics remain.")
		return jsonify({"Database error": "Could not delete metrics"}), 500

	result, success = workout_services.delete_user_workouts(user_id)
	if not success:
		logger.error(f"Failed to delete workouts for user {user_id}. User record might be deleted, but workouts remain.")
		return jsonify({"Database error": "Could not delete workouts"}), 500

	return jsonify({}), 204

 