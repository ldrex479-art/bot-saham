import json
import yfinance as yf
import pandas as pd
from datetime import datetime

# Watchlist dengan sektor
WATCHLIST = [
    {"kode": "BBCA.JK", "sektor": "Perbankan"},
    {"kode": "BBRI.JK", "sektor": "Perbankan"},
    {"kode": "BMRI.JK", "sektor": "Perbankan"},
    {"kode": "BBNI.JK", "sektor": "Perbankan"},
    {"kode": "ARTO.JK", "sektor": "Perbankan"},
    {"kode": "TLKM.JK", "sektor": "Telekomunikasi"},
    {"kode": "ASII.JK", "sektor": "Otomotif"},
    {"kode": "UNVR.JK", "sektor": "Konsumer"},
    {"kode": "ICBP.JK", "sektor": "Konsumer"},
    {"kode": "INDF.JK", "sektor": "Konsumer"},
    {"kode": "KLBF.JK", "sektor": "Kesehatan"},
    {"kode": "ANTM.JK", "sektor": "Tambang"},
    {"kode": "PTBA.JK", "sektor": "Tambang"},
    {"kode": "ADRO.JK", "sektor": "Tambang"},
    {"kode": "MDKA.JK", "sektor": "Tambang"},
    {"kode": "SMGR.JK", "sektor": "Semen"},
    {"kode": "INTP.JK", "sektor": "Semen"},
    {"kode": "GOTO.JK", "sektor": "Teknologi"},
    {"kode": "TPIA.JK", "sektor": "Petrokimia"},
    {"kode": "BRPT.JK", "sektor": "Energi"},
]


def analisis_saham(item):
    kode = item["kode"]
    sektor = item["sektor"]
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

        # Historis 60 hari buat chart modal
        hist = df.tail(60)
        historis = []
        for idx, row in hist.iterrows():
            historis.append({
                'tgl': idx.strftime("%d/%m"),
                'harga': round(float(row['Close']), 0)
            })

        skor = 0
        sinyal = []
        alerts = []

        if ma20 > ma50:
            skor += 1
        else:
            skor -= 1

        if float(prev['MA20']) <= float(prev['MA50']) and ma20 > ma50:
            sinyal.append("GOLDEN CROSS")
            skor += 3
            alerts.append({"tipe": "bull", "pesan": "Golden Cross terdeteksi!"})
        elif float(prev['MA20']) >= float(prev['MA50']) and ma20 < ma50:
            sinyal.append("DEATH CROSS")
            skor -= 3
            alerts.append({"tipe": "bear", "pesan": "Death Cross terdeteksi!"})

        if rsi >= 70:
            sinyal.append(f"OVERBOUGHT (RSI {rsi:.1f})")
            skor -= 1
            alerts.append({"tipe": "warn", "pesan": f"Overbought! RSI {rsi:.1f}"})
        elif rsi <= 30:
            sinyal.append(f"OVERSOLD (RSI {rsi:.1f})")
            skor += 1
            alerts.append({"tipe": "info", "pesan": f"Oversold! RSI {rsi:.1f}"})

        if skor >= 3:
            verdict, level = "SANGAT BULLISH", "strong-bull"
        elif skor >= 2:
            verdict, level = "BULLISH", "bull"
        elif skor >= 0.5:
            verdict, level = "CENDERUNG NAIK", "mild-bull"
        elif skor <= -3:
            verdict, level = "SANGAT BEARISH", "strong-bear"
        elif skor <= -2:
            verdict, level = "BEARISH", "bear"
        elif skor <= -0.5:
            verdict, level = "CENDERUNG TURUN", "mild-bear"
        else:
            verdict, level = "NETRAL", "neutral"

        return {
            'kode': kode.replace('.JK', ''),
            'sektor': sektor,
            'harga': round(harga, 0),
            'perubahan': round(perubahan, 2),
            'ma20': round(ma20, 0),
            'ma50': round(ma50, 0),
            'rsi': round(rsi, 1),
            'verdict': verdict,
            'level': level,
            'sinyal': sinyal,
            'alerts': alerts,
            'skor': skor,
            'historis': historis
        }
    except Exception as e:
        print(f"Error {kode}: {e}")
        return None


def main():
    print(f"Analisis {len(WATCHLIST)} saham...")
    hasil = []
    for item in WATCHLIST:
        h = analisis_saham(item)
        if h:
            hasil.append(h)
            print(f"  {h['kode']}: Rp {h['harga']:,.0f} | {h['verdict']}")

    hasil.sort(key=lambda x: x['skor'], reverse=True)

    naik = sorted(hasil, key=lambda x: x['perubahan'], reverse=True)[:5]
    turun = sorted(hasil, key=lambda x: x['perubahan'])[:5]

    # Kumpulkan semua alerts
    all_alerts = []
    for h in hasil:
        for a in h['alerts']:
            all_alerts.append({'kode': h['kode'], **a})

    output = {
        'updated': datetime.now().strftime("%d %b %Y %H:%M WIB"),
        'total': len(hasil),
        'top_naik': [{'kode': x['kode'], 'perubahan': x['perubahan'], 'harga': x['harga']} for x in naik],
        'top_turun': [{'kode': x['kode'], 'perubahan': x['perubahan'], 'harga': x['harga']} for x in turun],
        'alerts': all_alerts,
        'saham': hasil
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n data.json tersimpan dengan {len(hasil)} saham.")


if __name__ == "__main__":
    main()
