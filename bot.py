import json
import yfinance as yf
import pandas as pd
from datetime import datetime

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
        volume = df['Volume']
        df['MA20'] = close.rolling(20).mean()
        df['MA50'] = close.rolling(50).mean()
        df['BB_std'] = close.rolling(20).std()
        df['BB_upper'] = df['MA20'] + 2 * df['BB_std']
        df['BB_lower'] = df['MA20'] - 2 * df['BB_std']
        df['VolMA'] = volume.rolling(20).mean()

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
        bb_up = float(last['BB_upper'])
        bb_low = float(last['BB_lower'])
        vol = float(last['Volume'])
        vol_ma = float(last['VolMA'])
        vol_ratio = vol / vol_ma if vol_ma > 0 else 1

        hist = df.tail(60)
        historis = []
        for idx, row in hist.iterrows():
            historis.append({
                'tgl': idx.strftime("%d/%m"),
                'harga': round(float(row['Close']), 0),
                'vol': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                'bb_up': round(float(row['BB_upper']), 0) if pd.notna(row['BB_upper']) else None,
                'bb_low': round(float(row['BB_lower']), 0) if pd.notna(row['BB_lower']) else None
            })

        skor = 0
        sinyal = []
        alerts = []
        alasan = []

        if ma20 > ma50:
            skor += 1
            alasan.append("MA20 di atas MA50")
        else:
            skor -= 1
            alasan.append("MA20 di bawah MA50")

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

        if harga > bb_up:
            sinyal.append("DI ATAS BOLLINGER UPPER")
            alerts.append({"tipe": "warn", "pesan": "Harga di atas Bollinger Upper"})
        elif harga < bb_low:
            sinyal.append("DI BAWAH BOLLINGER LOWER")
            alerts.append({"tipe": "info", "pesan": "Harga di bawah Bollinger Lower"})

        if vol_ratio > 2:
            sinyal.append(f"VOLUME SPIKE {vol_ratio:.1f}x")
            alerts.append({"tipe": "warn", "pesan": f"Volume naik {vol_ratio:.1f}x rata-rata"})

        # Confidence score (% berdasarkan kekuatan skor)
        confidence = min(100, int(abs(skor) / 5 * 100))

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
            'bb_up': round(bb_up, 0),
            'bb_low': round(bb_low, 0),
            'volume': int(vol),
            'vol_ratio': round(vol_ratio, 2),
            'verdict': verdict,
            'level': level,
            'confidence': confidence,
            'alasan': alasan,
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
            print(f"  {h['kode']}: Rp {h['harga']:,.0f} | {h['verdict']} | Conf {h['confidence']}%")

    hasil.sort(key=lambda x: x['skor'], reverse=True)

    naik = sorted(hasil, key=lambda x: x['perubahan'], reverse=True)[:5]
    turun = sorted(hasil, key=lambda x: x['perubahan'])[:5]

    all_alerts = []
    for h in hasil:
        for a in h['alerts']:
            all_alerts.append({'kode': h['kode'], **a})

    # Sector performance
    sectors = {}
    for h in hasil:
        s = h['sektor']
        if s not in sectors:
            sectors[s] = {'total_perubahan': 0, 'count': 0, 'bull': 0, 'bear': 0}
        sectors[s]['total_perubahan'] += h['perubahan']
        sectors[s]['count'] += 1
        if h['skor'] >= 0.5:
            sectors[s]['bull'] += 1
        elif h['skor'] <= -0.5:
            sectors[s]['bear'] += 1

    sector_perf = []
    for name, data in sectors.items():
        avg = data['total_perubahan'] / data['count']
        sector_perf.append({
            'nama': name,
            'avg': round(avg, 2),
            'count': data['count'],
            'bull': data['bull'],
            'bear': data['bear']
        })
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

    print(f"\n data.json tersimpan dengan {len(hasil)} saham.")


if __name__ == "__main__":
    main()
