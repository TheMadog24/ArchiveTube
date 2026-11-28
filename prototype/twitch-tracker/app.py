import os

from database.db import (
    get_api_usage_by_endpoint,
    get_api_usage_history,
    get_api_usage_summary,
    initialize_database,
)
from flask import Flask, jsonify, render_template, request
from twitch_api.client import search_channels

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    usage_summary = get_api_usage_summary()
    usage_by_endpoint = get_api_usage_by_endpoint("all")

    return render_template(
        "dashboard.html",
        usage_summary=usage_summary,
        usage_by_endpoint=usage_by_endpoint,
        active_page="dashboard",
    )


@app.route("/channels")
def channels():
    return render_template(
        "channels.html",
        active_page="channels",
    )


@app.route("/api/usage/history")
def api_usage_history():
    period = request.args.get("period", "24h")
    endpoint = request.args.get("endpoint")

    try:
        history = get_api_usage_history(period, endpoint)
    except ValueError:
        return jsonify({"error": "Invalid time period or endpoint."}), 400

    return jsonify(history)


@app.route("/api/usage/endpoints")
def api_usage_endpoints():
    period = request.args.get("period", "24h")

    try:
        endpoints = get_api_usage_by_endpoint(period)
    except ValueError:
        return jsonify({"error": "Invalid time period."}), 400

    return jsonify(endpoints)


@app.route("/api/channels/search")
def search_twitch_channels():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Please enter a channel name."}), 400

    try:
        client_id = os.getenv("TWITCH_CLIENT_ID")
        client_secret = os.getenv("TWITCH_CLIENT_SECRET")

        channels = search_channels(
            query,
            client_id,
            client_secret,
        )

        return jsonify(channels)

    except (RuntimeError, TimeoutError) as error:
        return jsonify({"error": str(error)}), 502


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=8080, debug=True)
