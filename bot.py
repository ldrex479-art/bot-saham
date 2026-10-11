import json
import yfinance as yf
import pandas as pd
from datetime import datetime

WATCHLIST = [
    # Perbankan
    ("BBCA.JK","Perbankan"),("BBRI.JK","Perbankan"),("BMRI.JK","Perbankan"),("BBNI.JK","Perbankan"),
    ("ARTO.JK","Perbankan"),("BRIS.JK","Perbankan"),("BTPS.JK","Perbankan"),("BNGA.JK","Perbankan"),
    # Telekomunikasi
    ("TLKM.JK","Telekomunikasi"),("ISAT.JK","Telekomunikasi"),("EXCL.JK","Telekomunikasi"),("TOWR.JK","Telekomunikasi"),
    # Otomotif
    ("ASII.JK","Otomotif"),("AUTO.JK","Otomotif"),("SMSM.JK","Otomotif"),("INDS.JK","Otomotif"),
    # Konsumer
    ("UNVR.JK","Konsumer"),("ICBP.JK","Konsumer"),("INDF.JK","Konsumer"),("MYOR.JK","Konsumer"),
    ("GGRM.JK","Konsumer"),("HMSP.JK","Konsumer"),("WIIM.JK","Konsumer"),
    # Kesehatan
    ("KLBF.JK","Kesehatan"),("SIDO.JK","Kesehatan"),("KAEF.JK","Kesehatan"),("MIKA.JK","Kesehatan"),
    # Tambang
    ("ANTM.JK","Tambang"),("PTBA.JK","Tambang"),("ADRO.JK","Tambang"),("MDKA.JK","Tambang"),
    ("INCO.JK","Tambang"),("TINS.JK","Tambang"),("ITMG.JK","Tambang"),
    # Semen & Material
    ("SMGR.JK","Semen"),("INTP.JK","Semen"),("WSBP.JK","Semen"),
    # Teknologi & Digital
    ("GOTO.JK","Teknologi"),("BUKA.JK","Teknologi"),("EMTK.JK","Teknologi"),("DCII.JK","Teknologi"),
    # Energi
    ("PGAS.JK","Energi"),("MEDC.JK","Energi"),("BRPT.JK","Energi"),("TPIA.JK","Energi"),
    # Properti
    ("BSDE.JK","Properti"),("CTRA.JK","Properti"),("PWON.JK","Properti"),("SMRA.JK","Properti"),
    # Infrastruktur
    ("JSMR.JK","Infrastruktur"),("WIKA.JK","Infrastruktur"),
]


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
        df['BB_std'] = close.rolling(20).std()
        df['BB_upper'] = df['MA20'] + 2 * df['BB_std']
        df['BB_lower'] = df['MA20'] - 2 * df['BB_std']

        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain / loss))

        last, prev = df.iloc[-1], df.iloc[-2]
        harga = float(last['Close'])
        perubahan = ((harga - float(prev['Close'])) / float(prev['Close'])) * 100
        ma20, ma50 = float(last['MA20']), float(last['MA50'])
        rsi = float(last['RSI'])

        # OHLC 90 hari buat candlestick
        hist = df.tail(90)
        candles = []
        for idx, row in hist.iterrows():
            if pd.isna(row['Open']) or pd.isna(row['Close']):
                continue
            candles.append({
                'time': idx.strftime("%Y-%m-%d"),
                'open': round(float(row['Open']), 0),
                'high': round(float(row['High']), 0),
                'low': round(float(row['Low']), 0),
                'close': round(float(row['Close']), 0),
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0
            })

        # Sparkline
        spark = [{'tgl': idx.strftime("%d/%m"), 'harga': round(float(row['Close']),0)}
                 for idx, row in df.tail(30).iterrows()]

        skor, sinyal, alerts = 0, [], []
        if ma20 > ma50: skor += 1
        else: skor -= 1

        if float(prev['MA20']) <= float(prev['MA50']) and ma20 > ma50:
            sinyal.append("GOLDEN CROSS"); skor += 3
            alerts.append({"tipe": "bull", "pesan": "Golden Cross!"})
        elif float(prev['MA20']) >= float(prev['MA50']) and ma20 < ma50:
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
        volume = int(last['Volume']) if pd.notna(last['Volume']) else 0
        vol_ma = float(df['Volume'].tail(20).mean()) if df['Volume'].notna().any() else 1
        vol_ratio = round(volume / vol_ma, 2) if vol_ma > 0 else 1

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
        if h:
            hasil.append(h)
            print(f"  {h['kode']:6s} Rp {h['harga']:>8,.0f} | {h['verdict']}")

    hasil.sort(key=lambda x: x['skor'], reverse=True)

    naik = sorted(hasil, key=lambda x: x['perubahan'], reverse=True)[:5]
    turun = sorted(hasil, key=lambda x: x['perubahan'])[:5]

    all_alerts = []
    for h in hasil:
        for a in h['alerts']:
            all_alerts.append({'kode': h['kode'], **a})

    # Sektor
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
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n data.json: {len(hasil)} saham.")


if __name__ == "__main__":
    main()
