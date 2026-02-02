import yfinance as yf
import pandas as pd
import ta
import requests
import functions_framework

# CONFIGURATION
# Your Discord Webhook (I kept yours here)
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1467866367754633285/1YUrvsrr2r56IzemVYxqC0NFobpGgwW0oFoYlgZcdQnK3IezetxrxlspKkWAavBHen0W"

# Stocks to Watch
SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

def get_analysis(symbol):
    try:
        # Fetch data from Yahoo Finance (No Key Needed)
        ticker = yf.Ticker(symbol)
        
        # 1. Get Financials (Using ROE as a proxy for ROIC)
        info = ticker.info
        roe = info.get('returnOnEquity', 0)
        
        # 2. Get Price Data (Last 6 months)
        history = ticker.history(period="6mo")
        if history.empty: return None
        
        # Indicators
        macd = ta.trend.MACD(history['Close'])
        
        # Check Signals
        signals = []
        
        # MACD Bullish Crossover
        if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] and macd.macd().iloc[-2] < macd.macd_signal().iloc[-2]:
            signals.append("MACD Buy Signal")
            
        return {'price': history['Close'].iloc[-1], 'roe': roe, 'signals': signals}
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def send_discord(symbol, data):
    # Filter: Only alert if ROE is decent (> 10%)
    if data['roe'] < 0.10: return
    
    color = 5763719 if data['signals'] else 9807270
    desc = f"**Price:** ${data['price']:.2f}\n**ROE:** {data['roe']*100:.1f}%\n"
    if data['signals']: desc += "\n**🔔 SIGNALS:**\n" + "\n".join(data['signals'])
    
    requests.post(DISCORD_WEBHOOK, json={"embeds": [{"title": f"Update: {symbol}", "description": desc, "color": color}]})

@functions_framework.http
def run_scanner(request):
    report = []
    for s in SYMBOLS:
        data = get_analysis(s)
        if data: 
            send_discord(s, data)
            report.append(f"{s}: OK (${data['price']:.2f})")
        else:
            report.append(f"{s}: Failed")
            
    return "\n".join(report)
