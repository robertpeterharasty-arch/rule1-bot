import functions_framework
import os
import json
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# 1. LOAD SECRETS (From Google Cloud Variables)
# If these are missing, the bot will print an error in the logs
PUBLIC_KEY = os.environ.get('DISCORD_PUBLIC_KEY')

if not PUBLIC_KEY:
    raise ValueError("Missing DISCORD_PUBLIC_KEY environment variable")

# Initialize Security Tool
verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))

@functions_framework.http
def run_scanner(request):
    # 2. SECURITY CHECK (The Doorman)
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')
    body = request.data.decode('utf-8')

    if not signature or not timestamp:
        return 'Unauthorized', 401

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
    except BadSignatureError:
        return 'Invalid signature', 401

    # 3. INTERACTION HANDLER
    req = request.get_json()

    # TYPE 1: PING (The Handshake)
    if req['type'] == 1:
        return {'type': 1}

    # TYPE 2: COMMANDS (Slash Commands)
    if req['type'] == 2:
        command_name = req['data']['name']
        
        # HANDLE "/scan"
        if command_name == "scan":
            return {
                'type': 4,
                'data': {
                    'content': "🚀 **Scanning Market...** (This is a placeholder response using GitHub!)"
                }
            }

        # HANDLE "/add"
        if command_name == "add":
            stock = req['data']['options'][0]['value']
            return {
                'type': 4,
                'data': {
                    'content': f"✅ Added **{stock.upper()}** to the watchlist."
                }
            }

    return {'error': 'Unknown request'}
