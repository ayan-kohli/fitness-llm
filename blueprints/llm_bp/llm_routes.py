from flask import Blueprint, jsonify, request
from configs.config import groq_client
from services.helper import logger
from services.llm_processor import generate_workout_with_rag

llm_bp = Blueprint("llm_routes", __name__)

@llm_bp.route("/generate", methods = ["POST"])
def create_workout():
    doc = request.json
    if not doc:
        return jsonify({"Client-side error": "Invalid or empty JSON data"}), 400
    user_id = doc.get("user_id")
    workout = doc.get("workout")
    if not user_id or not workout or not isinstance(workout, list):
        return jsonify({"Client-side error": "user_id and workout (list of muscle groups) required"}), 400

    response, prompt = generate_workout_with_rag(user_id, workout)
    if response is None:
        return jsonify({"error": prompt}), 500
    return jsonify({
        "llm_response": response,
        "llm_prompt": prompt
    }), 200