import os
import json
import requests
import yfinance as yf
import pandas as pd
import ta
from google.cloud import firestore
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# CONFIGURATION
# 1. Paste your DISCORD PUBLIC KEY here (from the Developer Portal)
DISCORD_PUBLIC_KEY = "93e020388fb344711e2fc871a7fe4fadd804dcb7c4cdf925aec20ebbfd294afa"

# 2. Setup Database
db = firestore.Client()
COLLECTION_NAME = "watchlist"

# 3. Setup Verification (Security)
verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))

def get_watchlist():
    """Reads the stock list from Firestore"""
    docs = db.collection(COLLECTION_NAME).stream()
    return [doc.id for doc in docs]

def add_stock(symbol):
    """Adds a stock to Firestore"""
    db.collection(COLLECTION_NAME).document(symbol.upper()).set({'added': True})
    return f"✅ Added {symbol.upper()} to watchlist."

def remove_stock(symbol):
    """Removes a stock from Firestore"""
    db.collection(COLLECTION_NAME).document(symbol.upper()).delete()
    return f"🗑️ Removed {symbol.upper()}."

def run_analysis():
    """Runs the scan on the Firestore list"""
    symbols = get_watchlist()
    if not symbols: return "Watchlist is empty! Use /add to add stocks."
    
    report = []
    for s in symbols:
        try:
            ticker = yf.Ticker(s)
            hist = ticker.history(period="6mo")
            if hist.empty: continue
            
            # Simple Logic: Price > 50-day SMA
            sma = ta.trend.SMAIndicator(hist['Close'], window=50).sma_indicator()
            price = hist['Close'].iloc[-1]
            
            if price > sma.iloc[-1]:
                report.append(f"**{s}**: ${price:.2f} (Bullish)")
        except:
            continue
            
    return "\n".join(report) if report else "No bullish signals found."

def verify_signature(request):
    """Verifies that the request came from Discord"""
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    body = request.data.decode("utf-8")
    
    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
    except BadSignatureError:
        return False
    return True

def run_scanner(request):
    # 1. Security Check (Discord requires this)
    if not verify_signature(request):
        return ("invalid request signature", 401)
    
    req = request.get_json()
    
    # 2. Handle "PING" (Discord checks if bot is alive)
    if req.get("type") == 1:
        return ({"type": 1}, 200)
    
    # 3. Handle Commands
    if req.get("type") == 2:
        command = req['data']['name']
        options = req['data'].get('options', [])
        
        # /add [symbol]
        if command == "add":
            symbol = options[0]['value']
            msg = add_stock(symbol)
            return ({"type": 4, "data": {"content": msg}}, 200)
            
        # /remove [symbol]
        elif command == "remove":
            symbol = options[0]['value']
            msg = remove_stock(symbol)
            return ({"type": 4, "data": {"content": msg}}, 200)
            
        # /list
        elif command == "list":
            stocks = get_watchlist()
            msg = f"👀 Watchlist: {', '.join(stocks)}" if stocks else "Watchlist is empty."
            return ({"type": 4, "data": {"content": msg}}, 200)
            
        # /scan
        elif command == "scan":
            # Respond immediately (scanning takes time)
            # Note: For long scans, we need deferred responses, but let's keep it simple first.
            report = run_analysis()
            return ({"type": 4, "data": {"content": f"🔎 **Scan Results:**\n{report}"}}, 200)

    return ({"error": "unknown command"}, 400)
