from flask import Flask
from blueprints.main_bp.main_routes import routes_bp
from blueprints.llm_bp.llm_routes import llm_bp

app = Flask(__name__)
app.register_blueprint(routes_bp)
app.register_blueprint(llm_bp)
app.config['WTF_CSRF_ENABLED'] = False

if __name__ == "__main__":
    app.run(debug=True)
