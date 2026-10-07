"""Rol: STOK VE ÖDEME BETİĞİ (0 token).

Kural tablodan gelir, model gerekmez:
- Eşik altı ürün: eldeki < günlük satış × (tedarik süresi + tampon gün)
- Geciken ödeme: durum "bekliyor" ve vade bugünden önce
Çıktı: cikti/stok-uyari.json, cikti/geciken.json
"""
import math
from datetime import date

from ortak import ayar, bugun, csv_oku, json_yaz, maliyet_yaz, para


def stok_uyarilari(urunler, tampon_gun, hedef_gun):
    uyarilar = []
    for u in urunler:
        gunluk, eldeki, tedarik = float(u["gunluk_satis"]), int(u["eldeki"]), int(u["tedarik_gun"])
        esik = gunluk * (tedarik + tampon_gun)
        if eldeki >= esik:
            continue
        hedef = gunluk * (tedarik + tampon_gun + hedef_gun)
        uyarilar.append({
            "kod": u["kod"], "urun": u["urun"], "tedarikci": u["tedarikci"],
            "eldeki": eldeki, "esik": round(esik, 1), "gunluk_satis": gunluk, "tedarik_gun": tedarik,
            "kac_gun_yeter": round(eldeki / gunluk, 1) if gunluk else None,
            "onerilen_siparis": max(1, math.ceil(hedef - eldeki)),
        })
    return sorted(uyarilar, key=lambda x: (x["kac_gun_yeter"] or 0))


def gecikenler(odemeler, gun):
    sonuc = []
    for o in odemeler:
        vade = date.fromisoformat(o["vade"])
        if o["durum"].strip() != "bekliyor" or vade >= gun:
            continue
        sonuc.append({"id": o["id"], "musteri": o["musteri"], "iletisim": o["iletisim"],
                      "tutar_tl": int(o["tutar_tl"]), "vade": o["vade"],
                      "gecikme_gun": (gun - vade).days})
    return sorted(sonuc, key=lambda x: -x["gecikme_gun"])


def main():
    a = ayar()
    gun = bugun()
    stok = stok_uyarilari(csv_oku("veri/stok.csv"), a.get("tampon_gun", 3), a.get("siparis_hedef_gun", 14))
    gec = gecikenler(csv_oku("veri/odemeler.csv"), gun)
    json_yaz("cikti/stok-uyari.json", {"tarih": gun.isoformat(), "urunler": stok})
    json_yaz("cikti/geciken.json", {"tarih": gun.isoformat(), "odemeler": gec})
    maliyet_yaz("stok-odeme", [])
    toplam = sum(o["tutar_tl"] for o in gec)
    print(f"    {len(stok)} ürün eşik altında, {len(gec)} ödeme gecikmiş ({para(toplam)} TL). 0 token.")


if __name__ == "__main__":
    main()
