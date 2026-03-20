from flask import Flask
import threading
import os

# =========================
# WEB SERVER (RENDER GRATIS)
# =========================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web).start()

# =========================
# IMPORTS
# =========================
import requests
import time
from iqoptionapi.stable_api import IQ_Option
import pandas as pd

# =========================
# CONFIG
# =========================
EMAIL = "jjarandacarro@gmail.com"
PASSWORD = "Pelin0709$$$"

TOKEN = "8329264709:AAHyKe68ERfMr37EM8qn33KzMJuCuV6KeIM"
CHAT_ID = "6826449033"

PARIDADES = ["EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC"]
MONTO = 1
TIEMPO = 60

# =========================
# TELEGRAM
# =========================
def enviar_mensaje(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

# =========================
# INDICADORES
# =========================
def calcular_rsi(df, periodo=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_macd(df):
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9).mean()
    return macd, signal

# =========================
# ANALISIS
# =========================
def analizar(df):
    df['rsi'] = calcular_rsi(df)
    macd, signal = calcular_macd(df)
    df['macd'] = macd
    df['signal'] = signal

    ultima = df.iloc[-1]

    razones = []

    # RSI
    if ultima['rsi'] < 40:
        razones.append("RSI bajo")
    elif ultima['rsi'] > 60:
        razones.append("RSI alto")
    else:
        razones.append("RSI neutro")

    # MACD
    if ultima['macd'] > ultima['signal']:
        razones.append("MACD alcista")
    else:
        razones.append("MACD bajista")

    # DECISIÓN
    if ultima['rsi'] < 40 and ultima['macd'] > ultima['signal']:
        return "call", razones

    elif ultima['rsi'] > 60 and ultima['macd'] < ultima['signal']:
        return "put", razones

    return None, razones

# =========================
# CONEXIÓN IQ OPTION
# =========================
print("Conectando a IQ Option...")
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if Iq.check_connect():
    print("Conectado correctamente")
    Iq.change_balance("PRACTICE")
    enviar_mensaje("🚀 Bot ACTIVO en IQ Option DEMO")
else:
    print("Error al conectar")
    exit()

# =========================
# LOOP PRINCIPAL
# =========================
while True:
    try:
        enviar_mensaje("🤖 Analizando mercado...")

        for par in PARIDADES:
           velas = Iq.get_candles(par, TIEMPO, 50, time.time())
           df = pd.DataFrame(velas)

           # VALIDACIÓN
        if df.empty or 'close' not in df.columns:
           enviar_mensaje(f"⚠️ Error datos en {par}")
           continue

           señal, razones = analizar(df)

        if señal == "call":
           enviar_mensaje(f"🟢 COMPRA (CALL) {par}\n{razones}")
           status, id = Iq.buy(MONTO, par, "call", 1)

        if status:
            enviar_mensaje("✅ Operación ejecutada")
        else:
            enviar_mensaje("❌ Error al ejecutar")

        elif señal == "put":
            enviar_mensaje(f"🔴 VENTA (PUT) {par}\n{razones}")
            status, id = Iq.buy(MONTO, par, "put", 1)

        if status:
            enviar_mensaje("✅ Operación ejecutada")
        else:
            enviar_mensaje("❌ Error al ejecutar")
            time.sleep(10)
