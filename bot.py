import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# ===== AMBIL DARI GITHUB SECRETS =====
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

WATCHLIST = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK",
    "ASII.JK", "UNVR.JK", "ICBP.JK", "INDF.JK", "KLBF.JK",
    "ANTM.JK", "PTBA.JK", "ADRO.JK", "SMGR.JK", "INTP.JK",
    "GOTO.JK", "ARTO.JK", "MDKA.JK", "TPIA.JK", "BRPT.JK"
]


def kirim_telegram(pesan):
    """Kirim pesan ke Telegram, print detail kalau gagal."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ ERROR: TELEGRAM_TOKEN atau TELEGRAM_CHAT_ID kosong!")
        print(f"   Token panjang: {len(TELEGRAM_TOKEN)} karakter")
        print(f"   Chat ID: '{TELEGRAM_CHAT_ID}'")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": pesan,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    print(f"📡 Kirim ke: chat_id={TELEGRAM_CHAT_ID}")
    print(f"   Token prefix: {TELEGRAM_TOKEN[:15]}...")
    print(f"   Token panjang: {len(TELEGRAM_TOKEN)} karakter")

    try:
        r = requests.post(url, data=data, timeout=15)
        print(f"   Status: {r.status_code}")
        print(f"   Respon: {r.text[:300]}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def analisis_saham(kode):
    """Analisis satu saham."""
    try:
        df = yf.download(kode, period="6mo", interval="1d",
                         progress=False, auto_adjust=True)
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

        if skor >= 3:
            verdict = "🟢🟢 SANGAT BULLISH"
        elif skor >= 2:
            verdict = "🟢 BULLISH"
        elif skor >= 0.5:
            verdict = "🟡 CENDERUNG NAIK"
        elif skor <= -3:
            verdict = "🔴🔴 SANGAT BEARISH"
        elif skor <= -2:
            verdict = "🔴 BEARISH"
        elif skor <= -0.5:
            verdict = "🟠 CENDERUNG TURUN"
        else:
            verdict = "⚪ NETRAL"

        return {
            'kode': kode.replace('.JK', ''),
            'harga': harga,
            'ma20': ma20,
            'ma50': ma50,
            'rsi': rsi,
            'verdict': verdict,
            'sinyal': sinyal,
            'skor': skor
        }
    except Exception as e:
        print(f"   Error {kode}: {e}")
        return None


def main():
    print("=" * 50)
    print(f"🤖 Bot Saham IHSG — {datetime.now().strftime('%d %b %Y %H:%M')}")
    print("=" * 50)

    print(f"\n🔍 Analisis {len(WATCHLIST)} saham...\n")
    hasil = []
    for kode in WATCHLIST:
        h = analisis_saham(kode)
        if h:
            hasil.append(h)
            print(f"   {h['kode']}: Rp {h['harga']:,.0f} | {h['verdict']}")

    if not hasil:
        print("\n❌ Tidak ada data saham. Cek koneksi / kode saham.")
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

    print("\n" + "=" * 50)
    print("📤 Kirim ke Telegram...")
    print("=" * 50)
    ok = kirim_telegram(pesan)

    if ok:
        print("\n✅ SUKSES! Cek Telegram kamu.")
    else:
        print("\n❌ GAGAL kirim Telegram. Lihat detail di atas.")


if __name__ == "__main__":
    main()
