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
