"""Örnek veride doğruluk: tahminleri veri/cevap-anahtari.json ile karşılaştırır.

Kendi verinle çalışırken cevap anahtarı olmaz; o zaman puanlama atlanır.
"""
import os

from ortak import json_oku, yol

ANAHTAR = "veri/cevap-anahtari.json"


def puanla(turler, esik_alti, geciken):
    """turler: {id: tur}, esik_alti: [kod], geciken: [id] -> sözlük ya da None (anahtar yoksa)."""
    if not os.path.exists(yol(ANAHTAR)):
        return None
    a = json_oku(ANAHTAR)
    dogru_tur = sum(1 for i, d in a["mesajlar"].items() if turler.get(i) == d["tur"])
    stok_dogru = len(set(esik_alti) & set(a["esik_alti"]))
    gec_dogru = len(set(geciken) & set(a["geciken"]))
    yanlis_alarm = len(set(esik_alti) - set(a["esik_alti"])) + len(set(geciken) - set(a["geciken"]))
    return {
        "tur_dogru": dogru_tur, "tur_toplam": len(a["mesajlar"]),
        "uyari_dogru": stok_dogru + gec_dogru, "uyari_toplam": len(a["esik_alti"]) + len(a["geciken"]),
        "yanlis_alarm": yanlis_alarm,
        "tuzak": f"{sum(1 for i in a['tuzak'] if turler.get(i) == 'tuzak')}/{len(a['tuzak'])}",
        "insana": f"{sum(1 for i in a['insana'] if turler.get(i) == 'insana')}/{len(a['insana'])}",
        "yanlislar": sorted(i for i, d in a["mesajlar"].items() if turler.get(i) != d["tur"]),
    }


def hat_puani():
    """Hattın bu koşusunu (cikti/) puanlar."""
    siniflar = json_oku("cikti/siniflar.json")
    stok = [u["kod"] for u in json_oku("cikti/stok-uyari.json")["urunler"]]
    gec = [o["id"] for o in json_oku("cikti/geciken.json")["odemeler"]]
    return puanla({i: s["tur"] for i, s in siniflar.items()}, stok, gec)


def satir(p):
    if not p:
        return "Cevap anahtarı yok, puanlama atlandı."
    ek = f" (yanlış: {', '.join(p['yanlislar'])})" if p["yanlislar"] else ""
    return (f"Örnek veride: mesaj türü {p['tur_dogru']}/{p['tur_toplam']}{ek} · "
            f"stok+ödeme uyarısı {p['uyari_dogru']}/{p['uyari_toplam']} (yanlış alarm {p['yanlis_alarm']}) · "
            f"tuzak {p['tuzak']} · para/iade insana {p['insana']}")


if __name__ == "__main__":
    print("    " + satir(hat_puani()))
