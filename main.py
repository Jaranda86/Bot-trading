import requests
import time
import threading
from flask import Flask
from iqoptionapi.stable_api import IQ_Option
import pandas as pd
import numpy as np

# ==============================
# 🔐 CONFIGURACIÓN
# ==============================

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

PAR = "EURUSD"
TIEMPO = 1  # minutos

# ==============================
# 📲 TELEGRAM
# ==============================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except:
        pass

# ==============================
# 🔌 CONEXIÓN IQ OPTION
# ==============================

def conectar_iq():
    Iq = IQ_Option(EMAIL, PASSWORD)
    Iq.connect()
    
    if Iq.check_connect():
        print("✅ Conectado a IQ Option")
        Iq.change_balance("PRACTICE")
        return Iq
    else:
        print("❌ Error conectando")
        return None

# ==============================
# 📊 INDICADORES
# ==============================

def obtener_velas(Iq):
    velas = Iq.get_candles(PAR, 60, 100, time.time())
    df = pd.DataFrame(velas)
    return df

def calcular_rsi(df, periodo=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_ema(df, periodo=20):
    return df["close"].ewm(span=periodo).mean()

def calcular_macd(df):
    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

# ==============================
# 🧠 ESTRATEGIA PRO
# ==============================

def estrategia(df):
    rsi = calcular_rsi(df).iloc[-1]
    ema = calcular_ema(df).iloc[-1]
    macd, signal = calcular_macd(df)

    macd_actual = macd.iloc[-1]
    signal_actual = signal.iloc[-1]

    precio = df["close"].iloc[-1]

    vela_actual = df.iloc[-1]
    vela_anterior = df.iloc[-2]

    print(f"RSI: {rsi:.2f} | MACD: {macd_actual:.5f}")

    # 🟢 COMPRA
    if (
        rsi < 30 and
        macd_actual > signal_actual and
        precio > ema and
        vela_actual["close"] > vela_actual["open"]
    ):
        return "call"

    # 🔴 VENTA
    elif (
        rsi > 70 and
        macd_actual < signal_actual and
        precio < ema and
        vela_actual["close"] < vela_actual["open"]
    ):
        return "put"

    return None

# ==============================
# 📊 CONTROL
# ==============================

ultima_senal = None
ultimo_tiempo = 0

ganadas = 0
perdidas = 0

# ==============================
# 🤖 BOT
# ==============================

def run_bot():
    global ultima_senal, ultimo_tiempo, ganadas, perdidas

    Iq = conectar_iq()
    if not Iq:
        return

    send_telegram("🚀 Bot PRO conectado a IQ Option DEMO")

    while True:
        try:
            df = obtener_velas(Iq)
            señal = estrategia(df)

            ahora = time.time()

            if señal and (señal != ultima_senal or ahora - ultimo_tiempo > 300):

                send_telegram(f"📊 Señal: {señal.upper()} {PAR} - {TIEMPO} min")

                # 💰 EJECUTAR OPERACIÓN DEMO
                monto = 1
                status, id = Iq.buy(monto, PAR, señal, TIEMPO)

                if status:
                    send_telegram("⏳ Operación ejecutada")

                    time.sleep(TIEMPO * 60)

                    resultado = Iq.check_win_v4(id)

                    if resultado > 0:
                        ganadas += 1
                        send_telegram(f"✅ GANADA +{resultado}")
                    else:
                        perdidas += 1
                        send_telegram(f"❌ PERDIDA {resultado}")

                    send_telegram(f"📊 Stats → G: {ganadas} | P: {perdidas}")

                ultima_senal = señal
                ultimo_tiempo = ahora

            time.sleep(10)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

# ==============================
# 🌐 WEB (Render)
# ==============================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot PRO funcionando"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# ==============================
# 🚀 START
# ==============================

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    run_web()
