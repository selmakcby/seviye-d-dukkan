"""Bir ölçüm koşusunu olc/sonuclar/<yol>-<n>.json olarak özetler (maliyet, süre, doğruluk)."""
import json
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "betik"))
from ortak import json_ayikla  # noqa: E402
from puanla import hat_puani, puanla  # noqa: E402


def son_json(metin):
    """Metindeki son {"mesajlar": ...} bloğunu bulur."""
    yer = metin.rfind('"mesajlar"')
    bas = metin.rfind("{", 0, yer) if yer != -1 else -1
    if bas == -1:
        return {}
    try:
        return json.JSONDecoder().raw_decode(metin[bas:])[0]
    except json.JSONDecodeError:
        return json_ayikla(metin) or {}


def naif(ham_yol):
    with open(ham_yol, encoding="utf-8") as f:
        d = json.load(f)
    v = son_json(d.get("result", ""))
    turler = v.get("mesajlar", {}) if isinstance(v.get("mesajlar"), dict) else {}
    p = puanla(turler, v.get("esik_alti", []), v.get("geciken", []))
    dagilim = {m: round(u.get("costUSD", 0), 4) for m, u in d.get("modelUsage", {}).items()}
    return {"usd": d.get("total_cost_usd", 0.0), "cagri": d.get("num_turns"), "hata": d.get("is_error", False),
            "modeller": dagilim, "puan": p}


def hat(maliyet_yol):
    with open(maliyet_yol, encoding="utf-8") as f:
        m = json.load(f)
    dagilim = {}
    for r in m["roller"]:
        if r["cagri"]:
            dagilim[r["model"]] = round(dagilim.get(r["model"], 0) + r["usd"], 4)
    return {"usd": m["toplam_usd"], "cagri": m["cagri"], "hata": False, "modeller": dagilim, "puan": hat_puani()}


if __name__ == "__main__":
    yol, n, kaynak, sure = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    kayit = naif(kaynak) if yol == "naif" else hat(kaynak)
    kayit.update({"yol": yol, "kos": int(n), "sure_sn": sure})
    with open(os.path.join(KOK, "olc", "sonuclar", f"{yol}-{n}.json"), "w", encoding="utf-8") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=2)
    p = kayit["puan"] or {}
    print(f"   {yol} {n}: {kayit['usd']:.4f} USD · {sure} sn · tür {p.get('tur_dogru')}/{p.get('tur_toplam')}"
          f" · uyarı {p.get('uyari_dogru')}/{p.get('uyari_toplam')} · tuzak {p.get('tuzak')}")
