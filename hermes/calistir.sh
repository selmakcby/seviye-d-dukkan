#!/usr/bin/env bash
# Hermes müşteri masası: 3 örnek mesajı terminalden sırayla sorar. Hiçbir şey gönderilmez.
#   ./hermes/calistir.sh               # 002 (kalıp) 018 (zor -> Claude Code) 012 (tuzak)
#   ./hermes/calistir.sh 004 028       # istediğin mesajlar
# Model: Hermes'in ayarına dokunmadan bu koşu için Haiku. Değiştirmek için:
#   HERMES_MODEL=claude-sonnet-5 ./hermes/calistir.sh
# Hermes yoksa ya da çalışmazsa ana hat (./calistir.sh) Hermes'siz çalışmaya devam eder.
set -euo pipefail
cd "$(dirname "$0")/.."
MODEL="${HERMES_MODEL:-claude-haiku-4-5}"
SAGLAYICI="${HERMES_PROVIDER:-anthropic}"
IDLER=("$@"); [ ${#IDLER[@]} -eq 0 ] && IDLER=(002 018 012)
CIKTI=cikti/hermes-masa.md
command -v hermes >/dev/null || { echo "Hermes kurulu değil. Hermes isteğe bağlı; ana hat: ./calistir.sh"; exit 0; }
unset CLAUDE_CODE_PLUGIN_DIRS
mkdir -p cikti/hermes
rm -f cikti/hermes/*.json cikti/hermes/claude-devir.jsonl
{ echo "# Hermes müşteri masası · $(date '+%d.%m.%Y %H:%M')"; echo
  echo "> Hermes ($MODEL, $SAGLAYICI) + claude-code skill'i. Zor soru \`claude -p --model sonnet\` ile Claude Code'a devredilir."
  echo "> **Hiçbir şey gönderilmedi.** Telegram'a bağlamak Hermes'in kendi gateway ayarıdır; bu demo terminalden çalışır."
  echo; } > "$CIKTI"
for ID in "${IDLER[@]}"; do
  DOSYA="veri/mesajlar/$ID.md"
  [ -f "$DOSYA" ] || { echo "Mesaj yok: $DOSYA"; exit 1; }
  echo "== Hermes'e soruluyor: $ID"
  ISTEM="$(cat hermes/MASA.md)

## Kalıp cevap şablonları (sss.md)
$(sed -n '/^## kalip:/,/^## bilgi/p' sss.md | sed '$d')

REPO: $(pwd)

## Gelen mesaj
<mesaj id=\"$ID\">
$(sed '1,/^---$/d' "$DOSYA")
</mesaj>"
  BAS=$(date +%s)
  CEVAP=$(hermes -z "$ISTEM" -m "$MODEL" --provider "$SAGLAYICI" -t terminal,skills -s claude-code \
            --usage-file "cikti/hermes/kullanim-$ID.json" 2>&1) || CEVAP="HATA: hermes çıkış kodu sıfır değil
$CEVAP"
  SURE=$(( $(date +%s) - BAS ))
  CEVAP=$(printf '%s\n' "$CEVAP" | grep -v '^```' | sed '/^[[:space:]]*$/d')
  echo "$CEVAP"
  { echo "## $ID · $(sed -n 's/^kimden: //p' "$DOSYA") · $(sed -n 's/^kanal: //p' "$DOSYA") · ${SURE} sn"
    echo; echo "> $(sed '1,/^---$/d' "$DOSYA" | tr '\n' ' ' | cut -c1-220)"; echo
    echo '```'; echo "$CEVAP"; echo '```'; echo; } >> "$CIKTI"
done
python3 hermes/maliyet.py >> "$CIKTI"
echo; tail -8 "$CIKTI"; echo "Hazır: $CIKTI"
