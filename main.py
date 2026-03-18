import requests
import pandas as pd
import time

# 🔹 TELEGRAM
TOKEN = "AAHyKe68ERfMr37EM8qn33KzMJuCuV6KeIM"
CHAT_ID = "6826449033"


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🔹 OBTENER PRECIOS (API FUNCIONAL)
def get_price():
    import random

    prices = []
    price = 1.1000

    for _ in range(100):
        price += random.uniform(-0.001, 0.001)
        prices.append(price)

    return pd.Series(prices)


# 🔹 RSI
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# 🔹 EMA
def ema(series, span):
    return series.ewm(span=span).mean()


# 🔹 ESTRATEGIA
def estrategia():
    prices = get_price()

    print("Cantidad de precios:", len(prices))

    if len(prices) < 30:
        print("Esperando más datos...")
        return None

    rsi_val = rsi(prices).iloc[-1]
    ema9 = ema(prices, 9).iloc[-1]
    ema21 = ema(prices, 21).iloc[-1]

    print("RSI actual:", rsi_val)

    if rsi_val < 40:
        return "🟢 COMPRA (CALL)"

    elif rsi_val > 60:
        return "🔴 VENTA (PUT)"

    return None


# 🔹 LOOP
print("Bot iniciado...")

def run_bot():
    while True:
        try:
            señal = estrategia()

            if señal:
                print("Señal detectada:", señal)
                send_telegram(f"{señal} EUR/USD - 1 min")

            time.sleep(10)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)



import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot funcionando"

# correr bot en segundo plano
threading.Thread(target=run_bot).start()

# servidor web (esto necesita render)
app.run(host='0.0.0.0', port=10000)
