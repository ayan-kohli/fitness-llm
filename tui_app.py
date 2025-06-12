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
        weight = int(input("> "))
        while weight > 1000 or weight < 80:
            print("Unrealistic weight - please try again!")
            weight = int(input("> "))
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

try:
    response = requests.post(FLASK_URL, data=payload)
except requests.exceptions.ConnectionError as e:
    print(f"Encountered a connection error: {e}")
    exit(0)
except Exception as e:
    print(f"Encountered an unexpected error: {e}")
    exit(0)

try:
    response_data = response.json()
except json.JSONDecodeError:
    print("Error when parsing server data.")
    exit(0)

print(f"Response: {json.dumps(response_data, indent=2)}")