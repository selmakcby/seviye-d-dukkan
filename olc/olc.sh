#!/usr/bin/env bash
# Ölçüm: NAİF (Opus ajanı, araçlı) vs HAT (./calistir.sh) vs SADECE BETİK (./calistir.sh --sadece-betik).
# Kullanım: ./olc/olc.sh [N=2]     naif ve hat N kez, sadece betik 1 kez
# Tahmini harcama: naif koşu başına ~0,3-0,8 USD, hat koşu başına ~0,05 USD, betik 0.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(pwd)
N="${1:-2}"
SONUC=olc/sonuclar
mkdir -p "$SONUC"
# Kişisel hook'lar, eklentiler, ses çalan modlar bu koşulara karışmasın:
AYAR='{"disableAllHooks":true}'
unset CLAUDE_CODE_PLUGIN_DIRS

for i in $(seq 1 "$N"); do
  echo "== NAİF $i/$N: Opus'a veri/ klasörünü ver (ajan, Read/Glob/Grep araçlı)"
  # Ajan cevap anahtarını göremesin diye veri geçici bir klasöre kopyalanır.
  GECICI=$(mktemp -d)
  cp -R veri "$GECICI/veri" && cp sss.md "$GECICI/" && rm -f "$GECICI/veri/cevap-anahtari.json"
  BAS=$(date +%s)
  ( cd "$GECICI" && claude -p "$(cat "$REPO/olc/naif-prompt.txt")" --model opus \
      --tools Read,Glob,Grep --allowedTools Read Glob Grep \
      --output-format json --setting-sources project --settings "$AYAR" \
      --strict-mcp-config --no-session-persistence --max-budget-usd 1.0 ) \
      > "$SONUC/naif-$i.ham.json" || true
  SON=$(date +%s)
  rm -rf "$GECICI"
  python3 olc/kaydet.py naif "$i" "$SONUC/naif-$i.ham.json" $((SON - BAS))

  echo "== HAT $i/$N: betik -> Haiku bekçi -> Sonnet masa ve yazıcı"
  BAS=$(date +%s)
  ./calistir.sh > /dev/null
  SON=$(date +%s)
  python3 olc/kaydet.py hat "$i" cikti/maliyet.json $((SON - BAS))
done

echo "== SADECE BETİK: 0 token"
BAS=$(date +%s)
./calistir.sh --sadece-betik > /dev/null
SON=$(date +%s)
python3 olc/kaydet.py betik 1 cikti/maliyet.json $((SON - BAS))
./calistir.sh > /dev/null   # cikti/ yeniden tam hattın çıktısı olsun
python3 olc/tablo.py
echo "Tablo: olc/SONUC.md"
