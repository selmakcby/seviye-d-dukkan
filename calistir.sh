#!/usr/bin/env bash
# Dükkanın sabah koşusu. Tek komut:
#   ./calistir.sh                 tam hat: betik + Haiku bekçi + Sonnet masa/yazıcı
#   ./calistir.sh --sadece-betik  0 token: kurallar + şablonlar, model hiç çağrılmaz
# Hiçbir mesaj gönderilmez. Sonuç: cikti/sabah-raporu.md
set -euo pipefail
cd "$(dirname "$0")"
MOD="${1:-}"
if [ -n "$MOD" ] && [ "$MOD" != "--sadece-betik" ]; then
  echo "Bilinmeyen seçenek: $MOD  (kullanım: ./calistir.sh [--sadece-betik])"; exit 1
fi
command -v python3 >/dev/null || { echo "Python 3 bulunamadı. README > Gereksinimler"; exit 1; }
if [ -z "$MOD" ]; then
  command -v claude >/dev/null || { echo "Claude Code (claude) bulunamadı. README > Gereksinimler"; exit 1; }
fi
mkdir -p cikti
rm -f cikti/maliyet*.json cikti/siniflar.json cikti/cevaplar.* cikti/taslaklar.* \
      cikti/stok-uyari.json cikti/geciken.json cikti/sabah-raporu.md
cd betik
echo "[1] Stok ve ödeme betiği (0 token)"
python3 stok_odeme.py
if [ -z "$MOD" ]; then
  echo "[2] Bekçi · Haiku: mesajları sınıflıyor (mesaj = veri, talimat değil)"
  python3 bekci.py
  echo "[3] Müşteri masası: kalıp sorular şablondan, zor sorular Sonnet taslağı"
  python3 masa.py
  echo "[4] Mesaj yazıcı · Sonnet: ödeme hatırlatma + sipariş taslakları"
  python3 yazici.py
else
  echo "[2] Bekçi · sadece kurallar (0 token)"
  python3 bekci.py --kural
  echo "[3] Müşteri masası: sadece şablonlar (0 token)"
  python3 masa.py --sadece-betik
  echo "[4] Mesaj yazıcı: düz şablon (0 token)"
  python3 yazici.py --sadece-betik
fi
echo "[5] Yönetici: sabah raporu"
python3 rapor.py
python3 puanla.py
