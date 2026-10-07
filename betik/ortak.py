"""Ortak parçalar: veri okuma, Claude'a yalın çağrı, JSON ayıklama, maliyet kaydı.

Sadece Python standart kütüphanesi kullanılır; kurulacak paket yok.
"""
import csv
import glob
import json
import os
import re
import subprocess
import time
from datetime import date

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESAJ_SINIRI = 1200  # modele giden tek mesaj en fazla bu kadar karakter


# ---------------------------------------------------------------- dosyalar
def yol(goreli):
    return os.path.join(KOK, goreli)


def json_oku(goreli, varsayilan=None):
    try:
        with open(yol(goreli), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if varsayilan is not None:
            return varsayilan
        raise SystemExit(f"Dosya bulunamadı: {goreli} (önce ./calistir.sh çalıştı mı?)")


def json_yaz(goreli, veri):
    os.makedirs(os.path.dirname(yol(goreli)), exist_ok=True)
    with open(yol(goreli), "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)


def metin_oku(goreli):
    with open(yol(goreli), encoding="utf-8") as f:
        return f.read().strip()


def metin_yaz(goreli, metin):
    os.makedirs(os.path.dirname(yol(goreli)), exist_ok=True)
    with open(yol(goreli), "w", encoding="utf-8") as f:
        f.write(metin.rstrip() + "\n")


def csv_oku(goreli):
    if not os.path.exists(yol(goreli)):
        raise SystemExit(f"Tablo bulunamadı: {goreli}")
    with open(yol(goreli), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ayar():
    return json_oku("veri/ayar.json")


def bugun():
    """veri/ayar.json > bugun doluysa o tarih (örnek veri), boşsa gerçek bugün."""
    deger = ayar().get("bugun", "")
    return date.fromisoformat(deger) if deger else date.today()


def kucuk(metin):
    """Türkçe küçük harf: İ -> i, I -> ı."""
    return metin.replace("İ", "i").replace("I", "ı").lower()


# ---------------------------------------------------------------- mesajlar
def mesaj_oku(dosya):
    """`anahtar: değer` başlıkları, `---`, sonra mesaj metni."""
    with open(dosya, encoding="utf-8") as f:
        ham = f.read()
    bas, _, govde = ham.partition("\n---\n")
    alanlar = dict(s.split(": ", 1) for s in bas.splitlines() if ": " in s)
    return {"id": os.path.splitext(os.path.basename(dosya))[0],
            "kanal": alanlar.get("kanal", "?"), "kimden": alanlar.get("kimden", "?"),
            "tarih": alanlar.get("tarih", ""), "metin": govde.strip()}


def mesajlar_oku(klasor="veri/mesajlar"):
    dosyalar = sorted(glob.glob(os.path.join(yol(klasor), "*.md")))
    return [mesaj_oku(d) for d in dosyalar]


def veri_blogu(m):
    """Mesaj modele VERİ olarak gider: etiket içine sarılır, etiketi kıracak metin temizlenir."""
    temiz = re.sub(r"</?\s*mesaj[^>]*>", "[etiket silindi]", m["metin"][:MESAJ_SINIRI], flags=re.I)
    return (f'<mesaj id="{m["id"]}" kanal="{m["kanal"]}">\n'
            f'Kimden: {m["kimden"]}\n---\n{temiz}\n</mesaj>')


# ---------------------------------------------------------------- Claude çağrısı
def yalin_cagri(model, sistem, girdi, butce_usd=0.5):
    """Araçsız, kısa system prompt'lu tek çağrı: `claude -p --model <model>`.

    - --tools ""                 : hiçbir araç yok (dosya okuyamaz, komut çalıştıramaz, gönderemez)
    - --system-prompt            : Claude Code'un uzun ajan prompt'u yerine bizimki
    - --setting-sources project  : kişisel ayarlar ve hook'lar yüklenmez
    - claudeMdExcludes           : kişisel CLAUDE.md'ler bu çağrıya karışmaz
    - alwaysThinkingEnabled=false: sınıflama için "düşünme" token'ı harcanmaz
    Dönüş: {"metin", "usd", "sure", "model"}
    """
    ayarlar = {"disableAllHooks": True, "alwaysThinkingEnabled": False,
               "claudeMdExcludes": ["**/CLAUDE.md", "**/.claude/rules/**", "**/CLAUDE.local.md"]}
    komut = ["claude", "-p", "--model", model, "--system-prompt", sistem,
             "--tools", "", "--output-format", "json",
             "--setting-sources", "project", "--settings", json.dumps(ayarlar),
             "--strict-mcp-config", "--disable-slash-commands",
             "--no-session-persistence", "--max-budget-usd", str(butce_usd)]
    ortam = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_PLUGIN_DIRS"}
    ortam["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    bas = time.time()
    try:
        sonuc = subprocess.run(komut, input=girdi, capture_output=True, text=True,
                               timeout=300, env=ortam, cwd=KOK)
    except FileNotFoundError:
        raise SystemExit("`claude` komutu bulunamadı. Claude Code kurulu mu? (README > Gereksinimler)")
    except subprocess.TimeoutExpired:
        print(f"  ! {model} çağrısı 300 sn içinde bitmedi")
        return {"metin": "", "usd": 0.0, "sure": time.time() - bas, "model": model}
    return _cevap_coz(sonuc, model, time.time() - bas)


def _cevap_coz(sonuc, model, sure):
    try:
        veri = json.loads(sonuc.stdout)
    except json.JSONDecodeError:
        hata = (sonuc.stderr or sonuc.stdout).strip()[:300]
        print(f"  ! Claude çağrısı JSON dönmedi: {hata}")
        return {"metin": "", "usd": 0.0, "sure": sure, "model": model}
    if veri.get("is_error"):
        print(f"  ! Claude çağrısı hata döndü: {str(veri.get('result', ''))[:200]}")
    modeller = list(veri.get("modelUsage", {}).keys())
    return {"metin": veri.get("result", "") or "", "usd": float(veri.get("total_cost_usd", 0.0)),
            "sure": sure, "model": modeller[0] if modeller else model}


def json_ayikla(metin):
    """Model cevabındaki JSON nesnesini bulur (``` çitleri olsa da). Bulamazsa None."""
    if not metin:
        return None
    metin = re.sub(r"^```(?:json)?\s*|\s*```$", "", metin.strip())
    bas, son = metin.find("{"), metin.rfind("}")
    if bas == -1 or son <= bas:
        return None
    try:
        return json.loads(metin[bas:son + 1])
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- maliyet
def maliyet_yaz(rol, cagrilar):
    """Bu rolün bu koşudaki çağrılarını cikti/maliyet-<rol>.json'a yazar (0 çağrı = 0 token)."""
    json_yaz(f"cikti/maliyet-{rol}.json", {
        "rol": rol,
        "cagrilar": [{"model": c["model"], "usd": round(c["usd"], 5), "sure_sn": round(c["sure"], 1)}
                     for c in cagrilar],
    })


def para(tutar):
    """12500 -> '12.500'"""
    return f"{int(round(float(tutar))):,}".replace(",", ".")
