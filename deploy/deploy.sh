#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  DÉPLOIEMENT LASPAD EVENT — nouvelle charte (couche présentation)
#  Ne touche QUE le code (templates + images). Base & médias intacts.
#  Réversible à tout moment via ./deploy/rollback.sh
# ════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Configuration (ajuste si besoin) ──────────────────────────────
COMPOSE="${COMPOSE:-docker compose}"     # ou "docker-compose" si version v1
DB_SERVICE="db"
WEB_SERVICE="web"
BRANCH="main"
# URL testée après déploiement (mets ton vrai domaine) :
HEALTH_URL="${HEALTH_URL:-https://events.laspad.org/}"
# ──────────────────────────────────────────────────────────────────

cd "$(git rev-parse --show-toplevel)"                         # racine du repo
[ -f .env ] && set -a && . ./.env && set +a || true
DB_NAME="${DB_NAME:-laspad_event}"; DB_USER="${DB_USER:-laspad_user}"; DB_PASSWORD="${DB_PASSWORD:-}"
mkdir -p backups .deploy
TS="$(date +%F_%H%M%S)"
say(){ printf "\n\033[1;36m%s\033[0m\n" "$*"; }
ok(){ printf "   \033[1;32m✅ %s\033[0m\n" "$*"; }
warn(){ printf "   \033[1;33m⚠️  %s\033[0m\n" "$*"; }

say "════ DÉPLOIEMENT LASPAD EVENT — $TS ════"

# 1) Point de retour AVANT toute modif
PREV_COMMIT="$(git rev-parse HEAD)"
echo "$PREV_COMMIT" > .deploy/last_commit
ok "Point de retour enregistré : ${PREV_COMMIT:0:12}"

# 2) Sauvegarde de la base (filet de sécurité)
say "→ Sauvegarde de la base de données..."
$COMPOSE exec -T -e PGPASSWORD="$DB_PASSWORD" "$DB_SERVICE" \
  pg_dump -U "$DB_USER" "$DB_NAME" > "backups/backup_$TS.sql"
ok "Sauvegarde : backups/backup_$TS.sql ($(du -h "backups/backup_$TS.sql" | cut -f1))"

# 3) Récupération du nouveau code
say "→ Récupération du nouveau code ($BRANCH)..."
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
ok "Code à jour : $(git rev-parse --short HEAD)"

# 4) Reconstruction du conteneur web UNIQUEMENT (base 'db' non touchée)
say "→ Reconstruction du conteneur web (la base n'est pas touchée)..."
$COMPOSE up -d --build "$WEB_SERVICE"

# 5) Fichiers statiques (logo, photo hero)
say "→ Collecte des fichiers statiques..."
$COMPOSE exec -T "$WEB_SERVICE" python manage.py collectstatic --noinput >/dev/null
ok "Statiques collectés"

# 6) Migrations (aucune attendue — no-op, lancé par rigueur)
say "→ Migrations (aucune attendue)..."
$COMPOSE exec -T "$WEB_SERVICE" python manage.py migrate --noinput

# 7) Vérification santé + retour arrière AUTOMATIQUE si échec
say "→ Vérification que le site répond..."
sleep 5
CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$HEALTH_URL" || echo 000)"
if [ "$CODE" = "200" ] || [ "$CODE" = "302" ] || [ "$CODE" = "301" ]; then
  ok "Site OK (HTTP $CODE)"
  say "════ ✅ DÉPLOIEMENT RÉUSSI ════"
  echo "   Nouveau design en ligne. Contenu & données 100% intacts."
  echo "   Retour arrière possible à tout moment : ./deploy/rollback.sh"
else
  warn "Le site ne répond pas correctement (HTTP $CODE) — RETOUR ARRIÈRE AUTOMATIQUE..."
  git reset --hard "$PREV_COMMIT"
  $COMPOSE up -d --build "$WEB_SERVICE"
  $COMPOSE exec -T "$WEB_SERVICE" python manage.py collectstatic --noinput >/dev/null || true
  warn "Ancien design restauré automatiquement. Tes données n'ont jamais été touchées."
  echo "   (Sauvegarde de secours disponible : backups/backup_$TS.sql)"
  exit 1
fi
