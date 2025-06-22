from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from services import user_services, metric_services, workout_services, exercise_services
from services.helper import logger
from services.llm_processor import generate_workout_llm_output
import json
from ast import literal_eval
from bcrypt import gensalt, hashpw
import uuid

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
               username = request.form.get("username")
               password = request.form.get("password")
               hash_salt = gensalt()
               password_bytes = password.encode('utf-8')
               pass_hash = str(hashpw(password_bytes, hash_salt))
          except ValueError as e:
               return jsonify({"Client-side error when inputting": str(e)}), 400

          curr_time = datetime.now()
          user_creation, success = user_services.create_user(curr_time, activity, plan, username, pass_hash)
          if success:
               user_id = user_creation["user_id"]
               metric_result, success = metric_services.create_metric(user_id, curr_time, height, weight)
               if success:
                    metric_id = metric_result["_id"]
               else:
                    return jsonify({"Server-side error": "Failed when creating user metrics"}), 500
          else:
               return jsonify({"Server-side error": "Failed when creating new user"}), 500

          response, llm_prompt = generate_workout_llm_output(height, weight, plan, workout, activity)
          if response is None:
               return jsonify({"Server-side error": "Failed to generate workout from AI"}), 500
          
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
                         parsed_setreps = v

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
                         logger.critical(f"Unexpected error {e} when parsing LLM", exc_info=True)
                         return jsonify({"Server-side error": "An unexpected error occurred when parsing exercises"}), 500

                    workout_doc.append(to_enter)
               
               workout_result, success = workout_services.create_workout(user_id, curr_time, 
                                                                     workout, llm_prompt, response, workout_doc, "generated", None)
               if success:
                    workout_id = workout_result["_id"]
                    return jsonify({"message": "Workout created successfully", "user_id": user_id, "workout_id": str(workout_id), "workout_details": workout_doc}), 201
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
          if "created_at" in result and result["created_at"] is not None and isinstance(result["created_at"], datetime):
               result["created_at"] = result["created_at"].isoformat() 
          if "updated_at" in result and result["updated_at"] is not None and isinstance(result["updated_at"], datetime):
               result["updated_at"] = result["updated_at"].isoformat() 
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

@routes_bp.route("/metrics", methods=["POST"])
def create_new_metric():
    try:
        data = request.json
        user_id = data.get("user_id")
        height = data.get("height")
        weight = data.get("weight")
        
        if not user_id or (height is None and weight is None):
            return jsonify({"Client-side error": "User ID and at least height or weight required."}), 400
        
        if height is not None:
            height = int(height)
        if weight is not None:
            weight = float(weight)

    except (ValueError, TypeError) as e:
        return jsonify({"Client-side error": f"Invalid data types for metrics: {e}"}), 400
    except json.JSONDecodeError as e:
        return jsonify({"Client-side error": f"Invalid JSON data: {e}"}), 400

    curr_time = datetime.now()
    metric_result, success = metric_services.create_metric(user_id, curr_time, height, weight)

    if success:
        return jsonify({"message": "Metric recorded successfully", "metric_id": str(metric_result["_id"])}), 201
    else:
        return jsonify({"Server-side error": "Failed to record new metric."}), 500

@routes_bp.route("/metrics/height/latest/<user_id>", methods=["GET"])
def get_latest_height(user_id):
    result, success = metric_services.read_latest_height(user_id)
    if result and success:
        if "_id" in result:
            result["metric_id"] = str(result["metric_id"])
        if "recorded_at" in result and isinstance(result["recorded_at"], datetime):
            result["recorded_at"] = result["recorded_at"].isoformat()
        if "user_id" in result and isinstance(result["user_id"], uuid.UUID):
            result["user_id"] = str(result["user_id"])
        return jsonify({"User Info": result}), 200
    else:
        return jsonify({"Database error": "Latest height not found for user."}), 404

@routes_bp.route("/metrics/weight/latest/<user_id>", methods=["GET"])
def get_latest_weight(user_id):
    result, success = metric_services.read_latest_weight(user_id)
    if result and success:
        if "metric_id" in result:
            result["metric_id"] = str(result["metric_id"])
        if "recorded_at" in result and isinstance(result["recorded_at"], datetime):
            result["recorded_at"] = result["recorded_at"].isoformat()
        if "user_id" in result and isinstance(result["user_id"], uuid.UUID):
            result["user_id"] = str(result["user_id"])
        return jsonify({"User Info": result}), 200
    else:
        return jsonify({"Database error": "Latest weight not found for user."}), 404

