import json
import math
import time
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set User-Agent biar nggak di-block Yahoo
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# 300 saham likuid IDX (yang biasanya ada di Yahoo Finance)
RAW_LIST = """
BBCA|Perbankan
BBRI|Perbankan
BMRI|Perbankan
BBNI|Perbankan
ARTO|Perbankan
BRIS|Perbankan
BTPS|Perbankan
BNGA|Perbankan
BDMN|Perbankan
BJBR|Perbankan
BJTM|Perbankan
NISP|Perbankan
BBTN|Perbankan
AGRO|Perbankan
PNBN|Perbankan
MEGA|Perbankan
BACA|Perbankan
BCAP|Perbankan
BBYB|Perbankan
BNII|Perbankan
BTPN|Perbankan
BNBA|Perbankan
BVIC|Perbankan
MAYA|Perbankan
MCOR|Perbankan
NOBU|Perbankan
BMAS|Perbankan
BBKP|Perbankan
BBHI|Perbankan
BKSW|Perbankan
BFIN|Multifinance
ADMF|Multifinance
MFIN|Multifinance
CFIN|Multifinance
WOMF|Multifinance
PNIN|Asuransi
ASBI|Asuransi
LIFE|Asuransi
AMAG|Asuransi
ABDA|Asuransi
TLKM|Telekomunikasi
ISAT|Telekomunikasi
EXCL|Telekomunikasi
TOWR|Telekomunikasi
MTEL|Telekomunikasi
TBIG|Telekomunikasi
ASII|Otomotif
AUTO|Otomotif
SMSM|Otomotif
INDS|Otomotif
GJTL|Otomotif
IMAS|Otomotif
BIRD|Otomotif
UNVR|Konsumer
ICBP|Konsumer
INDF|Konsumer
MYOR|Konsumer
GGRM|Konsumer
HMSP|Konsumer
WIIM|Konsumer
CPIN|Konsumer
JPFA|Konsumer
MAIN|Konsumer
SIDO|Konsumer
DLTA|Konsumer
MLBI|Konsumer
ROTI|Konsumer
CAMP|Konsumer
AISA|Konsumer
ULTJ|Konsumer
STTP|Konsumer
TBLA|Konsumer
LSIP|Agrikultur
AALI|Agrikultur
SIMP|Agrikultur
SGRO|Agrikultur
DSNG|Agrikultur
ANJT|Agrikultur
BWPT|Agrikultur
SSMS|Agrikultur
KLBF|Kesehatan
KAEF|Kesehatan
MIKA|Kesehatan
HEAL|Kesehatan
SILO|Kesehatan
SAME|Kesehatan
PRDA|Kesehatan
IRRA|Kesehatan
TSPC|Kesehatan
PEHA|Kesehatan
DVLA|Kesehatan
SDPC|Kesehatan
ANTM|Tambang
PTBA|Tambang
ADRO|Tambang
MDKA|Tambang
INCO|Tambang
TINS|Tambang
ITMG|Tambang
HRUM|Tambang
BYAN|Tambang
GEMS|Tambang
BUMI|Tambang
TOBA|Tambang
DOID|Tambang
PTRO|Tambang
MBAP|Tambang
BSSR|Tambang
INDY|Tambang
SGER|Tambang
KKGI|Tambang
MYOH|Tambang
FIRE|Tambang
NICL|Tambang
ZINC|Tambang
CITA|Tambang
DKFT|Tambang
IFSH|Tambang
SMGR|Semen
INTP|Semen
WSBP|Semen
SMCB|Semen
SMBR|Semen
ARNA|Semen
TOTO|Semen
GOTO|Teknologi
BUKA|Teknologi
EMTK|Teknologi
DCII|Teknologi
MTDL|Teknologi
MLPT|Teknologi
DMMX|Teknologi
WIFI|Teknologi
KREN|Teknologi
LMAS|Teknologi
TECH|Teknologi
PGAS|Energi
MEDC|Energi
BRPT|Energi
TPIA|Energi
AKRA|Energi
ESSA|Energi
RAJA|Energi
ELSA|Energi
ENRG|Energi
BULL|Energi
SURE|Energi
PSAB|Energi
ARTI|Energi
POWR|Energi
KEEN|Energi
TGRA|Energi
PSSI|Energi
BSDE|Properti
CTRA|Properti
PWON|Properti
SMRA|Properti
LPKR|Properti
ASRI|Properti
DILD|Properti
APLN|Properti
KIJA|Properti
DMAS|Properti
BKSL|Properti
MDLN|Properti
BEST|Properti
PPRO|Properti
RDTX|Properti
KOTA|Properti
META|Properti
MTLA|Properti
BAPI|Properti
JSMR|Infrastruktur
WIKA|Infrastruktur
WSKT|Infrastruktur
PTPP|Infrastruktur
ADHI|Infrastruktur
TOTL|Infrastruktur
NRCA|Infrastruktur
ACST|Infrastruktur
MTRA|Infrastruktur
IPCM|Infrastruktur
ASSA|Logistik
SMDR|Logistik
TMAS|Logistik
HITS|Logistik
SOCA|Logistik
SAFE|Logistik
WEHA|Logistik
LEAD|Logistik
ACES|Ritel
MAPI|Ritel
LPPF|Ritel
RALS|Ritel
AMRT|Ritel
CSAP|Ritel
MIDI|Ritel
HERO|Ritel
ERAA|Ritel
RANC|Ritel
DPUM|Ritel
LION|Industri
KRAS|Industri
INAI|Industri
BAJA|Industri
JKSW|Industri
GGRP|Industri
ISSP|Industri
LMSH|Industri
KBLI|Industri
KBLM|Industri
PICO|Industri
SCCO|Industri
IKAI|Industri
INTA|Industri
ALKA|Industri
BMSR|Industri
TIRT|Industri
SRIL|Tekstil
TRIS|Tekstil
RICY|Tekstil
UNIT|Tekstil
ARGO|Tekstil
CNTX|Tekstil
ESTI|Tekstil
POLY|Tekstil
RMBA|Konsumer
BATI|Konsumer
ITIC|Konsumer
ASDM|Konsumer
INOV|Teknologi
LUCY|Ritel
SOTS|Ritel
SRAJ|Kesehatan
PRIM|Kesehatan
BMHS|Kesehatan
RSGK|Kesehatan
BABP|Perbankan
BBMD|Perbankan
BCIC|Perbankan
BEKS|Perbankan
BINA|Perbankan
BGTG|Perbankan
BSIM|Perbankan
BSWD|Perbankan
DNAR|Perbankan
INPC|Perbankan
MASB|Perbankan
NICK|Perbankan
PNBS|Perbankan
VRNA|Perbankan
YELO|Perbankan
"""

