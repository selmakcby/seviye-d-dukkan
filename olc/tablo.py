"""olc/sonuclar/*.json -> olc/SONUC.md tablosu (her koşu + ortalama)."""
import glob
import json
import os
from datetime import datetime

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADLAR = {"naif": "NAİF: Opus ajanına veri/ klasörünü ver", "hat": "HAT: betik + Haiku bekçi + Sonnet",
         "betik": "SADECE BETİK: kurallar + şablonlar"}


def virgul(x, b=4):
    return f"{x:.{b}f}".replace(".", ",")


def oku():
    kayitlar = []
    for yol in sorted(glob.glob(os.path.join(KOK, "olc", "sonuclar", "*.json"))):
        if not yol.endswith(".ham.json"):
            with open(yol, encoding="utf-8") as f:
                kayitlar.append(json.load(f))
    return kayitlar


def kosu_satiri(k):
    p = k["puan"] or {}
    dag = ", ".join(f"{m} {virgul(u)}" for m, u in k["modeller"].items()) or "model yok"
    return (f"| {ADLAR[k['yol']]} | {k['kos']} | {virgul(k['usd'])} | {k['sure_sn']} | "
            f"{p.get('tur_dogru', '-')}/{p.get('tur_toplam', '-')} | {p.get('uyari_dogru', '-')}/{p.get('uyari_toplam', '-')}"
            f" ({p.get('yanlis_alarm', '-')}) | {p.get('tuzak', '-')} | {p.get('insana', '-')} | {dag} |")


def tablo(kayitlar):
    satir = ["| Yol | Koşu | USD | Süre (sn) | Mesaj türü doğru | Stok+ödeme uyarısı (yanlış alarm) | Tuzak | Para/iade insana | Model dağılımı |",
             "|---|---|---|---|---|---|---|---|---|"]
    ozet = {}
    for yol in ("naif", "hat", "betik"):
        grup = sorted((k for k in kayitlar if k["yol"] == yol), key=lambda k: k["kos"])
        if not grup:
            continue
        satir += [kosu_satiri(k) for k in grup]
        ort = {a: sum(k[a] for k in grup) / len(grup) for a in ("usd", "sure_sn")}
        ozet[yol] = ort
        satir.append(f"| **{ADLAR[yol]}** | **ortalama** | **{virgul(ort['usd'])}** | **{ort['sure_sn']:.0f}** | | | | | |")
    return satir, ozet


if __name__ == "__main__":
    satirlar, ozet = tablo(oku())
    metin = [f"# Ölçüm sonucu · {datetime.now():%d.%m.%Y}", "",
             "Sırça Seramik örnek verisi: 30 müşteri mesajı, 20 ürün, 12 ödeme. Maliyet: `claude -p --output-format json`"
             " çıktısındaki `total_cost_usd`. Süre: duvar saati. Doğruluk: `veri/cevap-anahtari.json`"
             " (30 mesaj türü, 7 eşik altı ürün + 5 geciken ödeme = 12 uyarı, 1 tuzak, 1 para/iade).", ""] + satirlar
    if "naif" in ozet and "hat" in ozet and ozet["hat"]["usd"] > 0:
        oran = ozet["naif"]["usd"] / ozet["hat"]["usd"]
        metin += ["", f"**Ortalama maliyet oranı: naif yol hattın {virgul(oran, 1)} katı.**"]
    notlar = os.path.join(KOK, "olc", "notlar.md")
    if os.path.exists(notlar):
        with open(notlar, encoding="utf-8") as f:
            metin += ["", f.read().strip()]
    with open(os.path.join(KOK, "olc", "SONUC.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(metin) + "\n")
    print("\n".join(metin))
