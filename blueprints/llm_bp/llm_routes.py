from flask import Blueprint, jsonify, request
from configs.config import groq_client
from services.helper import logger

llm_bp = Blueprint("llm_routes", __name__)

@llm_bp.route("/generate", methods = ["POST"])
def create_workout():
    doc = request.json
    if not doc:
        return jsonify({"Client-side error": "Invalid or empty JSON data"}), 400
    height, weight, plan, activity, workout = doc["height"], doc["weight"], doc["plan"], doc["activity"], doc["workout"]
    llm_prompt = f"""You are a seasoned fitness trainer with 20+ years of experience.
                A client comes to you with the following body metrics:
                Height = {height}, Weight = {weight}, Plan = {plan}, Activity Level = {activity}
                Today, they want to target the following muscle groups: {workout}
                Based on their height, weight, and current plan, please provide them a workout routine for the day.
                Respond only with JSON using this format (assume completion for all generated exercises, and 
                assume X = # of sets, Y and Z represent start and end point for range of reps):
                {"exercise1": [sets, min_reps, max_reps]}
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
        return jsonify({"LLM error": "API connection failed"}), 500
    
    return jsonify({
    "llm_response": response,
    "llm_prompt": llm_prompt
    }), 200