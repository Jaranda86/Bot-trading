import requests
import time
from datetime import datetime
from iqoptionapi.stable_api import IQ_Option
import pandas as pd

# =========================
# CONFIG
# =========================
EMAIL = "jjarandacarro@gmail.com"
PASSWORD = "Pelin0709$$$"

TOKEN = "8329264709:AAHyKe68ERfMr37EM8qn33KzMJuCuV6KeIM"
CHAT_ID = "6826449033"

PARIDADES = ["EURUSD", "GBPUSD", "AUDUSD"]
TIEMPO = 60  # 1 min
MONTO = 1

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
    if ultima['rsi'] < 30:
        razones.append("RSI sobreventa")
    elif ultima['rsi'] > 70:
        razones.append("RSI sobrecompra")
    else:
        razones.append("RSI neutro")

    # MACD
    if ultima['macd'] > ultima['signal']:
        razones.append("MACD alcista")
    else:
        razones.append("MACD bajista")

    # DECISIÓN EQUILIBRADA
    if ultima['rsi'] < 35 and ultima['macd'] > ultima['signal']:
        return "call", razones

    elif ultima['rsi'] > 65 and ultima['macd'] < ultima['signal']:
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
    enviar_mensaje("🚀 Bot ACTIVO conectado a IQ Option DEMO")
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

            señal, razones = analizar(df)

            if señal == "call":
                msg = f"🟢 COMPRA (CALL) {par}\n" + "\n".join(razones)
                enviar_mensaje(msg)

                Iq.buy(MONTO, par, "call", 1)

            elif señal == "put":
                msg = f"🔴 VENTA (PUT) {par}\n" + "\n".join(razones)
                enviar_mensaje(msg)

                Iq.buy(MONTO, par, "put", 1)

            else:
                msg = f"❌ {par} sin señal clara\n" + "\n".join(razones)
                enviar_mensaje(msg)

            time.sleep(2)

        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        enviar_mensaje(f"⚠️ Error: {e}")
        time.sleep(10)
