"""
Flask Web API + Admin Dashboard
Provides REST API and serves the frontend dashboard.
"""

from flask import Flask, jsonify, request, render_template, abort
from flask_cors import CORS
from database import (
    init_db, db_get_logs, db_get_stats, db_get_blocklist,
    db_add_domain, db_remove_domain, db_clear_logs,
    db_get_setting, db_set_setting
)
import os

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ─────────────────────────────────────────
# Stats API
# ─────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    return jsonify(db_get_stats())


# ─────────────────────────────────────────
# Query Logs API
# ─────────────────────────────────────────

@app.route("/api/logs")
def api_logs():
    limit = int(request.args.get("limit", 200))
    action = request.args.get("action")      # BLOCKED / ALLOWED
    search = request.args.get("search")
    logs = db_get_logs(limit=limit, filter_action=action, search=search)
    return jsonify(logs)


@app.route("/api/logs/clear", methods=["POST"])
def api_clear_logs():
    db_clear_logs()
    return jsonify({"success": True, "message": "Logs cleared"})


# ─────────────────────────────────────────
# Blocklist API
# ─────────────────────────────────────────

@app.route("/api/blocklist")
def api_blocklist():
    search = request.args.get("search")
    return jsonify(db_get_blocklist(search=search))


@app.route("/api/blocklist/add", methods=["POST"])
def api_add_domain():
    data = request.json or {}
    domain = data.get("domain", "").strip()
    category = data.get("category", "custom")
    reason = data.get("reason", "")

    if not domain:
        return jsonify({"success": False, "message": "Domain required"}), 400

    success, message = db_add_domain(domain, category, reason)
    return jsonify({"success": success, "message": message})


@app.route("/api/blocklist/remove/<int:domain_id>", methods=["DELETE"])
def api_remove_domain(domain_id):
    success, message = db_remove_domain(domain_id)
    return jsonify({"success": success, "message": message})


# ─────────────────────────────────────────
# Settings API
# ─────────────────────────────────────────

@app.route("/api/settings")
def api_settings():
    return jsonify({
        "sinkhole_enabled": db_get_setting("sinkhole_enabled"),
        "upstream_dns": db_get_setting("upstream_dns"),
    })


@app.route("/api/settings", methods=["POST"])
def api_update_settings():
    data = request.json or {}
    if "sinkhole_enabled" in data:
        db_set_setting("sinkhole_enabled", data["sinkhole_enabled"])
    if "upstream_dns" in data:
        db_set_setting("upstream_dns", data["upstream_dns"])
    return jsonify({"success": True})


# ─────────────────────────────────────────
# DNS Test (simulate a query check)
# ─────────────────────────────────────────

@app.route("/api/test")
def api_test():
    from database import db_is_blocked, db_log_query
    domain = request.args.get("domain", "").strip().lower()
    if not domain:
        return jsonify({"error": "domain parameter required"}), 400
    blocked = db_is_blocked(domain)
    action = "BLOCKED" if blocked else "ALLOWED"
    db_log_query(domain, "dashboard-test", action)
    return jsonify({
        "domain": domain,
        "action": action,
        "blocked": blocked
    })


if __name__ == "__main__":
    init_db()
    print("🚀 Dashboard running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
