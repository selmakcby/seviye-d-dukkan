"""Olay kaydı: her rol başlarken ve bitirirken cikti/olaylar.jsonl'a bir satır ekler.

Sahne (sahne/sunucu.py) bu dosyayı okur ve ajanları tarayıcıda canlı gösterir.
Kayıt hiçbir zaman hattı durdurmaz: yazılamazsa sessizce değil, uyarıyla geçer.

Python'dan:  from olay import olay; olay("bekci", "bitti", "25 kalıp · 3 zor", maliyet=0.01)
Kabuktan:    python3 betik/olay.py hermes not "002 kalıp cevap" [--kullanim cikti/hermes/kullanim-002.json]
"""
import json
import os
import sys
import time

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSYA = os.path.join(KOK, "cikti", "olaylar.jsonl")
ROLLER = ("betik", "bekci", "masa", "yazici", "yonetici", "hermes", "claude")
DURUMLAR = ("basladi", "bitti", "not")


def olay(rol, durum, detay="", maliyet=None, sayac=None):
    """Tek satır ekler. sayac: {"kalip": 25, ...} gibi sahne sayacının son değerleri."""
    if rol not in ROLLER or durum not in DURUMLAR:
        print(f"  ! olay: bilinmeyen rol/durum ({rol}, {durum})", file=sys.stderr)
        return
    satir = {"t": round(time.time(), 3), "rol": rol, "durum": durum, "detay": detay,
             "maliyet_usd": None if maliyet is None else round(float(maliyet), 5)}
    if sayac:
        satir = {**satir, "sayac": dict(sayac)}
    try:
        os.makedirs(os.path.dirname(DOSYA), exist_ok=True)
        with open(DOSYA, "a", encoding="utf-8") as f:
            f.write(json.dumps(satir, ensure_ascii=False) + "\n")
    except OSError as hata:
        print(f"  ! olay yazılamadı: {hata}", file=sys.stderr)


def kullanim_maliyeti(goreli):
    """Hermes --usage-file raporundaki tahmini USD; dosya yoksa None."""
    try:
        with open(os.path.join(KOK, goreli), encoding="utf-8") as f:
            return float(json.load(f).get("estimated_cost_usd") or 0)
    except (OSError, ValueError):
        return None


def main(argv):
    if len(argv) < 3:
        raise SystemExit("Kullanım: python3 betik/olay.py <rol> <durum> [detay] [--kullanim dosya]")
    maliyet = kullanim_maliyeti(argv[argv.index("--kullanim") + 1]) if "--kullanim" in argv else None
    detay = argv[3] if len(argv) > 3 and argv[3] != "--kullanim" else ""
    olay(argv[1], argv[2], detay, maliyet)


if __name__ == "__main__":
    main(sys.argv)
