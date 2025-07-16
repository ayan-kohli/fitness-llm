# FitSense: AI-Powered Fitness Planner

FitSense is an AI-powered fitness planning system that uses Retrieval Augmented Generation (RAG) and prompt chaining to generate personalized workout routines. It leverages user history, exercise data, and advanced language models to provide context-aware, refined workout plans.

## Features
- Personalized workout generation using LLMs
- Retrieval of user and exercise history for context
- Prompt chaining for workout refinement
- Command-line TUI for easy interaction
- Flask backend API

## Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/ayan-kohli/fitness-llm.git
cd fitness-llm
```

### 2. Install Dependencies
Create a virtual environment and install requirements:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Up Environment
- Configure your `.env` file with any required API keys or database settings.
- Initialize the database:
  ```bash
  python scripts/db_init.py
  python scripts/exercise_init.py
  ```

### 4. Run the Flask App
```bash
python app.py
```

### 5. Use the TUI (Terminal User Interface)
```bash
python tui_app.py
```
Follow the prompts to create users, record metrics, and generate AI-powered workouts.
