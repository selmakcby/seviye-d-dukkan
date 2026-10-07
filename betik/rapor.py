"""Rol: YÖNETİCİ. Bütün rollerin çıktısını tek sabah raporunda toplar (0 token).

Sıra: acil/insana -> stok -> geciken ödemeler -> zor soru taslakları -> mesaj taslakları
      -> kalıp cevaplar -> bu koşunun maliyeti.
Çıktı: cikti/sabah-raporu.md, cikti/maliyet.json, cikti/kosu-gecmisi.jsonl (boş koşu sayacı)
"""
import json
import os
from datetime import datetime

from ortak import ayar, bugun, json_oku, json_yaz, metin_yaz, para, yol
from puanla import hat_puani, satir as puan_satiri

ROLLER = [("stok-odeme", "Stok ve ödeme betiği"), ("bekci", "Bekçi"), ("masa", "Müşteri masası"),
          ("yazici", "Mesaj yazıcı")]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim",
         "Kasım", "Aralık"]


def virgul(x, b=1):
    return f"{x:.{b}f}".replace(".", ",")


def kisa(metin, n=90):
    metin = " ".join(metin.split())
    return metin if len(metin) <= n else metin[:n - 1] + "…"


def acil_bolumu(cevaplar):
    secili = [(i, k) for i, k in cevaplar.items() if k["tur"] in ("tuzak", "insana")]
    secili.sort(key=lambda x: x[1]["tur"] != "tuzak")
    s = [f"## 1. ACİL · insana devredilenler ({len(secili)})", "",
         "Bunlara model cevap yazmadı. Karar senin.", "",
         "| # | Tür | Kimden | Kanal | Neden | Mesaj |", "|---|---|---|---|---|---|"]
    for i, k in secili:
        tur = "TUZAK (talimat enjeksiyonu)" if k["tur"] == "tuzak" else "insana"
        s.append(f"| {i} | {tur} | {k['kimden']} | {k['kanal']} | {k['neden']} | {kisa(k['metin'])} |")
    return s + [""]


def stok_bolumu(stok):
    s = [f"## 2. Stok uyarıları ({len(stok)})", "",
         "Kural: eldeki < günlük satış × (tedarik süresi + tampon). Hesap betikte, model yok.", "",
         "| Ürün | Eldeki | Eşik | Kaç gün yeter | Önerilen sipariş | Tedarikçi |", "|---|---|---|---|---|---|"]
    for u in stok:
        s.append(f"| {u['urun']} | {u['eldeki']} | {virgul(u['esik'])} | {virgul(u['kac_gun_yeter'] or 0)} | "
                 f"{u['onerilen_siparis']} | {u['tedarikci']} |")
    return s + [""]


def odeme_bolumu(gec):
    toplam = sum(o["tutar_tl"] for o in gec)
    s = [f"## 3. Geciken ödemeler ({len(gec)} · {para(toplam)} TL)", "",
         "| Fatura | Müşteri | Tutar | Vade | Gecikme |", "|---|---|---|---|---|"]
    s += [f"| {o['id']} | {o['musteri']} | {para(o['tutar_tl'])} TL | {o['vade']} | {o['gecikme_gun']} gün |"
          for o in gec]
    return s + [""]


def zor_bolumu(cevaplar):
    zor = [(i, k) for i, k in cevaplar.items() if k["tur"] == "zor"]
    s = [f"## 4. Zor sorular · cevap taslakları ({len(zor)})", ""]
    for i, k in zor:
        s += [f"**{i} · {k['kimden']}** ({k['kanal']}): _{kisa(k['metin'], 140)}_", "", f"> {k['cevap']}", ""]
    return s


def taslak_bolumu(t):
    s = [f"## 5. Mesaj taslakları ({len(t['hatirlatmalar'])} hatırlatma, {len(t['siparisler'])} sipariş)", "",
         "Tam metinler: `cikti/taslaklar.md`.", ""]
    s += [f"- **{h['id']}**: {kisa(h['metin'], 160)}" for h in t["hatirlatmalar"]]
    s += [f"- **{x['tedarikci']}**: {kisa(x['metin'], 160)}" for x in t["siparisler"]]
    return s + [""]


def kalip_bolumu(cevaplar):
    kalip = [(i, k) for i, k in cevaplar.items() if k["tur"] == "kalip"]
    sayac = {}
    for _, k in kalip:
        sayac[k["konu"]] = sayac.get(k["konu"], 0) + 1
    dagilim = ", ".join(f"{k} {v}" for k, v in sorted(sayac.items()))
    return [f"## 6. Kalıp sorular · şablon cevap hazır ({len(kalip)})", "",
            f"{dagilim}. Hepsi `sss.md` şablonundan, 0 token. Tam metinler: `cikti/cevaplar.md`.", ""]


