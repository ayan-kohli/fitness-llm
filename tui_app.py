import requests
import json

print("Welcome to FitSense!")
print("To start, please enter your height (in inches)")

def height_input():
    try:
        height = int(input("> "))
        while height > 99 or height < 25:
            print("Unrealistic height - please try again!")
            height = int(input("> "))
    except ValueError as e:
        print("Your height doesn't seem right - are you sure it's an integer represented in inches?")
        height_input()
    return height
    
height = height_input()

print("Now, enter your weight (in pounds)")

def weight_input():
    try:
        weight = float(input("> "))
        while weight > 1000 or weight < 80:
            print("Unrealistic weight - please try again!")
            weight = float(input("> "))
    except ValueError as e:
        print("Your weight doesn't seem right - are you sure it's an integer represented in pounds?")
        weight_input()
    return weight
weight = weight_input()
    
print("Now, please select a plan! You have the following options (enter exactly as seen): ")
print("Standard Cut, Aggressive Cut, Lean Bulk, Dirty Bulk, Body Recomposition, Maintain")
plan = input("> ")
while plan.strip() not in ["Dirty Bulk", "Lean Bulk", "Standard Cut", "Aggressive Cut", "Body Recomposition","Maintain"]:
    print("Invalid plan - please try again!")
    plan = input("> ")

print("Now, please select your activity level! You have the following options (enter exactly as seen): ")
print("Sedentary, Lightly Active, Active, Extremely Active")
activity = input("> ")
while activity.strip() not in ["Sedentary", "Lightly Active", "Active", "Extremely Active"]:
    print("Invalid plan - please try again!")
    plan = input("> ")

print("Lastly, what muscle groups are you looking to target today?")
workout = input("> ")

FLASK_URL = "http://127.0.0.1:5000/"
payload = {
    "height": height,
    "weight": weight,
    "plan": plan,
    "activity": activity,
    "workout": workout
}

def generic_request_handling(req_callable, *args, **kwargs):
    try:
        response = req_callable(*args, **kwargs)
        return response
    except requests.exceptions.ConnectionError as e:
        print(f"Encountered a connection error: {e}")
        exit(0)
    except Exception as e:
        print(f"Encountered an unexpected error: {e}")
        exit(0)
        
def generic_response_handling(response): 
    try:
        if response.status_code == 204:
            return {}, response.status_code 

        response_data = response.json()
        return response_data, response.status_code 

    except json.JSONDecodeError:
        print("Error: Server returned non-JSON data or empty/malformed JSON.")
        print(f"Raw response content: {response.text}") 
        return {"error": "JSON decoding failed on client"}, response.status_code 
    except Exception as e: 
        print(f"An unexpected error occurred during response handling: {e}")
        return {"error": "Unexpected client-side response error"}, response.status_code

response = generic_request_handling(requests.post, FLASK_URL, data=payload)
response_data, status_code = generic_response_handling(response)

if status_code == 201:
    user_id = response_data.get("user_id") 
    print(f"User and workout created successfully! User ID: {user_id}")
    print(f"Workout: {json.dumps(response_data.get('workout', {}), indent=2)}")
elif status_code == 400:
    print(f"Client-side input error: {json.dumps(response_data, indent=2)}")
elif status_code == 500:
    print(f"Server-side error: {json.dumps(response_data, indent=2)}")
else:
    print(f"Unhandled status code {status_code}: {json.dumps(response_data, indent=2)}")

while True:
    print("Current MENU options: (1) Read Current User (2) Quit")
    choice = input("> ")
    if choice == "1":
        user_read = generic_request_handling(requests.get, FLASK_URL + f"users/{user_id}")
        response_data = generic_response_handling(user_read)
        print(response_data)
    elif choice == "2":
        print("Exiting app...")
        exit(0)
    else:
        print("Invalid choice. Try again! ")