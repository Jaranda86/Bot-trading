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

PAR = "EURUSD""AUDCAD""EURGBP"
TIEMPO = 1  # minutos
MONTO = 1   # monto por operación

# ===== TELEGRAM =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ===== CONEXION =====
def conectar():
    Iq = IQ_Option(EMAIL, PASSWORD)
    Iq.connect()
    
    if Iq.check_connect():
        print("✅ Conectado")
        send_telegram("🚀 Bot ACTIVO conectado a IQ Option DEMO")
        Iq.change_balance("PRACTICE")
        return Iq
    else:
        print("❌ Error conexión")
        return None

# ===== ESTRATEGIA ACTIVA =====
def estrategia(Iq):
    velas = Iq.get_candles(PAR, 60, 100, time.time())
    df = pd.DataFrame(velas)

    close = df['close']

    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # MACD
    exp1 = close.ewm(span=12).mean()
    exp2 = close.ewm(span=26).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9).mean()

    rsi_actual = rsi.iloc[-1]
    macd_actual = macd.iloc[-1]
    signal_actual = signal.iloc[-1]

    print("RSI:", rsi_actual)

    # 🎯 MODO ACTIVO (más flexible)
    if rsi_actual < 35 and macd_actual > signal_actual:
        return "call"
    
    elif rsi_actual > 65 and macd_actual < signal_actual:
        return "put"

    return None

# ===== OPERAR =====
def operar(Iq, accion):
    print("Ejecutando operación:", accion)
    
    check, id = Iq.buy(MONTO, PAR, accion, TIEMPO)
    
    if check:
        send_telegram(f"📊 {PAR}\n{'🟢 COMPRA' if accion=='call' else '🔴 VENTA'}\n💰 ${MONTO}\n⏱ {TIEMPO} min")
        
        time.sleep(TIEMPO * 60)
        
        result = Iq.check_win_v4(id)
        
        if result > 0:
            send_telegram(f"✅ GANADA +{result}")
        else:
            send_telegram(f"❌ PERDIDA {result}")
    else:
        print("Error al operar")

# ===== BOT =====
def run_bot():
    Iq = conectar()
    ultimo_mensaje = time.time()

    while True:
        try:
            if not Iq or not Iq.check_connect():
                print("🔄 Reconectando...")
                Iq = conectar()
                time.sleep(5)
                continue

            print("🤖 Analizando mercado...")

            # mensaje cada 5 min
            if time.time() - ultimo_mensaje > 300:
                send_telegram("🤖 Bot activo analizando mercado...")
                ultimo_mensaje = time.time()

            señal = estrategia(Iq)

            if señal:
                operar(Iq, señal)
                time.sleep(60)  # evita spam

            time.sleep(10)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

# ===== WEB =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot funcionando"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# ===== INICIO =====
threading.Thread(target=run_web).start()
run_bot()
