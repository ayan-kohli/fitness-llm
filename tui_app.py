import requests
import json
from datetime import datetime

FLASK_URL = "http://127.0.0.1:5000/"
current_user_id = None 

def generic_request_handling(method_callable, url, data_payload=None, json_payload=None):
    try:
        if data_payload:
            response = method_callable(url, data=data_payload)
        elif json_payload:
            response = method_callable(url, json=json_payload)
        else:
            response = method_callable(url)
        return response
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Connection to Flask API failed. Is the server running at {FLASK_URL}? Details: {e}")
        exit(1) 
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during request: {e}")
        exit(1) 

def generic_response_handling(response):
    try:
        if response.status_code == 204:
            return {}, 204 

        response_data = response.json()
        return response_data, response.status_code
    except json.JSONDecodeError:
        print(f"ERROR: Server returned non-JSON data or empty/malformed JSON (Status: {response.status_code}).")
        print(f"Raw response content: {response.text}")
        return {"error": "JSON decoding failed on client"}, response.status_code
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during response handling: {e}")
        return {"error": "Unexpected client-side response error"}, 500

def display_response(response_data, status_code, success_message="Operation successful."):
    if 200 <= status_code < 300: 
        if status_code == 204:
            print(f"SUCCESS (Status {status_code}): {success_message}")
        else:
            print(f"SUCCESS (Status {status_code}): {success_message}")
            if response_data:
                print(json.dumps(response_data, indent=2))
    else: 
        print(f"ERROR (Status {status_code}):")
        if response_data and isinstance(response_data, dict):
            print(json.dumps(response_data, indent=2))
        else:
            print(response_data)

def format_workout_display(workout_details):
    if not workout_details:
        return "No workout details provided."

    display_str = "\n--- Generated Workout Routine ---\n"
    for i, exercise in enumerate(workout_details):
        exercise_name = exercise.get("Exercise", "N/A")
        sets = exercise.get("Sets", "N/A")
        rep_range = exercise.get("Rep Range", "N/A")

        if isinstance(rep_range, list) and len(rep_range) == 2:
            reps_str = f"{rep_range[0]}-{rep_range[1]} reps"
        else:
            reps_str = f"{rep_range} reps" 

        display_str += f"{i+1}. {exercise_name}: {sets} sets of {reps_str}\n"
    display_str += "---------------------------------\n"
    return display_str

def _get_user_info_input():
    username = input("Enter Username (optional): ").strip()
    password = input("Enter Password (optional, will be hashed): ").strip()
    height = int(input("Enter Height (inches): ")) 
    weight = float(input("Enter Weight (pounds): "))
    
    plan_options = ["Dirty Bulk", "Lean Bulk", "Standard Cut", "Aggressive Cut", "Body Recomposition", "Maintain"]
    plan = input(f"Enter Plan {plan_options}: ").strip()
    while plan not in plan_options:
        plan = input(f"Invalid plan. Enter Plan {plan_options}: ").strip()

    activity_options = ["Sedentary", "Lightly Active", "Active", "Extremely Active"]
    activity = input(f"Enter Activity Level {activity_options}: ").strip()
    while activity not in activity_options:
        activity = input(f"Invalid activity level. Enter Activity Level {activity_options}: ").strip()
    
    workout_target = input("What muscle groups are you looking to target today for initial workout generation? ").strip()

    return username, password, height, weight, plan, activity, workout_target

def _get_user_update_data():
    update_payload = {}
    print("\nEnter new values (leave blank to keep current):")
    
    new_username = input("New Username: ").strip()
    if new_username: update_payload["username"] = new_username

    new_password = input("New Password: ").strip()
    if new_password: update_payload["password"] = new_password

    plan_options = ["Dirty Bulk", "Lean Bulk", "Standard Cut", "Aggressive Cut", "Body Recomposition", "Maintain"]
    new_plan = input(f"New Plan {plan_options} (or blank): ").strip()
    if new_plan:
        if new_plan not in plan_options:
            print("Invalid plan. Not updating.")
        else:
            update_payload["plan"] = new_plan

    activity_options = ["Sedentary", "Lightly Active", "Active", "Extremely Active"]
    new_activity = input(f"New Activity Level {activity_options} (or blank): ").strip()
    if new_activity:
        if new_activity not in activity_options:
            print("Invalid activity level. Not updating.")
        else:
            update_payload["activity"] = new_activity
            
    return update_payload

def _get_metric_creation_data():
    height = None
    weight = None
    try:
        h_str = input("Enter Height (inches, leave blank to skip): ").strip()
        if h_str: height = int(h_str)
        w_str = input("Enter Weight (pounds, leave blank to skip): ").strip()
        if w_str: weight = float(w_str)
    except ValueError:
        print("Invalid numerical input for height/weight. Skipping.")
    
    if height is None and weight is None:
        return None 
    return {"height": height, "weight": weight}

