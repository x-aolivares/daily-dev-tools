#!/usr/bin/env bash
# Uso: ./sync-all.sh <rama_default> [rama_a_actualizar] [commits_a_borrar]
#   ./sync-all.sh master
#   ./sync-all.sh master performance/ABC
#   ./sync-all.sh master performance/ABC 2   # además borra los últimos 2 commits locales

set -u
default_branch="${1:?Falta rama_default (ej: master)}"
update_from_branch="${2:-$default_branch}"
behind_commit_delete="${3:-0}"

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG="$ROOT/sync.log"
: > "$LOG"

log() { echo "[$(date +%T)] [$project] $*" | tee -a "$LOG"; }

sync_project() {
  cd "$ROOT/$project" || return 1
  git fetch origin --prune -q || { log "fetch falló"; return 1; }

  # ¿existe la rama en el remoto? si no, usamos la default
  local target="$default_branch"
  if git ls-remote --exit-code --heads origin "$update_from_branch" >/dev/null 2>&1; then
    target="$update_from_branch"
  else
    log "'$update_from_branch' no existe en remoto -> uso '$default_branch'"
  fi

  # stash solo si hay algo (evita sacar un stash viejo con el pop)
  local stashed=0
  if [[ -n "$(git status --porcelain)" ]]; then
    git stash push -u -m "sync-all $(date +%F_%T)" -q || { log "stash falló"; return 1; }
    stashed=1
  fi

  local err=0

  # moverse a la rama objetivo (sin esto el pull mezclaría otra rama en la actual)
  if git show-ref --verify --quiet "refs/heads/$target"; then
    git checkout -q "$target" || err=1
  else
    git checkout -q -b "$target" "origin/$target" || err=1
  fi

  # borrar N commits locales, con backup por si te arrepientes
  if [[ $err -eq 0 && "$behind_commit_delete" -gt 0 ]]; then
    local backup="backup/sync-$(date +%Y%m%d-%H%M%S)"
    git branch "$backup" && log "backup en '$backup'"
    git reset --hard "HEAD~$behind_commit_delete" -q || err=1
  fi

  if [[ $err -eq 0 ]]; then
    git pull --ff-only -q origin "$target" || { log "pull falló"; err=1; }
  fi

  # devolver tus cambios siempre, aunque algo haya fallado
  if [[ $stashed -eq 1 ]]; then
    if ! git stash pop -q 2>>"$LOG"; then
      mapfile -t conflicts < <(git diff --name-only --diff-filter=U)
      if [[ ${#conflicts[@]} -gt 0 ]]; then
        for f in "${conflicts[@]}"; do
          git checkout --theirs -- "$f" && git reset -q -- "$f"   # theirs = el stash
        done
        git stash drop -q
        log "conflictos resueltos a favor del stash: ${conflicts[*]}"
      else
        log "stash pop falló sin conflictos; tus cambios siguen en 'git stash list'"
        return 1
      fi
    fi
  fi

  [[ $err -eq 0 ]] && log "OK ($target)"
  return $err
}

ok=(); fail=()
for dir in "$ROOT"/common-backend-*/; do
  project="$(basename "$dir")"
  [[ -d "$dir/.git" ]] || continue
  if sync_project; then ok+=("$project"); else fail+=("$project"); fi
done

echo
echo "OK:    ${ok[*]:-ninguno}"
echo "FALLÓ: ${fail[*]:-ninguno}   (detalle en $LOG)"
[[ ${#fail[@]} -eq 0 ]]