"""Rol: MESAJ YAZICI (Sonnet). Geciken ödeme hatırlatmaları + tedarikçi sipariş taslakları.

- Girdi betikten gelir (cikti/geciken.json, cikti/stok-uyari.json); model sayı hesaplamaz.
- Yapacak iş yoksa model çağrılmaz (ön kontrol).
- `--sadece-betik`: model yerine düz şablon (0 token).
Hiçbir şey GÖNDERMEZ. Çıktı: cikti/taslaklar.md, cikti/taslaklar.json
"""
import re
import sys

from dogrula import hatalar, sema_yukle
from ortak import json_ayikla, json_oku, json_yaz, maliyet_yaz, metin_oku, metin_yaz, para, yalin_cagri

MODEL = "sonnet"
YASAK_CIKTI = re.compile(r"\biban\b\s*:?\s*TR|TR\d{2}\s?\d{4}", re.I)


def girdi_metni(gecikenler, stok):
    satir = ["GECİKEN ÖDEMELER (id | müşteri | ilgili kişi | tutar TL | vade | kaç gün geçti):"]
    satir += [f"{o['id']} | {o['musteri']} | {o['iletisim']} | {para(o['tutar_tl'])} | {o['vade']} | {o['gecikme_gun']}"
              for o in gecikenler]
    satir += ["", "SİPARİŞ VERİLECEK ÜRÜNLER (tedarikçi | ürün | önerilen adet | eldeki):"]
    satir += [f"{u['tedarikci']} | {u['urun']} | {u['onerilen_siparis']} | {u['eldeki']}" for u in stok]
    return "\n".join(satir)


def sablon_taslaklar(gecikenler, stok):
    """0 token yol: model yok, düz şablon."""
    hat = [{"id": o["id"], "metin": f"Merhaba {o['iletisim']}, {o['vade']} vadeli {para(o['tutar_tl'])} TL "
            f"tutarındaki faturamızın ödemesi {o['gecikme_gun']} gün gecikmiş görünüyor. "
            "Uygun olduğunuzda kontrol edebilir misiniz? Teşekkürler, Sırça Seramik."} for o in gecikenler]
    tedarikciler = sorted({u["tedarikci"] for u in stok})
    sip = [{"tedarikci": t, "metin": "Merhaba, şu ürünlerden sipariş vermek istiyoruz: " + "; ".join(
        f"{u['urun']} x{u['onerilen_siparis']}" for u in stok if u["tedarikci"] == t)
        + ". Ne zaman gönderebilirsiniz?"} for t in tedarikciler]
    return {"hatirlatmalar": hat, "siparisler": sip}


def model_taslaklar(gecikenler, stok):
    sistem, sema = metin_oku("betik/promptlar/yazici.txt"), sema_yukle("yazici.schema.json")
    cagrilar = []
    for deneme in (1, 2):
        c = yalin_cagri(MODEL, sistem, girdi_metni(gecikenler, stok), butce_usd=0.3)
        cagrilar.append(c)
        veri = json_ayikla(c["metin"])
        if veri is not None and not hatalar(veri, sema) and not YASAK_CIKTI.search(c["metin"]):
            return veri, cagrilar
        print(f"    ! deneme {deneme}: yazıcı cevabı şemaya ya da çıkış filtresine uymadı")
    print("    ! yazıcı taslak üretemedi, düz şablona dönülüyor")
    return sablon_taslaklar(gecikenler, stok), cagrilar


def md_yaz(taslak, gecikenler, yazan):
    adlar = {o["id"]: o for o in gecikenler}
    satir = ["# Mesaj taslakları", "", f"> {yazan}. **Hiçbiri gönderilmedi.**", "",
             f"## Ödeme hatırlatmaları ({len(taslak['hatirlatmalar'])})", ""]
    for h in taslak["hatirlatmalar"]:
        o = adlar.get(h["id"], {})
        satir += [f"### {h['id']} · {o.get('musteri', '?')} · {para(o.get('tutar_tl', 0))} TL · "
                  f"{o.get('gecikme_gun', '?')} gün gecikme", "", h["metin"].strip(), ""]
    satir += [f"## Tedarikçi sipariş taslakları ({len(taslak['siparisler'])})", ""]
    for s in taslak["siparisler"]:
        satir += [f"### {s['tedarikci']}", "", s["metin"].strip(), ""]
    metin_yaz("cikti/taslaklar.md", "\n".join(satir))


def main():
    sadece_betik = "--sadece-betik" in sys.argv
    gecikenler = json_oku("cikti/geciken.json")["odemeler"]
    stok = json_oku("cikti/stok-uyari.json")["urunler"]
    cagrilar = []
    if not gecikenler and not stok:
        taslak, yazan = {"hatirlatmalar": [], "siparisler": []}, "Yapacak iş yok, model çağrılmadı"
    elif sadece_betik:
        taslak, yazan = sablon_taslaklar(gecikenler, stok), "Düz şablon (0 token)"
    else:
        taslak, cagrilar = model_taslaklar(gecikenler, stok)
        yazan = "Sonnet taslağı"
    json_yaz("cikti/taslaklar.json", taslak)
    md_yaz(taslak, gecikenler, yazan)
    maliyet_yaz("yazici", cagrilar)
    usd = sum(c["usd"] for c in cagrilar)
    print(f"    {len(taslak['hatirlatmalar'])} hatırlatma, {len(taslak['siparisler'])} sipariş taslağı"
          f" · {usd:.4f} USD · gönderilen: 0")


if __name__ == "__main__":
    main()