def _get_exercise_data(is_custom_bool):
    name = input("Exercise Name: ").strip()
    primary_muscle_group = input("Primary Muscle Group: ").strip()
    secondary_muscle_group = input("Secondary Muscle Group (optional): ").strip() or None
    equipment = input("Equipment: ").strip()
    difficulty = input("Difficulty (optional): ").strip() or None
    instructions = input("Instructions: ").strip()
    video_url = input("Video URL (optional): ").strip() or None

    return {
        "name": name,
        "primary_muscle_group": primary_muscle_group,
        "secondary_muscle_group": secondary_muscle_group,
        "equipment": equipment,
        "difficulty": difficulty,
        "instructions": instructions,
        "video_url": video_url,
        "is_custom": is_custom_bool,
        "user_id_custom": current_user_id if is_custom_bool else None,
        "created_at": datetime.now().isoformat() 
    }

def create_user_and_initial_workout():
    global current_user_id
    print("\n--- Create New User & Generate Initial Workout ---")
    username, password, height, weight, plan, activity, workout_target = _get_user_info_input()

    payload = {
        "username": username,
        "password": password,
        "height": height,
        "weight": weight,
        "plan": plan,
        "activity": activity,
        "workout": workout_target
    }

    response = generic_request_handling(requests.post, FLASK_URL, data_payload=payload)
    response_data, status_code = generic_response_handling(response)

    if status_code == 201:
        current_user_id = response_data.get("user_id")
        display_response(response_data, status_code, "User and initial workout created successfully!")
    else:
        display_response(response_data, status_code, "Failed to create user or initial workout.")

def read_user_profile(user_id_to_read=None):
    if user_id_to_read is None:
        user_id_to_read = current_user_id
        if not user_id_to_read:
            print("No user selected. Please create or select a user first.")
            return

    print(f"\n--- Reading User Profile for ID: {user_id_to_read} ---")
    response = generic_request_handling(requests.get, FLASK_URL + f"users/{user_id_to_read}")
    response_data, status_code = generic_response_handling(response)
    display_response(response_data, status_code, "User profile retrieved.")
    return response_data, status_code

def update_user_profile():
    if not current_user_id:
        print("No user selected. Please create or select a user first.")
        return

    print(f"\n--- Updating User Profile for ID: {current_user_id} ---")
    update_payload = _get_user_update_data()
    if not update_payload:
        print("No valid fields provided for update.")
        return

    response = generic_request_handling(requests.put, FLASK_URL + f"users/{current_user_id}", json_payload=update_payload)
    response_data, status_code = generic_response_handling(response)
    display_response(response_data, status_code, "User profile updated.")

