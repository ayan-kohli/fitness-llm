from flask import Flask
from blueprints.main_bp.main_routes import routes_bp

app = Flask(__name__)
app.register_blueprint(routes_bp)
app.config['WTF_CSRF_ENABLED'] = False

if __name__ == "__main__":
    app.run(debug=True)
