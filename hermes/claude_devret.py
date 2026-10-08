"""Hermes -> Claude Code devri: zor müşteri sorusuna `claude -p --model sonnet` ile taslak.

Hermes bu komutu `claude-code` skill'inin print modu yoluyla çalıştırır:
    python3 hermes/claude_devret.py 018
Neden sarmalayıcı? Hermes'in yazdığı serbest bir `claude -p` satırı kişisel ayarları ve hook'ları
(ses çalan Stop hook'u gibi) yükleyebilir. Burada çağrı araçsız, hook'suz ve bütçe tavanlı.
Maliyet cikti/hermes/claude-devir.jsonl dosyasına eklenir.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "betik"))
from masa import sss_oku  # noqa: E402
from olay import olay  # noqa: E402
from ortak import KOK, mesaj_oku, metin_oku, veri_blogu, yalin_cagri, json_ayikla  # noqa: E402


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"\d{3}", sys.argv[1]):
        raise SystemExit("Kullanım: python3 hermes/claude_devret.py <3 haneli mesaj id>, örnek: 018")
    dosya = os.path.join(KOK, "veri", "mesajlar", f"{sys.argv[1]}.md")
    if not os.path.exists(dosya):
        raise SystemExit(f"Mesaj bulunamadı: veri/mesajlar/{sys.argv[1]}.md")
    m = mesaj_oku(dosya)
    _, bilgi = sss_oku()
    sistem = metin_oku("betik/promptlar/masa.txt").replace("{bilgi}", bilgi)
    olay("claude", "basladi", f"{m['id']} Hermes'ten devir · claude -p (sonnet)")
    c = yalin_cagri("sonnet", sistem, veri_blogu(m), butce_usd=0.2)
    taslak = (json_ayikla(c["metin"]) or {}).get("taslaklar", {}).get(m["id"], "").strip()
    os.makedirs(os.path.join(KOK, "cikti", "hermes"), exist_ok=True)
    with open(os.path.join(KOK, "cikti", "hermes", "claude-devir.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": m["id"], "model": c["model"], "usd": round(c["usd"], 5),
                            "sure_sn": round(c["sure"], 1)}) + "\n")
    olay("claude", "bitti", f"{m['id']} taslak " + ("hazır" if taslak else "alınamadı"), maliyet=c["usd"])
    if not taslak:
        raise SystemExit("Claude Code taslak döndürmedi. Bu mesajı insana işaretle.")
    print(f"[claude -p · {c['model']} · {c['usd']:.4f} USD]")
    print(taslak)


if __name__ == "__main__":
    main()