@routes_bp.route("/metrics/height/<user_id>", methods=["PUT"])
def update_user_height(user_id):
    try:
        data = request.json
        new_height = data.get("new_height")
        timestamp = data.get("timestamp")
        if new_height is None or not timestamp:
            return jsonify({"Client-side error": "New height and timestamp required."}), 400
        new_height = int(new_height)
        timestamp = datetime.fromisoformat(timestamp)
    except (ValueError, TypeError) as e:
        return jsonify({"Client-side error": f"Invalid data types: {e}"}), 400
    except json.JSONDecodeError as e:
        return jsonify({"Client-side error": f"Invalid JSON data: {e}"}), 400

    result, success = metric_services.update_height(user_id, new_height, timestamp)
    if success:
        return jsonify({"message": "Height updated successfully (new metric recorded).", "metric_id": str(result["_id"])}), 200
    else:
        return jsonify({"Server-side error": "Failed to update height."}), 500

@routes_bp.route("/metrics/weight/<user_id>", methods=["PUT"])
def update_user_weight(user_id):
    try:
        data = request.json
        new_weight = data.get("new_weight")
        timestamp = data.get("timestamp")
        if new_weight is None or not timestamp:
            return jsonify({"Client-side error": "New weight and timestamp required."}), 400
        new_weight = float(new_weight)
        timestamp = datetime.fromisoformat(timestamp)
    except (ValueError, TypeError) as e:
        return jsonify({"Client-side error": f"Invalid data types: {e}"}), 400
    except json.JSONDecodeError as e:
        return jsonify({"Client-side error": f"Invalid JSON data: {e}"}), 400

    result, success = metric_services.update_weight(user_id, new_weight, timestamp)
    if success:
        return jsonify({"message": "Weight updated successfully (new metric recorded).", "metric_id": str(result["_id"])}), 200
    else:
        return jsonify({"Server-side error": "Failed to update weight."}), 500

@routes_bp.route("/metrics/<user_id>", methods=["DELETE"])
def delete_all_user_metrics(user_id):
    result, success = metric_services.delete_user_metrics(user_id)
    if result and success:
        return jsonify({"message": "All metrics for user deleted."}), 204
    elif not result and success:
        return jsonify({"message": "No metrics found for user to delete."}), 204
    else:
        return jsonify({"Server-side error": "Failed to delete user metrics."}), 500

@routes_bp.route("/workouts/generate/<user_id>", methods=["POST"])
def generate_and_store_workout_for_user(user_id):
    try:
        data = request.json
        height = data.get("height")
        weight = data.get("weight")
        plan = data.get("plan")
        workout_target = data.get("workout")
        activity = data.get("activity")

        if not all([user_id, height, weight, plan, workout_target, activity]):
            return jsonify({"Client-side error": "Missing required fields for workout generation."}), 400
        if plan not in ["Dirty Bulk", "Lean Bulk", "Standard Cut", "Aggressive Cut", "Body Recomposition","Maintain"]:
             raise ValueError("Invalid plan type.")
        if activity not in ["Sedentary", "Lightly Active", "Active", "Extremely Active"]:
             raise ValueError("Invalid activity level.")

    except (ValueError, TypeError) as e:
        return jsonify({"Client-side error": f"Invalid data types or values: {e}"}), 400
    except json.JSONDecodeError as e:
        return jsonify({"Client-side error": f"Invalid JSON data: {e}"}), 400

    curr_time = datetime.now()

    response, llm_prompt = generate_workout_llm_output(height, weight, plan, workout_target, activity)
    if response is None:
        return jsonify({"Server-side error": "Failed to generate workout from AI."}), 500
    
    try:
        workout_dict = json.loads(response)
        if "error" in workout_dict:
            error_message = workout_dict["error"].get("message", "Unknown LLM API error")
            return jsonify({"LLM API Error": error_message}), 500
        
        workout_doc = []
        for k, v in workout_dict.items():
            to_enter = {
                "Exercise": k,
                "Sets": 0,
                "Rep Range": [0, 0]
            }
            if isinstance(v, list) and len(v) == 3:
                try:
                    sets = int(v[0])
                    rep_min = int(v[1])
                    rep_max = int(v[2])
                    to_enter["Sets"] = sets
                    to_enter["Rep Range"] = [rep_min, rep_max]
                except ValueError as ve:
                    logger.error(f"LLM output values not convertible to int for exercise {k}: {v}. Error: {ve}", exc_info=True)
                    return jsonify({"LLM Parsing Error": "AI did not return numeric values for sets/reps."}), 500
            else:
                logger.error(f"LLM returned unintended format for exercise {k}: {v}. Expected list of 3.", exc_info=True)
                return jsonify({"LLM Parsing Error": "Failed to parse exercises from AI output."}), 500
            workout_doc.append(to_enter)

        workout_result, success = workout_services.create_workout(
            user_id, curr_time, workout_target, llm_prompt, response, workout_doc, "generated", None
        )
        if success:
            workout_id = workout_result["_id"]
            return jsonify({"message": "Workout generated and stored successfully", "workout_id": str(workout_id), "workout_details": workout_doc}), 201
        else:
            return jsonify({"Server-side error": "Failed to store generated workout."}), 500

    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError parsing LLM response: {e}", exc_info=True)
        return jsonify({"LLM Parsing Error": "AI response was not valid JSON."}), 500
    except Exception as e:
        logger.critical(f"Critical error during workout generation/storage: {e}", exc_info=True)
        return jsonify({"Server-side error": "An unexpected error occurred during workout processing."}), 500

