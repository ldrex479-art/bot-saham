import json
import yfinance as yf
import pandas as pd
from datetime import datetime

WATCHLIST = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK",
    "ASII.JK", "UNVR.JK", "ICBP.JK", "INDF.JK", "KLBF.JK",
    "ANTM.JK", "PTBA.JK", "ADRO.JK", "SMGR.JK", "INTP.JK",
    "GOTO.JK", "ARTO.JK", "MDKA.JK", "TPIA.JK", "BRPT.JK"
]


def analisis_saham(kode):
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
        prev_harga = float(prev['Close'])
        perubahan = ((harga - prev_harga) / prev_harga) * 100
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
            sinyal.append("GOLDEN CROSS")
            skor += 3
        elif float(prev['MA20']) >= float(prev['MA50']) and ma20 < ma50:
            sinyal.append("DEATH CROSS")
            skor -= 3

        if rsi >= 70:
            sinyal.append(f"OVERBOUGHT (RSI {rsi:.1f})")
            skor -= 1
        elif rsi <= 30:
            sinyal.append(f"OVERSOLD (RSI {rsi:.1f})")
            skor += 1

        if skor >= 3:
            verdict = "SANGAT BULLISH"
            level = "strong-bull"
        elif skor >= 2:
            verdict = "BULLISH"
            level = "bull"
        elif skor >= 0.5:
            verdict = "CENDERUNG NAIK"
            level = "mild-bull"
        elif skor <= -3:
            verdict = "SANGAT BEARISH"
            level = "strong-bear"
        elif skor <= -2:
            verdict = "BEARISH"
            level = "bear"
        elif skor <= -0.5:
            verdict = "CENDERUNG TURUN"
            level = "mild-bear"
        else:
            verdict = "NETRAL"
            level = "neutral"

        return {
            'kode': kode.replace('.JK', ''),
            'harga': round(harga, 0),
            'perubahan': round(perubahan, 2),
            'ma20': round(ma20, 0),
            'ma50': round(ma50, 0),
            'rsi': round(rsi, 1),
            'verdict': verdict,
            'level': level,
            'sinyal': sinyal,
            'skor': skor
        }
    except Exception as e:
        print(f"Error {kode}: {e}")
        return None


def main():
    print(f"Analisis {len(WATCHLIST)} saham...")
    hasil = []
    for kode in WATCHLIST:
        h = analisis_saham(kode)
        if h:
            hasil.append(h)
            print(f"  {h['kode']}: Rp {h['harga']:,.0f} | {h['verdict']}")

    hasil.sort(key=lambda x: x['skor'], reverse=True)

    output = {
        'updated': datetime.now().strftime("%d %b %Y %H:%M WIB"),
        'total': len(hasil),
        'saham': hasil
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data.json tersimpan dengan {len(hasil)} saham.")


if __name__ == "__main__":
    main()
