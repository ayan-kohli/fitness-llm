from flask import Flask, render_template, jsonify, request, redirect
from blueprints.main_bp.routes import routes_bp

app = Flask(__name__)
app.register_blueprint(routes_bp)
app.config['WTF_CSRF_ENABLED'] = False

if __name__ == "__main__":
    app.run(debug=True)
