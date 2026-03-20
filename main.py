from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo"

def run_web():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_web).start()

# ============================
# IMPORTS
# ============================
import time
from datetime import datetime
import pandas as pd
import requests
from iqoptionapi.stable_api import IQ_Option

# ============================
# CONFIG
# ============================
EMAIL = "jjarandacarro@gmail.com"
PASSWORD = "Pelin0709$$$"
TOKEN = "8329264709:AAHyKe68ERfMr37EM8qn33KzMJuCuV6KeIM"
CHAT_ID = "6826449033"

PARIDADES = ["EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC"]
TIEMPO = 60
MONTO = 100

# ============================
# TELEGRAM
# ============================
def enviar_mensaje(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

# ============================
# INDICADORES
# ============================
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
    señal = macd.ewm(span=9).mean()
    return macd, señal

# ============================
# ANALISIS
# ============================
def analizar(df):
    df['rsi'] = calcular_rsi(df)
    macd, señal_macd = calcular_macd(df)

    rsi = df['rsi'].iloc[-1]
    macd_actual = macd.iloc[-1]
    señal_actual = señal_macd.iloc[-1]

    razones = ""

    if rsi < 30 and macd_actual > señal_actual:
        razones = f"RSI bajo ({rsi:.2f})\nMACD alcista"
        return "call", razones

    elif rsi > 70 and macd_actual < señal_actual:
        razones = f"RSI alto ({rsi:.2f})\nMACD bajista"
        return "put", razones

    else:
        razones = f"RSI neutro ({rsi:.2f})\nMACD sin cruce claro"
        return "none", razones

# ============================
# CONEXION IQ OPTION
# ============================
Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()
Iq.change_balance("PRACTICE")

enviar_mensaje("🚀 Bot ACTIVO conectado a IQ Option DEMO")

# ============================
# LOOP PRINCIPAL
# ============================
while True:
    try:
        enviar_mensaje("🤖 Analizando mercado...")

        for par in PARIDADES:
            velas = Iq.get_candles(par, TIEMPO, 50, time.time())
            df = pd.DataFrame(velas)

            # VALIDACIÓN ANTI ERROR
            if df.empty or 'close' not in df.columns:
                enviar_mensaje(f"⚠️ Error datos en {par}")
                continue

            señal, razones = analizar(df)

            if señal == "call":
                enviar_mensaje(f"🟢 COMPRA {par}\n{razones}")
                status, _ = Iq.buy(MONTO, par, "call", 1)

                if status:
                    enviar_mensaje("✅ Operación ejecutada")
                else:
                    enviar_mensaje("❌ Error al ejecutar")

            elif señal == "put":
                enviar_mensaje(f"🔴 VENTA {par}\n{razones}")
                status, _ = Iq.buy(MONTO, par, "put", 1)

                if status:
                    enviar_mensaje("✅ Operación ejecutada")
                else:
                    enviar_mensaje("❌ Error al ejecutar")

            else:
                enviar_mensaje(f"❌ {par} sin señal\n{razones}")

        time.sleep(60)

    except Exception as e:
        enviar_mensaje(f"⚠️ Error: {e}")
        time.sleep(10)
