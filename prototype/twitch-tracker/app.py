import os

from database.db import (
    add_channel,
    get_api_usage_by_endpoint,
    get_api_usage_history,
    get_api_usage_summary,
    get_channel,
    get_channels,
    initialize_database,
    remove_channel,
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


@app.route("/channels/<int:channel_id>")
def channel_detail(channel_id):
    channel = get_channel(channel_id)

    if channel is None:
        return "Channel not found.", 404

    return render_template(
        "channel.html",
        channel=channel,
        active_page="channels",
    )


@app.route("/channels/<int:channel_id>/manage")
def manage_channel(channel_id):
    channel = get_channel(channel_id)

    if channel is None:
        return "Channel not found.", 404

    return render_template(
        "channel_manage.html",
        channel=channel,
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


@app.route("/api/channels", methods=["POST"])
def create_channel():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid request data."}), 400

    twitch_user_id = data.get("id")
    username = data.get("broadcaster_login")
    display_name = data.get("display_name")
    profile_image_url = data.get("thumbnail_url")

    if not twitch_user_id or not username or not display_name:
        return jsonify({"error": "Missing required channel information."}), 400

    added = add_channel(
        twitch_user_id=twitch_user_id,
        username=username,
        display_name=display_name,
        profile_image_url=profile_image_url,
    )

    if not added:
        return jsonify({"error": "This channel is already in your library."}), 409

    return jsonify(
        {
            "success": True,
            "message": "Channel added to your library.",
        }
    ), 201


@app.route("/api/channels")
def list_channels():
    channels = get_channels()
    return jsonify(channels)


@app.route("/api/channels/<int:channel_id>", methods=["DELETE"])
def delete_channel(channel_id):
    removed = remove_channel(channel_id)

    if not removed:
        return jsonify({"error": "Channel not found in your library."}), 404

    return jsonify(
        {
            "success": True,
            "message": "Channel removed from your library.",
        }
    )


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=8080, debug=True)
