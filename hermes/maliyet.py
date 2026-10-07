"""Hermes koşusunun maliyet tablosu: Hermes'in --usage-file tahmini + Claude Code devirleri."""
import glob
import json
import os

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(KOK, "cikti", "hermes")


def main():
    satir = ["## Bu koşunun maliyeti", "", "| Mesaj | Kim | Model | USD | Not |", "|---|---|---|---|---|"]
    toplam = 0.0
    for dosya in sorted(glob.glob(os.path.join(H, "kullanim-*.json"))):
        with open(dosya, encoding="utf-8") as f:
            k = json.load(f)
        mid = os.path.basename(dosya)[9:12]
        usd = float(k.get("estimated_cost_usd") or 0)
        toplam += usd
        durum = "tamam" if k.get("completed") and not k.get("failed") else "BAŞARISIZ"
        satir.append(f"| {mid} | Hermes | {k.get('model')} | {usd:.4f} | {k.get('api_calls')} API çağrısı, "
                     f"tahmini ({k.get('cost_status')}), {durum} |")
    devir = os.path.join(H, "claude-devir.jsonl")
    if os.path.exists(devir):
        with open(devir, encoding="utf-8") as f:
            for s in f.read().splitlines():
                d = json.loads(s)
                toplam += d["usd"]
                satir.append(f"| {d['id']} | Claude Code (`claude -p`) | {d['model']} | {d['usd']:.4f} | "
                             "`total_cost_usd` |")
    satir += [f"| **Toplam** | | | **{toplam:.4f}** | |", ""]
    print("\n".join(satir))


if __name__ == "__main__":
    main()
