import json
import math
import yfinance as yf
import pandas as pd
from datetime import datetime

WATCHLIST = [
    ("BBCA.JK","Perbankan"),("BBRI.JK","Perbankan"),("BMRI.JK","Perbankan"),("BBNI.JK","Perbankan"),
    ("ARTO.JK","Perbankan"),("BRIS.JK","Perbankan"),("BTPS.JK","Perbankan"),("BNGA.JK","Perbankan"),
    ("TLKM.JK","Telekomunikasi"),("ISAT.JK","Telekomunikasi"),("EXCL.JK","Telekomunikasi"),("TOWR.JK","Telekomunikasi"),
    ("ASII.JK","Otomotif"),("AUTO.JK","Otomotif"),("SMSM.JK","Otomotif"),("INDS.JK","Otomotif"),
    ("UNVR.JK","Konsumer"),("ICBP.JK","Konsumer"),("INDF.JK","Konsumer"),("MYOR.JK","Konsumer"),
    ("GGRM.JK","Konsumer"),("HMSP.JK","Konsumer"),("WIIM.JK","Konsumer"),
    ("KLBF.JK","Kesehatan"),("SIDO.JK","Kesehatan"),("KAEF.JK","Kesehatan"),("MIKA.JK","Kesehatan"),
    ("ANTM.JK","Tambang"),("PTBA.JK","Tambang"),("ADRO.JK","Tambang"),("MDKA.JK","Tambang"),
    ("INCO.JK","Tambang"),("TINS.JK","Tambang"),("ITMG.JK","Tambang"),
    ("SMGR.JK","Semen"),("INTP.JK","Semen"),("WSBP.JK","Semen"),
    ("GOTO.JK","Teknologi"),("BUKA.JK","Teknologi"),("EMTK.JK","Teknologi"),("DCII.JK","Teknologi"),
    ("PGAS.JK","Energi"),("MEDC.JK","Energi"),("BRPT.JK","Energi"),("TPIA.JK","Energi"),
    ("BSDE.JK","Properti"),("CTRA.JK","Properti"),("PWON.JK","Properti"),("SMRA.JK","Properti"),
    ("JSMR.JK","Infrastruktur"),("WIKA.JK","Infrastruktur"),
]


def safe(v, default=0):
    """Konversi nilai ke float yang aman. NaN/inf → default."""
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except:
        return default


def safe_int(v, default=0):
    """Konversi nilai ke int yang aman."""
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return default
        return int(f)
    except:
        return default


