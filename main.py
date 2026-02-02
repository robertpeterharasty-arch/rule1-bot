import functions_framework
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import json

# CONFIGURATION
# PASTE YOUR PUBLIC KEY FROM DISCORD DEVELOPER PORTAL HERE:
DISCORD_PUBLIC_KEY = "93e020388fb344711e2fc871a7fe4fadd804dcb7c4cdf925aec20ebbfd294afa"

# Initialize Security Tool
verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))

@functions_framework.http
def run_scanner(request):
    # 1. Verify the Request is from Discord (Security Check)
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')
    body = request.data.decode('utf-8')

    if not signature or not timestamp:
        return 'Unauthorized', 401

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
    except BadSignatureError:
        return 'Invalid signature', 401

    # 2. Handle the "Handshake" (PING)
    req = request.get_json()
    if req['type'] == 1:
        return {'type': 1}

    # 3. Handle Commands (e.g., /add NVDA)
    # We will build this out fully next, but this keeps the bot alive.
    return {'type': 4, 'data': {'content': "✅ Command received! (Logic coming soon)"}}