def maliyet_topla():
    """cikti/maliyet-<rol>.json dosyalarını toplar. Dönüş: (satırlar, toplam_usd, toplam_cagri)."""
    satirlar, toplam, cagri = [], 0.0, 0
    for rol, ad in ROLLER:
        veri = json_oku(f"cikti/maliyet-{rol}.json", varsayilan={"cagrilar": []})
        c = veri["cagrilar"]
        usd = sum(x["usd"] for x in c)
        modeller = ", ".join(sorted({x["model"] for x in c})) or "model yok"
        satirlar.append({"rol": ad, "model": modeller, "cagri": len(c), "usd": usd,
                         "sure": sum(x["sure_sn"] for x in c)})
        toplam, cagri = toplam + usd, cagri + len(c)
    return satirlar, toplam, cagri


def gecmis_yaz(toplam, is_sayisi):
    """Boş koşu sayacı: her koşu bir satır; son 10 koşunun kaçı boştu?"""
    dosya = yol("cikti/kosu-gecmisi.jsonl")
    with open(dosya, "a", encoding="utf-8") as f:
        f.write(json.dumps({"zaman": datetime.now().isoformat(timespec="seconds"),
                            "usd": round(toplam, 5), "is": is_sayisi}) + "\n")
    with open(dosya, encoding="utf-8") as f:
        son = [json.loads(s) for s in f.read().splitlines() if s.strip()][-10:]
    return len(son), sum(1 for k in son if k["is"] == 0)


def maliyet_bolumu(satirlar, toplam, cagri, is_sayisi):
    tavan = ayar().get("butce_tavani_usd", 0.5)
    s = ["## Bu koşunun maliyeti", "",
         "| Rol | Model | Çağrı | USD | Süre (sn) |", "|---|---|---|---|---|"]
    s += [f"| {r['rol']} | {r['model']} | {r['cagri']} | {virgul(r['usd'], 4)} | {r['sure']:.0f} |" for r in satirlar]
    s += [f"| **Toplam** | | **{cagri}** | **{virgul(toplam, 4)}** | |", ""]
    s.append(f"Bütçe tavanı {virgul(tavan, 2)} USD: " + ("**AŞILDI, kontrol et.**" if toplam > tavan else "altında."))
    kos, bos = gecmis_yaz(toplam, is_sayisi)
    s.append(f"Boş koşu sayacı: son {kos} koşunun {bos} tanesinde yapacak iş yoktu.")
    s += ["", "USD = `claude -p --output-format json` çıktısındaki `total_cost_usd` (abonelikte API karşılığı)."]
    return s


def ozet_satiri(cevaplar, stok, gec):
    say = lambda t: sum(1 for k in cevaplar.values() if k["tur"] == t)  # noqa: E731
    hazir = sum(1 for k in cevaplar.values() if k["cevap"])
    return (f"> {len(cevaplar)} mesaj · {hazir} cevap taslağı hazır · **{say('tuzak') + say('insana')} insana** · "
            f"{len(stok)} stok uyarısı · {len(gec)} geciken ödeme. **Hiçbir şey gönderilmedi.**")


def main():
    cevaplar = json_oku("cikti/cevaplar.json")
    stok = json_oku("cikti/stok-uyari.json")["urunler"]
    gec = json_oku("cikti/geciken.json")["odemeler"]
    taslak = json_oku("cikti/taslaklar.json")
    g = bugun()
    s = [f"# Sabah raporu · Sırça Seramik · {g.day} {AYLAR[g.month - 1]} {g.year}", "",
         ozet_satiri(cevaplar, stok, gec), ""]
    s += acil_bolumu(cevaplar) + stok_bolumu(stok) + odeme_bolumu(gec) + zor_bolumu(cevaplar)
    s += taslak_bolumu(taslak) + kalip_bolumu(cevaplar)
    satirlar, toplam, cagri = maliyet_topla()
    s += maliyet_bolumu(satirlar, toplam, cagri, len(cevaplar) + len(stok) + len(gec))
    if os.path.exists(yol("veri/cevap-anahtari.json")):
        s += ["", puan_satiri(hat_puani())]
    metin_yaz("cikti/sabah-raporu.md", "\n".join(s))
    json_yaz("cikti/maliyet.json", {"toplam_usd": round(toplam, 5), "cagri": cagri,
                                    "roller": satirlar})
    print(f"Hazır: cikti/sabah-raporu.md · toplam {toplam:.4f} USD · {cagri} model çağrısı · gönderilen: 0")


if __name__ == "__main__":
    main()
