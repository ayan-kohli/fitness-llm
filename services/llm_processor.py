from configs.config import groq_client
from services.helper import logger 

def generate_workout_llm_output(height, weight, plan, workout, activity):
    llm_prompt = f"""You are a seasoned fitness trainer with 20+ years of experience.
                A client comes to you with the following body metrics:
                Height = {height}, Weight = {weight}, Plan = {plan}, Activity Level = {activity}
                Today, they want to target the following muscle groups: {workout}
                Based on their height, weight, and current plan, please provide them a workout routine for the day.
                Respond only with JSON using this format (assume completion for all generated exercises, and 
                assume X = # of sets, Y and Z represent start and end point for range of reps):
                {{"exercise1": [X, Y, Z]}}
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
        return response, llm_prompt
    except Exception as e:
        logger.error(f"LLM error {e}", exc_info=True)
        return None, None

def generate_workout_with_rag(user_id, workout_targets):
    from services.user_services import read_user
    from services.metric_services import read_latest_height
    from services.workout_services import read_workouts_for_user
    from services.exercise_services import get_exercises_by_muscle_group

    user_info, user_ok = read_user(user_id)
    if not user_ok or not user_info:
        return None, "User not found"
    plan = user_info.get("plan", "")
    activity = user_info.get("activity_level", "")

    metrics, metrics_ok = read_latest_height(user_id)
    if not metrics_ok or not metrics:
        return None, "User metrics not found"
    height = metrics.get("height", "")
    weight = metrics.get("weight", "")

    from services.workout_services import read_workouts_for_user
    workout_history, wh_ok = read_workouts_for_user(user_id)
    if not wh_ok:
        workout_history = []

    last_workouts = workout_history[:3] if workout_history else []
    workout_summary = " | ".join([
        f"{w.get('date_generated', '')}: {w.get('muscles_targeted', '')}" for w in last_workouts
    ])

    all_exercises = []
    for muscle in workout_targets:
        exercises, ok = get_exercises_by_muscle_group(muscle)
        if ok and exercises:
            all_exercises.extend(exercises)

    seen = set()
    unique_exercises = []
    for ex in all_exercises:
        name = ex.get("exercise_name")
        if name and name not in seen:
            unique_exercises.append(ex)
            seen.add(name)

    exercise_context = "\n".join([
        f"{ex['exercise_name']} (Primary: {', '.join(ex['primary_muscle_group'])}; Equipment: {ex['equipment']}; Difficulty: {ex['difficulty']})"
        for ex in unique_exercises[:10]
    ])


    initial_prompt = f"""
You are a seasoned fitness trainer with 20+ years of experience.\n
A client comes to you with the following body metrics:\n
Height = {height}, Weight = {weight}, Plan = {plan}, Activity Level = {activity}\n
Today, they want to target the following muscle groups: {', '.join(workout_targets)}\n
Their last 3 workouts were: {workout_summary if workout_summary else 'N/A'}\n
Here are some exercises you can use:\n{exercise_context}\n
Based on their history, metrics, and plan, generate a JSON workout routine for the day.\nRespond only with JSON using this format (assume completion for all generated exercises, and assume X = # of sets, Y and Z represent start and end point for range of reps):\n{{"exercise1": [X, Y, Z]}}
"""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "user", "content": initial_prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        draft_response = chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM error (initial draft) {e}", exc_info=True)
        return None, "LLM error (initial draft)"

    refine_prompt = f"""
Refine the following workout for the user, considering their plan ({plan}), activity level ({activity}), and last 3 workouts ({workout_summary if workout_summary else 'N/A'}).\n
Workout draft: {draft_response}\n
Make sure to avoid overtraining the same muscle groups as previous days, and add variety if possible. Respond only with improved JSON.
"""
    try:
        chat_completion2 = groq_client.chat.completions.create(
            messages=[
                {"role": "user", "content": refine_prompt}
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        refined_response = chat_completion2.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM error (refinement) {e}", exc_info=True)
        return draft_response, "LLM error (refinement)"

    return refined_response, initial_prompt
