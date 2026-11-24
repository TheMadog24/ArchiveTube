
from flask import Flask, render_template
from database.db import initialize_database

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=8080, debug=True)