def analisis_saham(kode, sektor):
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

        last, prev = df.iloc[-1], df.iloc[-2]
        harga = safe(last['Close'])
        prev_harga = safe(prev['Close'], 1)
        if prev_harga == 0:
            perubahan = 0
        else:
            perubahan = ((harga - prev_harga) / prev_harga) * 100
        if math.isnan(perubahan) or math.isinf(perubahan):
            perubahan = 0

        ma20 = safe(last['MA20'])
        ma50 = safe(last['MA50'])
        rsi = safe(last['RSI'], 50)

        # OHLC 90 hari
        hist = df.tail(90)
        candles = []
        for idx, row in hist.iterrows():
            o = safe(row['Open'])
            h = safe(row['High'])
            l = safe(row['Low'])
            c = safe(row['Close'])
            if o == 0 or c == 0:
                continue
            candles.append({
                'time': idx.strftime("%Y-%m-%d"),
                'open': round(o, 0),
                'high': round(h, 0),
                'low': round(l, 0),
                'close': round(c, 0),
                'volume': safe_int(row['Volume'])
            })

        # Sparkline 30 hari
        spark = []
        for idx, row in df.tail(30).iterrows():
            c = safe(row['Close'])
            if c > 0:
                spark.append({'tgl': idx.strftime("%d/%m"), 'harga': round(c, 0)})

        skor, sinyal, alerts = 0, [], []
        if ma20 > ma50: skor += 1
        else: skor -= 1

        if safe(prev['MA20']) <= safe(prev['MA50']) and ma20 > ma50 and ma20 > 0:
            sinyal.append("GOLDEN CROSS"); skor += 3
            alerts.append({"tipe": "bull", "pesan": "Golden Cross!"})
        elif safe(prev['MA20']) >= safe(prev['MA50']) and ma20 < ma50 and ma20 > 0:
            sinyal.append("DEATH CROSS"); skor -= 3
            alerts.append({"tipe": "bear", "pesan": "Death Cross!"})

        if rsi >= 70:
            sinyal.append(f"OVERBOUGHT RSI {rsi:.0f}"); skor -= 1
            alerts.append({"tipe": "warn", "pesan": f"Overbought RSI {rsi:.0f}"})
        elif rsi <= 30:
            sinyal.append(f"OVERSOLD RSI {rsi:.0f}"); skor += 1
            alerts.append({"tipe": "info", "pesan": f"Oversold RSI {rsi:.0f}"})

        if skor >= 3: verdict, level = "SANGAT BULLISH", "strong-bull"
        elif skor >= 2: verdict, level = "BULLISH", "bull"
        elif skor >= 0.5: verdict, level = "CENDERUNG NAIK", "mild-bull"
        elif skor <= -3: verdict, level = "SANGAT BEARISH", "strong-bear"
        elif skor <= -2: verdict, level = "BEARISH", "bear"
        elif skor <= -0.5: verdict, level = "CENDERUNG TURUN", "mild-bear"
        else: verdict, level = "NETRAL", "neutral"

        confidence = min(100, int(abs(skor) / 5 * 100))
        volume = safe_int(last['Volume'])
        vol_avg = df['Volume'].tail(20).mean()
        vol_ma = safe(vol_avg, 1)
        if vol_ma == 0: vol_ma = 1
        vol_ratio = round(volume / vol_ma, 2)
        if math.isnan(vol_ratio) or math.isinf(vol_ratio):
            vol_ratio = 0

        return {
            'kode': kode.replace('.JK',''),
            'sektor': sektor,
            'harga': round(harga, 0),
            'perubahan': round(perubahan, 2),
            'ma20': round(ma20, 0),
            'ma50': round(ma50, 0),
            'rsi': round(rsi, 1),
            'volume': volume,
            'vol_ratio': vol_ratio,
            'verdict': verdict,
            'level': level,
            'confidence': confidence,
            'sinyal': sinyal,
            'alerts': alerts,
            'skor': skor,
            'candles': candles,
            'spark': spark
        }
    except Exception as e:
        print(f"Error {kode}: {e}")
        return None


def main():
    print(f"Analisis {len(WATCHLIST)} saham...")
    hasil = []
    for kode, sektor in WATCHLIST:
        h = analisis_saham(kode, sektor)
        if h and h['harga'] > 0:
            hasil.append(h)
            print(f"  {h['kode']:6s} Rp {h['harga']:>8,.0f} | {h['verdict']}")

    hasil.sort(key=lambda x: x['skor'], reverse=True)

    naik = sorted(hasil, key=lambda x: x['perubahan'], reverse=True)[:5]
    turun = sorted(hasil, key=lambda x: x['perubahan'])[:5]

    all_alerts = []
    for h in hasil:
        for a in h['alerts']:
            all_alerts.append({'kode': h['kode'], **a})

    sec = {}
    for h in hasil:
        s = h['sektor']
        if s not in sec: sec[s] = {'total': 0, 'n': 0, 'bull': 0, 'bear': 0}
        sec[s]['total'] += h['perubahan']; sec[s]['n'] += 1
        if h['skor'] >= 0.5: sec[s]['bull'] += 1
        elif h['skor'] <= -0.5: sec[s]['bear'] += 1
    sector_perf = [{'nama': k, 'avg': round(v['total']/v['n'],2), 'count': v['n'],
                    'bull': v['bull'], 'bear': v['bear']} for k,v in sec.items()]
    sector_perf.sort(key=lambda x: x['avg'], reverse=True)

    output = {
        'updated': datetime.now().strftime("%d %b %Y %H:%M WIB"),
        'total': len(hasil),
        'top_naik': [{'kode': x['kode'], 'perubahan': x['perubahan'], 'harga': x['harga']} for x in naik],
        'top_turun': [{'kode': x['kode'], 'perubahan': x['perubahan'], 'harga': x['harga']} for x in turun],
        'alerts': all_alerts,
        'sector_perf': sector_perf,
        'saham': hasil
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, allow_nan=False)

    print(f"\n data.json: {len(hasil)} saham.")


if __name__ == "__main__":
    main()
