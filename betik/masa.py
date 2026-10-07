"""Rol: MÜŞTERİ MASASI. Cevap TASLAĞI yazar, hiçbir şey GÖNDERMEZ.

- kalip  -> sss.md şablonu + veri/ tabloları (0 token)
- zor    -> tek yalın Sonnet çağrısında 2-3 cümlelik taslak (`--sadece-betik` ile atlanır)
- tuzak / insana -> cevap yazılmaz, rapora "insana" olarak gider
Çıktı: cikti/cevaplar.md, cikti/cevaplar.json
"""
import re
import sys

from dogrula import hatalar, sema_yukle
from ortak import (csv_oku, json_ayikla, json_oku, json_yaz, kucuk, maliyet_yaz, mesajlar_oku,
                   metin_oku, metin_yaz, veri_blogu, yalin_cagri)

MODEL = "sonnet"
YASAK_CIKTI = re.compile(r"\biban\b|TR\d{2}\s?\d{4}|indirim kodu\s*:?\s*[A-Z0-9]{4,}", re.I)
DURUM = {"hazirlaniyor": "hazırlanıyor, 1-2 iş günü içinde kargoya verilecek",
         "kargoda": "kargoda", "teslim edildi": "kargo firmasına göre teslim edildi"}


def sss_oku():
    """sss.md -> ({'fiyat': şablon, ...}, bilgi metni)"""
    sablonlar, bilgi = {}, ""
    for parca in re.split(r"^## ", metin_oku("sss.md"), flags=re.M)[1:]:
        baslik, _, govde = parca.partition("\n")
        if baslik.startswith("kalip:"):
            sablonlar[baslik.split(":", 1)[1].strip()] = govde.strip()
        elif baslik.strip() == "bilgi":
            bilgi = govde.strip()
    return sablonlar, bilgi


def urun_bul(metin, urunler):
    """En uzun eşleşen anahtar kelimenin ürünü (0 token)."""
    metin, aday = kucuk(metin), (0, None)
    for u in urunler:
        for kelime in u["anahtar_kelimeler"].split(";"):
            if kucuk(kelime) in metin and len(kelime) > aday[0]:
                aday = (len(kelime), u)
    return aday[1]


def siparis_alanlari(metin, siparisler):
    bulunan = re.search(r"(?:#|\b)(10\d\d)\b", metin)
    s = next((x for x in siparisler if bulunan and x["no"] == bulunan.group(1)), None)
    if not s:
        return None
    kargo = f"{s['kargo']}, takip no: {s['takip_no']}." if s["takip_no"] else ""
    if s["durum"] == "teslim edildi":
        kargo += " Eline ulaşmadıysa bize yaz, hemen kargo firmasıyla kontrol edelim."
    return {"no": s["no"], "siparis_urun": s["urun"], "durum": DURUM.get(s["durum"], s["durum"]),
            "kargo_bilgisi": kargo.strip()}


def kalip_cevap(m, konu, sablonlar, tablolar):
    """Şablonu doldurur. Dönüş: (cevap, None) ya da (None, neden doldurulamadı)."""
    alan = {"ad": m["kimden"].split()[0]}
    if konu in ("fiyat", "stok"):
        u = urun_bul(m["metin"], tablolar["stok"])
        if not u:
            return None, "ürün tabloda bulunamadı"
        alan.update(urun=u["urun"], fiyat=u["fiyat_tl"], tedarik_gun=u["tedarik_gun"])
        if konu == "stok":
            konu = "stok-var" if int(u["eldeki"]) > 0 else "stok-yok"
    if konu == "siparis":
        s = siparis_alanlari(m["metin"], tablolar["siparisler"])
        if not s:
            return None, "sipariş numarası bulunamadı"
        alan.update(s)
    if konu not in sablonlar:
        return None, f"sss.md içinde '{konu}' şablonu yok"
    return sablonlar[konu].format(**alan), None