def delete_user_profile():
    global current_user_id
    if not current_user_id:
        print("No user selected. Please create or select a user first.")
        return

    confirm = input(f"Are you sure you want to delete user {current_user_id} and ALL their data? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("User deletion cancelled.")
        return

    print(f"\n--- Deleting User Profile for ID: {current_user_id} ---")
    response = generic_request_handling(requests.delete, FLASK_URL + f"users/{current_user_id}")
    response_data, status_code = generic_response_handling(response)
    display_response(response_data, status_code, "User and all associated data deleted successfully.")
    if status_code == 204: 
        current_user_id = None 

def manage_metrics():
    if not current_user_id:
        print("No user selected. Please create or select a user first.")
        return

    while True:
        print(f"\n--- Metric Management for User: {current_user_id[:8]}... ---")
        print("1. Record New Metrics (Height/Weight)")
        print("2. Update Height (creates new record)")
        print("3. Update Weight (creates new record)")
        print("4. View Latest Metrics")
        print("5. Delete All User Metrics")
        print("0. Back to Main Menu")
        choice = input("Enter choice: ").strip()

        if choice == '1':
            metric_data = _get_metric_creation_data()
            if metric_data:
                payload = {
                    "user_id": current_user_id,
                    "timestamp": datetime.now().isoformat(),
                    "height": metric_data.get("height"),
                    "weight": metric_data.get("weight")
                }
                response = generic_request_handling(requests.post, FLASK_URL + "metrics", json_payload=payload) # Assuming /metrics POST endpoint
                response_data, status_code = generic_response_handling(response)
                display_response(response_data, status_code, "New metrics recorded.")
        elif choice == '2':
            try:
                new_h = int(input("Enter new height (inches): "))
                payload = {"new_height": new_h, "timestamp": datetime.now().isoformat()}
                response = generic_request_handling(requests.put, FLASK_URL + f"metrics/height/{current_user_id}", json_payload=payload) # Assuming /metrics/height/{user_id} PUT
                response_data, status_code = generic_response_handling(response)
                display_response(response_data, status_code, "Height updated (new metric record created).")
            except ValueError: print("Invalid input.")
        elif choice == '3':
            try:
                new_w = float(input("Enter new weight (pounds): "))
                payload = {"new_weight": new_w, "timestamp": datetime.now().isoformat()}
                response = generic_request_handling(requests.put, FLASK_URL + f"metrics/weight/{current_user_id}", json_payload=payload) 
                response_data, status_code = generic_response_handling(response)
                display_response(response_data, status_code, "Weight updated (new metric record created).")
            except ValueError: print("Invalid input.")
        elif choice == '4':
            response_h = generic_request_handling(requests.get, FLASK_URL + f"metrics/height/latest/{current_user_id}")
            data_h, status_h = generic_response_handling(response_h)
            response_w = generic_request_handling(requests.get, FLASK_URL + f"metrics/weight/latest/{current_user_id}") 
            data_w, status_w = generic_response_handling(response_w)
            
            print("\n--- Latest Metrics ---")
            if status_h == 200 and data_h.get("User Info"):
                 print(f"Height: {data_h['User Info'].get('height', 'N/A')} recorded at {data_h['User Info'].get('recorded_at', 'N/A')}")
            else:
                print(f"Height: Not found ({data_h.get('error', 'N/A')})")
            
            if status_w == 200 and data_w.get("User Info"):
                 print(f"Weight: {data_w['User Info'].get('weight', 'N/A')} recorded at {data_w['User Info'].get('recorded_at', 'N/A')}")
            else:
                print(f"Weight: Not found ({data_w.get('error', 'N/A')})")

        elif choice == '5':
            confirm = input(f"Delete ALL metrics for user {current_user_id[:8]}...? (yes/no): ").strip().lower()
            if confirm == 'yes':
                response = generic_request_handling(requests.delete, FLASK_URL + f"metrics/{current_user_id}") 
                response_data, status_code = generic_response_handling(response)
                display_response(response_data, status_code, "All user metrics deleted.")
            else:
                print("Deletion cancelled.")
        elif choice == '0':
            break
        else:
            print("Invalid choice. Try again.")

def manage_workouts():
    if not current_user_id:
        print("No user selected. Please create or select a user first.")
        return

    while True:
        print(f"\n--- Workout Management for User: {current_user_id[:8]}... ---")
        print("1. Generate New Workout (using LLM)")
        print("2. View Latest Workout")
        print("3. View All Workouts for User")
        print("4. View Specific Workout by ID")
        print("5. Mark Workout as Completed")
        print("6. Delete Specific Workout by ID")
        print("7. Delete All User Workouts")
        print("0. Back to Main Menu")
        choice = input("Enter choice: ").strip()

        if choice == '1':
            if not current_user_id:
                print("No user selected. Please create or select a user first.")
                return
            
            workout_target = input("What muscle groups are you looking to target today? ").strip()
            response_h = generic_request_handling(requests.get, FLASK_URL + f"metrics/height/latest/{current_user_id}")
            data_h, status_h = generic_response_handling(response_h)
            response_w = generic_request_handling(requests.get, FLASK_URL + f"metrics/weight/latest/{current_user_id}") 
            data_w, status_w = generic_response_handling(response_w)
            
            if status_h == 200 and data_h.get("User Info"):
                 h = data_h['User Info'].get('height', 'N/A')
            else:
                print(f"Height: Not found ({data_h.get('error', 'N/A')})")
            
            if status_w == 200 and data_w.get("User Info"):
                 w = data_w['User Info'].get('weight', 'N/A')
            else:
                print(f"Weight: Not found ({data_w.get('error', 'N/A')})")
            
            user_data = read_user_profile(current_user_id).get("User Info")
            p = user_data.get("plan")
            a = user_data.get("activity")
            
            _, _, h, w, p, a, _ = _get_user_info_input() 

            payload = {
                "height": h, "weight": w, "plan": p,
                "activity": a, "workout": workout_target
            }
            response = generic_request_handling(requests.post, FLASK_URL + f"workouts/generate/{current_user_id}", json_payload=payload) 
            response_data, status_code = generic_response_handling(response)

            if status_code == 201: 
                display_response(response_data, status_code, "Workout generated and stored successfully!")
            else:
                display_response(response_data, status_code, "Failed to generate and store workout.")

        elif choice == '2':
            response = generic_request_handling(requests.get, FLASK_URL + f"workouts/latest/{current_user_id}") 
            response_data, status_code = generic_response_handling(response)
            if status_code == 200 and response_data.get("parsed_workout"):
                print(format_workout_display(response_data["parsed_workout"]))
            else:
                display_response(response_data, status_code, "No latest workout found.")
        elif choice == '3':
            response = generic_request_handling(requests.get, FLASK_URL + f"workouts/user/{current_user_id}") 
            response_data, status_code = generic_response_handling(response)
            if status_code == 200 and response_data:
                for i, workout in enumerate(response_data):
                    print(f"\n--- Workout {i+1} (ID: {workout.get('workout_id', 'N/A')}) ---")
                    if workout.get("parsed_workout"):
                        print(format_workout_display(workout["parsed_workout"]))
                    else:
                        print("No parsed workout details.")
            else:
                display_response(response_data, status_code, "No workouts found for user.")
        elif choice == '4':
            workout_id = input("Enter Workout ID to view: ").strip()
            response = generic_request_handling(requests.get, FLASK_URL + f"workouts/{workout_id}") 
            response_data, status_code = generic_response_handling(response)
            if status_code == 200 and response_data.get("parsed_workout"):
                print(format_workout_display(response_data["parsed_workout"]))
            else:
                display_response(response_data, status_code, "Workout not found.")
        elif choice == '5':
            workout_id = input("Enter Workout ID to mark as completed: ").strip()
            payload = {"timestamp": datetime.now().isoformat()}
            response = generic_request_handling(requests.put, FLASK_URL + f"workouts/complete/{workout_id}", json_payload=payload) 
            response_data, status_code = generic_response_handling(response)
            display_response(response_data, status_code, "Workout marked as completed.")
        elif choice == '6':
            workout_id = input("Enter Workout ID to delete: ").strip()
            response = generic_request_handling(requests.delete, FLASK_URL + f"workouts/{workout_id}") 
            response_data, status_code = generic_response_handling(response)
            display_response(response_data, status_code, "Workout deleted.")
        elif choice == '7':
            confirm = input(f"Delete ALL workouts for user {current_user_id[:8]}...? (yes/no): ").strip().lower()
            if confirm == 'yes':
                response = generic_request_handling(requests.delete, FLASK_URL + f"workouts/user/{current_user_id}") 
                response_data, status_code = generic_response_handling(response)
                display_response(response_data, status_code, "All user workouts deleted.")
            else:
                print("Deletion cancelled.")
        elif choice == '0':
            break
        else:
            print("Invalid choice. Try again.")

def manage_exercises():
    if not current_user_id:
        print("No user selected. Please create or select a user first.")
        return

    while True:
        print(f"\n--- Exercise Management for User: {current_user_id[:8]}... ---")
        print("1. Create Custom Exercise")
        print("2. Lookup Exercise by Name")
        print("0. Back to Main Menu")
        choice = input("Enter choice: ").strip()

        if choice == '1':
            print("\n--- Create Custom Exercise ---")
            exercise_data = _get_exercise_data(is_custom_bool=True)
            response = generic_request_handling(requests.post, FLASK_URL + "exercises", json_payload=exercise_data) 
            response_data, status_code = generic_response_handling(response)
            display_response(response_data, status_code, "Custom exercise created.")
        elif choice == '2':
            name = input("Enter Exercise Name to lookup: ").strip()
            response = generic_request_handling(requests.get, FLASK_URL + f"exercises/{name}") 
            response_data, status_code = generic_response_handling(response)
            display_response(response_data, status_code, "Exercise lookup result.")
        elif choice == '0':
            break
        else:
            print("Invalid choice. Try again.")

def main_menu():
    global current_user_id
    while True:
        print("\n===== FitSense Main Menu =====")
        if current_user_id:
            print(f"Active User ID: {current_user_id[:8]}...")
        else:
            print("No Active User.")
        print("1. Create New User & Initial Workout")
        print("2. Read Active User Profile")
        print("3. Update Active User Profile")
        print("4. Delete Active User Profile")
        print("5. Manage Metrics (Active User)")
        print("6. Manage Workouts (Active User)")
        print("7. Manage Exercises (Active User)")
        print("8. Select Existing User (by ID)")
        print("0. Exit")
        
        choice = input("Enter choice: ").strip()

        if choice == '1':
            create_user_and_initial_workout()
        elif choice == '2':
            read_user_profile()
        elif choice == '3':
            update_user_profile()
        elif choice == '4':
            delete_user_profile()
        elif choice == '5':
            manage_metrics()
        elif choice == '6':
            manage_workouts()
        elif choice == '7':
            manage_exercises()
        elif choice == '8':
            user_id_to_select = input("Enter User ID to select: ").strip()
            response_data, status_code = read_user_profile(user_id_to_select) 
            if status_code == 200:
                current_user_id = user_id_to_select
                print(f"User {current_user_id[:8]}... selected.")
            else:
                print("User not found or unable to select.")
        elif choice == '0':
            print("Exiting FitSense. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()