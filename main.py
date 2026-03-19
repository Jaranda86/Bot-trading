import time
import requests
import threading
from flask import Flask

from iqoptionapi.stable_api import IQ_Option
import pandas as pd

# ===== CONFIG =====
EMAIL = "jjarandacarro@gmail.com"
PASSWORD = "Pelin0709$$$"

TELEGRAM_TOKEN = "8329264709:AAHyKe68ERfMr37EM8qn33KzMJuCuV6KeIM"
CHAT_ID = "6826449033"

PAR = "EURUSD"
TIEMPO = 60

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ===== CONEXION IQ =====
def conectar():
    Iq = IQ_Option(EMAIL, PASSWORD)
    Iq.connect()
    
    if Iq.check_connect():
        print("✅ Conectado a IQ Option")
        send_telegram("🚀 Bot PRO conectado a IQ Option DEMO")
        Iq.change_balance("PRACTICE")
        return Iq
    else:
        print("❌ Error conectando")
        return None

# ===== ESTRATEGIA =====
def estrategia(Iq):
    velas = Iq.get_candles(PAR, 60, 100, time.time())
    df = pd.DataFrame(velas)
    
    df['close'] = df['close']
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9).mean()
    
    rsi_actual = df['rsi'].iloc[-1]
    macd_actual = macd.iloc[-1]
    signal_actual = signal.iloc[-1]
    
    print("RSI:", rsi_actual)
    
    # FILTRO PRO
    if rsi_actual < 30 and macd_actual > signal_actual:
        return "🟢 COMPRA (CALL)"
    
    elif rsi_actual > 70 and macd_actual < signal_actual:
        return "🔴 VENTA (PUT)"
    
    return None

# ===== BOT =====
def run_bot():
    Iq = conectar()
    
    while True:
        try:
            if not Iq or not Iq.check_connect():
                print("Reconectando...")
                Iq = conectar()
                time.sleep(5)
                continue
            
            señal = estrategia(Iq)
            
            if señal:
                msg = f"{señal} {PAR} - 1 min"
                print(msg)
                send_telegram(msg)
                time.sleep(60)  # evita spam
            
            time.sleep(10)
        
        except Exception as e:
            print("Error:", e)
            time.sleep(10)

# ===== WEB (Render) =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot funcionando"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ===== INICIO =====
threading.Thread(target=run_web).start()
run_bot()