def zor_taslaklar(zorlar, bilgi):
    """Tek Sonnet çağrısı; şemaya uymazsa bir kez tekrar. Dönüş: ({id: taslak}, cagrilar)."""
    if not zorlar:
        return {}, []
    sistem = metin_oku("betik/promptlar/masa.txt").replace("{bilgi}", bilgi)
    sema, girdi = sema_yukle("taslak.schema.json"), "\n\n".join(veri_blogu(m) for m in zorlar)
    cagrilar, gecerli = [], {}
    for deneme in (1, 2):
        c = yalin_cagri(MODEL, sistem, girdi, butce_usd=0.3)
        cagrilar.append(c)
        cevap = (json_ayikla(c["metin"]) or {}).get("taslaklar", {})
        gecerli = {i: t for i, t in cevap.items() if not hatalar(t, sema) and not YASAK_CIKTI.search(t)}
        if all(m["id"] in gecerli for m in zorlar):
            break
        print(f"    ! deneme {deneme}: bazı taslaklar şemaya ya da çıkış filtresine takıldı")
    return gecerli, cagrilar


def cevaplari_kur(mesajlar, siniflar, sablonlar, tablolar):
    """Kalıp cevapları doldurur, zor olanları ayırır. Dönüş: (sonuc, zorlar)."""
    sonuc, zorlar = {}, []
    for m in mesajlar:
        s = siniflar.get(m["id"], {"tur": "insana", "konu": "diger", "neden": "bekçi sınıflamadı"})
        kayit = {"kimden": m["kimden"], "kanal": m["kanal"], "tur": s["tur"], "konu": s["konu"],
                 "neden": s["neden"], "metin": m["metin"], "cevap": None, "yazan": None}
        if s["tur"] == "kalip":
            cevap, sorun = kalip_cevap(m, s["konu"], sablonlar, tablolar)
            if cevap:
                kayit.update(cevap=cevap, yazan="şablon (0 token)")
            else:
                kayit.update(tur="insana", neden=f"şablon doldurulamadı: {sorun}")
        elif s["tur"] == "zor":
            zorlar.append(m)
        sonuc[m["id"]] = kayit
    return sonuc, zorlar


def md_yaz(sonuc):
    satir = ["# Müşteri cevap taslakları", "",
             "> **Hiçbiri gönderilmedi.** Kontrol et, düzelt, kendin gönder.", ""]
    gruplar = [("zor", "Zor sorular · Sonnet taslağı"), ("kalip", "Kalıp sorular · sss.md şablonu, 0 token"),
               ("insana", "Cevap yazılmadı · insana"), ("tuzak", "Cevap yazılmadı · tuzak (talimat enjeksiyonu)")]
    for tur, baslik in gruplar:
        secili = [(i, k) for i, k in sonuc.items() if k["tur"] == tur]
        if not secili:
            continue
        satir += [f"## {baslik} ({len(secili)})", ""]
        for i, k in secili:
            satir.append(f"### {i} · {k['kimden']} · {k['kanal']}" + (f" · {k['konu']}" if tur == "kalip" else ""))
            satir.append("> " + k["metin"].replace("\n", " ")[:300])
            satir += ["", k["cevap"] if k["cevap"] else f"_Neden: {k['neden']}_", ""]
    metin_yaz("cikti/cevaplar.md", "\n".join(satir))


def main():
    sadece_betik = "--sadece-betik" in sys.argv
    siniflar = json_oku("cikti/siniflar.json")
    sablonlar, bilgi = sss_oku()
    tablolar = {"stok": csv_oku("veri/stok.csv"), "siparisler": csv_oku("veri/siparisler.csv")}
    sonuc, zorlar = cevaplari_kur(mesajlar_oku(), siniflar, sablonlar, tablolar)
    taslaklar, cagrilar = ({}, []) if sadece_betik else zor_taslaklar(zorlar, bilgi)
    for m in zorlar:
        if m["id"] in taslaklar:
            sonuc[m["id"]].update(cevap=taslaklar[m["id"]].strip(), yazan="Sonnet taslağı")
        else:
            neden = "--sadece-betik: zor soruya model çağrılmadı" if sadece_betik else "Sonnet taslağı alınamadı"
            sonuc[m["id"]].update(tur="insana", neden=neden)
    json_yaz("cikti/cevaplar.json", sonuc)
    md_yaz(sonuc)
    maliyet_yaz("masa", cagrilar)
    hazir = sum(1 for k in sonuc.values() if k["cevap"])
    usd = sum(c["usd"] for c in cagrilar)
    print(f"    {hazir} cevap taslağı hazır ({len(taslaklar)} Sonnet, {hazir - len(taslaklar)} şablon)"
          f" · {usd:.4f} USD · gönderilen: 0")


if __name__ == "__main__":
    main()
