#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  RETOUR ARRIÈRE — restaure l'ancien design (données jamais touchées)
# ════════════════════════════════════════════════════════════════
set -euo pipefail
COMPOSE="${COMPOSE:-docker compose}"
WEB_SERVICE="web"
HEALTH_URL="${HEALTH_URL:-https://events.laspad.org/}"
cd "$(git rev-parse --show-toplevel)"

if [ ! -f .deploy/last_commit ]; then
  echo "❌ Aucun point de retour enregistré (.deploy/last_commit introuvable)."
  echo "   Retour manuel : git reset --hard <commit_precedent> && $COMPOSE up -d --build $WEB_SERVICE"
  exit 1
fi
PREV="$(cat .deploy/last_commit)"
printf "\n\033[1;33m→ Retour à l'état précédent : %s\033[0m\n" "${PREV:0:12}"
git reset --hard "$PREV"
echo "→ Reconstruction du conteneur web..."
$COMPOSE up -d --build "$WEB_SERVICE"
$COMPOSE exec -T "$WEB_SERVICE" python manage.py collectstatic --noinput >/dev/null || true
sleep 5
CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$HEALTH_URL" || echo 000)"
printf "\n\033[1;32m✅ Ancien design restauré (HTTP %s). Tes données n'ont JAMAIS été touchées.\033[0m\n" "$CODE"
