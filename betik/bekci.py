"""Rol: BEKÇİ (Haiku). Her mesaja tür verir: kalip | zor | tuzak | insana.

- Bütün mesajlar TEK yalın Haiku çağrısında sınıflanır (araçsız, düşünme kapalı).
- Cevap JSON şemasıyla doğrulanır; uymazsa bir kez tekrar denenir, yine uymazsa o mesaj "insana".
- Kural ağı: bilinen enjeksiyon ve para/iade kalıpları, model ne derse desin tuzak/insana olur.
- `--kural`: model hiç çağrılmaz (0 token); konu anahtar kelimeyle bulunur.
Çıktı: cikti/siniflar.json
"""
import re
import sys

from dogrula import hatalar, sema_yukle
from olay import olay
from ortak import json_ayikla, json_yaz, kucuk, maliyet_yaz, mesajlar_oku, metin_oku, veri_blogu, yalin_cagri

MODEL = "haiku"
ENJEKSIYON = re.compile(r"talimat\w* (yok say|unut|görmezden)|sistem notu|ignore (all|previous)|"
                        r"indirim kodu üret|yönetici asistan|müşteri listesi", re.I)
PARA = re.compile(r"\biade\b|iade ed|param\w*|ıban|\biban\b|geri öde|şikayet ed", re.I)
KONU_KURALLARI = [
    ("siparis", r"#\d{4}|\b10\d\d\b|sipariş(im| no)"),
    ("kargo", r"kargo"),
    ("stok", r"stok|var m[ıi]|kald[ıi] m[ıi]"),
    ("fiyat", r"fiyat|ne kadar|kaç lira|kaç tl"),
    ("saat", r"saat|açık m|kaçta|açıl"),
]


def kural_agi(m):
    """Model kandırılsa bile yakalanacak kalıplar. Dönüş: (tur, neden) ya da None."""
    metin = kucuk(m["metin"])
    if ENJEKSIYON.search(metin):
        return "tuzak", "kural: talimat enjeksiyonu kalıbı"
    if PARA.search(metin):
        return "insana", "kural: para / iade talebi"
    return None


def kural_ile_sinifla(m):
    """0 token yol: anahtar kelimeyle konu bulunursa kalıp, bulunamazsa insana."""
    metin = kucuk(m["metin"])
    for konu, desen in KONU_KURALLARI:
        if re.search(desen, metin):
            return {"tur": "kalip", "konu": konu, "neden": f"kural: '{konu}' anahtar kelimesi"}
    return {"tur": "insana", "konu": "diger", "neden": "kural: anahtar kelime yok"}


def model_ile_sinifla(mesajlar):
    """Tek Haiku çağrısı; şemaya uymayan cevapta bir kez tekrar. Dönüş: (siniflar, cagrilar)."""
    sistem, sema = metin_oku("betik/promptlar/bekci.txt"), sema_yukle("bekci.schema.json")
    girdi = "\n\n".join(veri_blogu(m) for m in mesajlar)
    cagrilar, gecerli = [], {}
    for deneme in (1, 2):
        c = yalin_cagri(MODEL, sistem, girdi, butce_usd=0.2)
        cagrilar.append(c)
        cevap = (json_ayikla(c["metin"]) or {}).get("mesajlar", {})
        gecerli = {i: s for i, s in cevap.items() if isinstance(s, dict) and not hatalar(s, sema)}
        eksik = [m["id"] for m in mesajlar if m["id"] not in gecerli]
        if not eksik:
            break
        print(f"    ! deneme {deneme}: {len(eksik)} mesaj şemaya uymadı ya da eksik ({', '.join(eksik[:5])})")
    return gecerli, cagrilar


def birlestir(mesajlar, model_siniflari, kural_modu):
    sonuc = {}
    for m in mesajlar:
        s = kural_ile_sinifla(m) if kural_modu else model_siniflari.get(m["id"])
        s = dict(s) if s else {"tur": "insana", "konu": "diger", "neden": "model cevabı şemaya uymadı"}
        s["kaynak"] = "kural" if kural_modu else "model"
        ag = kural_agi(m)
        if ag and (ag[0] != s["tur"] or kural_modu):
            s = {**s, "tur": ag[0], "konu": "diger", "neden": ag[1], "kaynak": "kural ağı"}
        sonuc[m["id"]] = {**s, "kimden": m["kimden"], "kanal": m["kanal"]}
    return sonuc


def olay_yaz(siniflar, sayac, usd):
    """Sahne için: tuzak ve insana mesajları tek tek, sonra toplam."""
    for i, s in siniflar.items():
        if s["tur"] in ("tuzak", "insana"):
            olay("bekci", "not", f"{i} → {s['tur']}")
    say = {t: sayac.get(t, 0) for t in ("kalip", "zor", "tuzak", "insana")}
    olay("bekci", "bitti", f"{say['kalip']} kalıp · {say['zor']} zor · {say['tuzak']} tuzak · {say['insana']} insana",
         maliyet=usd, sayac=say)


def main():
    kural_modu = "--kural" in sys.argv
    mesajlar = mesajlar_oku()
    if not mesajlar:
        print("    Yeni mesaj yok: bekçi çağrılmadı (ön kontrol, 0 token).")
        json_yaz("cikti/siniflar.json", {})
        maliyet_yaz("bekci", [])
        olay("bekci", "bitti", "mesaj yok · 0 token")
        return
    olay("bekci", "basladi", f"{len(mesajlar)} mesaj sınıflanıyor" + (" · sadece kurallar" if kural_modu else " · Haiku"))
    model_siniflari, cagrilar = ({}, []) if kural_modu else model_ile_sinifla(mesajlar)
    siniflar = birlestir(mesajlar, model_siniflari, kural_modu)
    json_yaz("cikti/siniflar.json", siniflar)
    maliyet_yaz("bekci", cagrilar)
    sayac = {}
    for s in siniflar.values():
        sayac[s["tur"]] = sayac.get(s["tur"], 0) + 1
    usd = sum(c["usd"] for c in cagrilar)
    olay_yaz(siniflar, sayac, usd)
    print(f"    {len(mesajlar)} mesaj: " + ", ".join(f"{k} {v}" for k, v in sorted(sayac.items()))
          + f" · {usd:.4f} USD")


if __name__ == "__main__":
    main()
