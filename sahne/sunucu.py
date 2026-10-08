"""Sahne sunucusu: ajanları çalışırken tarayıcıda izle.

    python3 sahne/sunucu.py          # http://127.0.0.1:8796
    python3 sahne/sunucu.py --ac     # Safari'de de açar

Sadece okur: cikti/olaylar.jsonl (betik/olay.py yazar) + sahne dosyaları. Hiçbir yere yazmaz.
Sadece standart kütüphane; yalnız 127.0.0.1'e bağlanır.
"""
import json
import os
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ADRES, PORT = "127.0.0.1", 8796
SAHNE = os.path.dirname(os.path.abspath(__file__))
OLAYLAR = os.path.join(os.path.dirname(SAHNE), "cikti", "olaylar.jsonl")
GORSELLER = os.path.join(SAHNE, "gorseller")
DOSYALAR = {"/": ("sahne.html", "text/html; charset=utf-8"),
            "/sahne.js": ("sahne.js", "text/javascript; charset=utf-8")}


def olaylari_oku():
    """Dosyadaki geçerli satırlar; dosya yoksa boş liste. Bozuk satır atlanır."""
    try:
        with open(OLAYLAR, encoding="utf-8") as f:
            satirlar = f.read().splitlines()
    except FileNotFoundError:
        return []
    sonuc = []
    for s in satirlar:
        try:
            sonuc = [*sonuc, json.loads(s)] if s.strip() else sonuc
        except json.JSONDecodeError:
            continue
    return sonuc


def yeni_olaylar(since):
    """since'ten sonraki olaylar. Dosya sıfırlandıysa (koşu yeniden başladı) baştan, sifirla=True."""
    hepsi = olaylari_oku()
    sifirla = since > len(hepsi)
    bas = 0 if sifirla else since
    return {"olaylar": hepsi[bas:], "toplam": len(hepsi), "sifirla": sifirla}


class Isleyici(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/olaylar":
            self._olaylar(url.query)
        elif url.path in DOSYALAR:
            ad, tur = DOSYALAR[url.path]
            self._dosya(os.path.join(SAHNE, ad), tur)
        elif url.path.startswith("/gorseller/"):
            self._gorsel(url.path[len("/gorseller/"):])
        else:
            self._gonder(404, b"yok", "text/plain; charset=utf-8")

    def _olaylar(self, sorgu):
        try:
            since = max(0, int(parse_qs(sorgu).get("since", ["0"])[0]))
        except ValueError:
            since = 0
        govde = json.dumps(yeni_olaylar(since), ensure_ascii=False).encode("utf-8")
        self._gonder(200, govde, "application/json; charset=utf-8")

    def _gorsel(self, ad):
        # yol aşımı yok: yalnız düz .png adı, klasör ayracı yok
        if "/" in ad or "\\" in ad or ".." in ad or not ad.endswith(".png"):
            self._gonder(404, b"yok", "text/plain; charset=utf-8")
            return
        self._dosya(os.path.join(GORSELLER, ad), "image/png")

    def _dosya(self, yol, tur):
        try:
            with open(yol, "rb") as f:
                self._gonder(200, f.read(), tur)
        except FileNotFoundError:
            self._gonder(404, b"yok", "text/plain; charset=utf-8")

    def _gonder(self, kod, govde, tur):
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def log_message(self, *_):
        pass  # her saniyelik /olaylar isteği terminali doldurmasın


def main():
    adres = f"http://{ADRES}:{PORT}"
    try:
        sunucu = ThreadingHTTPServer((ADRES, PORT), Isleyici)
    except OSError as hata:
        raise SystemExit(f"{PORT} portu açılamadı ({hata}). Sahne zaten açık olabilir: {adres}")
    print(f"Sahne: {adres}  (kapatmak için Ctrl+C)")
    print("Başka bir terminalde: ./calistir.sh   sonra   ./hermes/calistir.sh")
    if "--ac" in sys.argv:
        if sys.platform == "darwin":
            subprocess.run(["open", "-a", "Safari", adres], check=False)
        else:
            webbrowser.open(adres)
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nSahne kapandı.")


if __name__ == "__main__":
    main()
