import functions_framework
import os
import requests
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# 1. SETUP KEYS
PUBLIC_KEY = os.environ.get('DISCORD_PUBLIC_KEY')
BOT_TOKEN = os.environ.get('DISCORD_TOKEN')
APP_ID = os.environ.get('DISCORD_APP_ID')

if not PUBLIC_KEY or not BOT_TOKEN or not APP_ID:
    raise ValueError("Missing environment variables (Keys/Ids)")

verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))

@functions_framework.http
def run_scanner(request):
    # === THE INSTALLER LOGIC ===
    # If you visit this URL in a browser, it registers the commands!
    if request.method == 'GET':
        url = f"https://discord.com/api/v10/applications/{APP_ID}/commands"
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        
        commands = [
            {
                "name": "scan",
                "description": "Scans the watchlist for Rule #1 stocks",
                "type": 1
            },
            {
                "name": "add",
                "description": "Add a stock to the watchlist",
                "options": [{
                    "name": "symbol",
                    "description": "The stock ticker (e.g. NVDA)",
                    "type": 3,
                    "required": True
                }]
            }
        ]
        
        # Send to Discord
        logs = []
        for cmd in commands:
            r = requests.post(url, headers=headers, json=cmd)
            logs.append(f"Registered {cmd['name']}: {r.status_code} - {r.text}")
        
        return f"INSTALLATION REPORT:\n" + "\n".join(logs)

    # === STANDARD BOT LOGIC ===
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')
    body = request.data.decode('utf-8')

    if not signature or not timestamp:
        return 'Unauthorized', 401

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
    except BadSignatureError:
        return 'Invalid signature', 401

    req = request.get_json()
    if req['type'] == 1:
        return {'type': 1}
        
    return {'type': 4, 'data': {'content': "Bot is running!"}}
