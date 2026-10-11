import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# ===== AMBIL DARI ENVIRONMENT (GitHub Secrets) =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

WATCHLIST = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK",
    "ASII.JK", "UNVR.JK", "ICBP.JK", "INDF.JK", "KLBF.JK",
    "ANTM.JK", "PTBA.JK", "ADRO.JK", "SMGR.JK", "INTP.JK",
    "GOTO.JK", "ARTO.JK", "MDKA.JK", "TPIA.JK", "BRPT.JK"
]


def kirim_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": pesan,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Error kirim Telegram: {e}")
        return False


def analisis(kode):
    try:
        df = yf.download(kode, period="6mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 50:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df['Close']
        df['MA20'] = close.rolling(20).mean()
        df['MA50'] = close.rolling(50).mean()

        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain / loss))

        last = df.iloc[-1]
        prev = df.iloc[-2]

        harga = float(last['Close'])
        ma20 = float(last['MA20'])
        ma50 = float(last['MA50'])
        rsi = float(last['RSI'])

        skor = 0
        sinyal = []

        if ma20 > ma50:
            skor += 1
        else:
            skor -= 1

        if float(prev['MA20']) <= float(prev['MA50']) and ma20 > ma50:
            sinyal.append("🟢 GOLDEN CROSS")
            skor += 3
        elif float(prev['MA20']) >= float(prev['MA50']) and ma20 < ma50:
            sinyal.append("🔴 DEATH CROSS")
            skor -= 3

        if rsi >= 70:
            sinyal.append(f"⚠️ OVERBOUGHT (RSI {rsi:.1f})")
            skor -= 1
        elif rsi <= 30:
            sinyal.append(f"💎 OVERSOLD (RSI {rsi:.1f})")
            skor += 1

        if skor >= 3: verdict = "🟢🟢 SANGAT BULLISH"
        elif skor >= 2: verdict = "🟢 BULLISH"
        elif skor >= 0.5: verdict = "🟡 CENDERUNG NAIK"
        elif skor <= -3: verdict = "🔴🔴 SANGAT BEARISH"
        elif skor <= -2: verdict = "🔴 BEARISH"
        elif skor <= -0.5: verdict = "🟠 CENDERUNG TURUN"
        else: verdict = "⚪ NETRAL"

        return {
            'kode': kode.replace('.JK',''),
            'harga': harga,
            'ma20': ma20,
            'ma50': ma50,
            'rsi': rsi,
            'verdict': verdict,
            'sinyal': sinyal,
            'skor': skor
        }
    except Exception as e:
        print(f"Error {kode}: {e}")
        return None


def main():
    print(f"🔍 Analisis {len(WATCHLIST)} saham...")
    hasil = []
    for kode in WATCHLIST:
        h = analisis(kode)
        if h:
            hasil.append(h)
            print(f"   {h['kode']}: Rp {h['harga']:,.0f} | {h['verdict']}")

    if not hasil:
        print("❌ Tidak ada data")
        return

    hasil.sort(key=lambda x: x['skor'], reverse=True)

    now = datetime.now().strftime("%d %b %Y %H:%M WIB")
    pesan = f"📊 <b>LAPORAN SAHAM IHSG</b>\n<i>{now}</i>\n"
    pesan += "━" * 20 + "\n\n"

    for h in hasil:
        pesan += f"<b>{h['kode']}</b> — Rp {h['harga']:,.0f}\n"
        pesan += f"   MA20: {h['ma20']:,.0f} | MA50: {h['ma50']:,.0f} | RSI: {h['rsi']:.1f}\n"
        pesan += f"   {h['verdict']}\n"
        for s in h['sinyal']:
            pesan += f"   • {s}\n"
        pesan += "\n"

    pesan += "━" * 20 + "\n"
    pesan += "⚠️ <i>Bukan rekomendasi. DYOR.</i>"

    ok = kirim_telegram(pesan)
    print(f"📤 Telegram: {'✅' if ok else '❌'}")


if __name__ == "__main__":
    main()
