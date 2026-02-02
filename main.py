import requests
import pandas as pd
import ta
import functions_framework

# CONFIGURATION
# Your Discord Webhook
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1467866367754633285/1YUrvsrr2r56IzemVYxqC0NFobpGgwW0oFoYlgZcdQnK3IezetxrxlspKkWAavBHen0W"

# PASTE YOUR FMP API KEY HERE:
API_KEY = "yb4uNgddC9qTm1rSybhtF5zxzgxFjCbv"

# Stocks to Watch
SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']

def get_rule1_analysis(symbol):
    """Checks ROIC > 10%"""
    try:
        url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}?period=annual&limit=5&apikey={API_KEY}"
        r = requests.get(url).json()
        if not r or len(r) < 5: return None
        return {'roic': r[0].get('roic', 0)}
    except: return None

def get_technicals(symbol):
    """Checks MACD and SMA"""
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?timeseries=100&apikey={API_KEY}"
        data = requests.get(url).json()
        if 'historical' not in data: return None
        df = pd.DataFrame(data['historical']).iloc[::-1]
        
        # Indicators
        macd = ta.trend.MACD(df['close'])
        
        # Check Signals
        last = df.iloc[-1]
        prev = df.iloc[-2]
        signals = []
        
        # MACD Bullish Crossover
        if macd.macd().iloc[-1] > macd.macd_signal().iloc[-1] and macd.macd().iloc[-2] < macd.macd_signal().iloc[-2]:
            signals.append("MACD Buy Signal")
        
        # Price > 10 SMA
        sma = ta.trend.SMAIndicator(df['close'], window=10).sma_indicator()
        if last['close'] > sma.iloc[-1] and prev['close'] < sma.iloc[-2]:
             signals.append("Price crossed above 10-day MA")
            
        return {'price': last['close'], 'signals': signals}
    except: return None

def send_discord(symbol, fin, tech):
    # Rule #1 Filter: Only alert if ROIC > 10%
    if fin['roic'] < 0.10: return
    
    color = 5763719 if tech['signals'] else 9807270
    desc = f"**Price:** ${tech['price']:.2f}\n**ROIC:** {fin['roic']*100:.1f}%\n"
    if tech['signals']: desc += "\n**🔔 SIGNALS:**\n" + "\n".join(tech['signals'])
    
    requests.post(DISCORD_WEBHOOK, json={"embeds": [{"title": f"Update: {symbol}", "description": desc, "color": color}]})

@functions_framework.http
def run_scanner(request):
    report = []
    for s in SYMBOLS:
        f = get_rule1_analysis(s)
        t = get_technicals(s)
        if f and t: 
            send_discord(s, f, t)
            report.append(f"{s}: OK")
    return "\n".join(report) if report else "No data"