@routes_bp.route("/workouts/latest/<user_id>", methods=["GET"])
def get_latest_workout(user_id):
    result, success = workout_services.read_latest_workout_for_user(user_id)
    if result and success:
        return jsonify(result), 200
    else:
        return jsonify({"Database error": "No latest workout found for user."}), 404

@routes_bp.route("/workouts/user/<user_id>", methods=["GET"])
def get_all_workouts_for_user(user_id):
    result, success = workout_services.read_workouts_for_user(user_id)
    if result and success:
        return jsonify(result), 200
    else:
        return jsonify({"Database error": "No workouts found for user."}), 404

@routes_bp.route("/workouts/<workout_id>", methods=["GET"])
def get_workout_by_id(workout_id):
    result, success = workout_services.read_workout_by_id(workout_id)
    if result and success:
        return jsonify(result), 200
    else:
        return jsonify({"Database error": "Workout not found."}), 404

@routes_bp.route("/workouts/complete/<workout_id>", methods=["PUT"])
def mark_workout_completed(workout_id):
    curr_time = datetime.now()
    result, success = workout_services.complete_workout(workout_id, curr_time)
    if result and success:
        return jsonify({"message": "Workout marked as completed."}), 200
    elif success and not result:
        return jsonify({"message": "Workout not found or already completed."}), 200
    else:
        return jsonify({"Server-side error": "Failed to mark workout as completed."}), 500

@routes_bp.route("/workouts/<workout_id>", methods=["DELETE"])
def delete_single_workout(workout_id):
    result, success = workout_services.delete_workout_by_id(workout_id)
    if result and success:
        return jsonify({}), 204
    elif success and not result:
        return jsonify({"message": "Workout not found."}), 200
    else:
        return jsonify({"Server-side error": "Failed to delete workout."}), 500

@routes_bp.route("/workouts/user/<user_id>", methods=["DELETE"])
def delete_all_user_workouts(user_id):
    result, success = workout_services.delete_user_workouts(user_id)
    if result and success:
        return jsonify({}), 204
    elif success and not result:
        return jsonify({"message": "No workouts found for user to delete."}), 204
    else:
        return jsonify({"Server-side error": "Failed to delete user workouts."}), 500

@routes_bp.route("/exercises", methods=["POST"])
def create_exercise():
    try:
        data = request.json
        name = data.get("name")
        primary_muscle_group = data.get("primary_muscle_group")
        secondary_muscle_group = data.get("secondary_muscle_group")
        equipment = data.get("equipment")
        difficulty = data.get("difficulty")
        instructions = data.get("instructions")
        video_url = data.get("video_url")
        is_custom = data.get("is_custom", False)
        user_id = data.get("user_id_custom")

        if not all([name, primary_muscle_group, equipment, instructions]):
            return jsonify({"Client-side error": "Missing required exercise fields."}), 400
        
        if is_custom and not user_id:
            return jsonify({"Client-side error": "Custom exercise requires a user_id."}), 400
        
        if not is_custom:
            user_id = None
        
    except json.JSONDecodeError as e:
        return jsonify({"Client-side error": f"Invalid JSON data: {e}"}), 400
    except Exception as e:
        logger.error(f"Error parsing exercise data: {e}", exc_info=True)
        return jsonify({"Server-side error": "An unexpected error occurred while parsing exercise data."}), 500

    curr_time = datetime.now()
    result, success = exercise_services.create_exercise(
        name, primary_muscle_group, secondary_muscle_group, equipment, difficulty,
        instructions, video_url, is_custom, user_id, curr_time
    )

    if success:
        return jsonify({"message": "Exercise created successfully", "exercise_id": str(result["_id"])}), 201
    else:
        return jsonify({"Server-side error": "Failed to create exercise. Name might already exist."}), 500

@routes_bp.route("/exercises/<name>", methods=["GET"])
def get_exercise_by_name(name):
    result, success = exercise_services.read_exercise_by_name(name)
    if result and success:
        return jsonify(result), 200
    else:
        return jsonify({"Database error": "Exercise not found."}), 404