WATCHLIST = [tuple(line.split('|')) for line in RAW_LIST.strip().split('\n') if line.strip()]


def safe(v, default=0):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except:
        return default


def safe_int(v, default=0):
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return default
        return int(f)
    except:
        return default


def analisis_saham(item):
    kode_short, sektor = item
    kode = kode_short + ".JK"
    
    # Coba 2x kalau gagal
    for attempt in range(2):
        try:
            df = yf.download(
                kode, 
                period="3mo", 
                interval="1d", 
                progress=False, 
                auto_adjust=True,
                threads=False,
                timeout=10
            )
            if df.empty or len(df) < 20:
                if attempt == 0:
                    time.sleep(0.5)
                    continue
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

            harga = safe(last['Close'])
            if harga == 0:
                return None
            prev_harga = safe(prev['Close'], 1)
            perubahan = ((harga - prev_harga) / prev_harga * 100) if prev_harga else 0
            if math.isnan(perubahan) or math.isinf(perubahan):
                perubahan = 0

            ma20 = safe(last['MA20'])
            ma50 = safe(last['MA50'])
            rsi = safe(last['RSI'], 50)

            # Candles 60 hari
            hist = df.tail(60)
            candles = []
            for idx, row in hist.iterrows():
                o, h, l, c = safe(row['Open']), safe(row['High']), safe(row['Low']), safe(row['Close'])
                if o == 0 or c == 0:
                    continue
                candles.append({
                    'time': idx.strftime("%Y-%m-%d"),
                    'open': round(o, 0), 'high': round(h, 0),
                    'low': round(l, 0), 'close': round(c, 0),
                    'volume': safe_int(row['Volume'])
                })

            spark = [{'tgl': idx.strftime("%d/%m"), 'harga': round(safe(r['Close']), 0)}
                     for idx, r in df.tail(20).iterrows() if safe(r['Close']) > 0]

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
                'kode': kode_short,
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
            if attempt == 0:
                time.sleep(0.5)
                continue
            return None
    return None


def main():
    print(f"Analisis {len(WATCHLIST)} saham (parallel, retry-enabled)...")
    hasil = []
    gagal = []
    done = 0

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(analisis_saham, item): item for item in WATCHLIST}
        for future in as_completed(futures):
            done += 1
            item = futures[future]
            h = future.result()
            if h and h['harga'] > 0:
                hasil.append(h)
            else:
                gagal.append(item[0])
            if done % 25 == 0 or done == len(WATCHLIST):
                print(f"  [{done}/{len(WATCHLIST)}] Berhasil: {len(hasil)}")

    print(f"\nTotal berhasil: {len(hasil)} saham")
    print(f"Gagal: {len(gagal)} saham")
    if gagal:
        print(f"Daftar gagal: {', '.join(gagal[:30])}{'...' if len(gagal)>30 else ''}")

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

    advancing = sum(1 for h in hasil if h['perubahan'] > 0)
    declining = sum(1 for h in hasil if h['perubahan'] < 0)
    unchanged = len(hasil) - advancing - declining

    output = {
        'updated': datetime.now().strftime("%d %b %Y %H:%M WIB"),
        'total': len(hasil),
        'breadth': {'advancing': advancing, 'declining': declining, 'unchanged': unchanged},
        'top_naik': [{'kode': x['kode'], 'perubahan': x['perubahan'], 'harga': x['harga']} for x in naik],
        'top_turun': [{'kode': x['kode'], 'perubahan': x['perubahan'], 'harga': x['harga']} for x in turun],
        'alerts': all_alerts[:50],
        'sector_perf': sector_perf,
        'saham': hasil
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, allow_nan=False)

    print(f"\n data.json: {len(hasil)} saham.")


if __name__ == "__main__":
    main()
