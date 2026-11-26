#!/usr/bin/env bash
# Uso: ./sync-projects.sh <rama_default> [rama_a_actualizar] [commits_a_borrar]
# Ejemplo:
#   sh sync-projects.sh development performance/springboot-4.2.0-upgrade

set -u
default_branch="${1:?Falta rama_default (ej: development)}"
update_from_branch="${2:-$default_branch}"
behind_commit_delete="${3:-0}"

# Directorio desde donde se ejecuta el script
ROOT="$(pwd)"
LOG="$ROOT/sync.log"
: > "$LOG"

log() { echo "[$(date +%T)] [$project] $*" | tee -a "$LOG"; }

sync_project() {
  cd "$dir" || return 1
  git fetch origin --prune -q || { log "fetch falló"; return 1; }

  # ¿Existe la rama en el remoto? Si no, usar la rama default
  local target="$default_branch"
  if git ls-remote --exit-code --heads origin "$update_from_branch" >/dev/null 2>&1; then
    target="$update_from_branch"
  else
    log "'$update_from_branch' no existe en remoto -> uso '$default_branch'"
  fi

  # Stash preventivo si hay modificaciones locales
  local stashed=0
  if [[ -n "$(git status --porcelain)" ]]; then
    git stash push -u -m "sync-projects $(date +%F_%T)" -q || { log "stash falló"; return 1; }
    stashed=1
  fi

  local err=0

  # Moverse a la rama objetivo (con soporte para worktrees simultáneos)
  if git show-ref --verify --quiet "refs/heads/$target"; then
    git checkout -q --ignore-other-worktrees "$target" 2>/dev/null || \
    git checkout -q "$target" || err=1
  else
    git checkout -q -b "$target" "origin/$target" 2>/dev/null || \
    git checkout -q --detach "origin/$target" || err=1
  fi

  # Borrar N commits locales con backup previo (si se configuró)
  if [[ $err -eq 0 && "$behind_commit_delete" -gt 0 ]]; then
    local backup="backup/sync-$(date +%Y%m%d-%H%M%S)"
    git branch "$backup" 2>/dev/null && log "backup en '$backup'"
    git reset --hard "HEAD~$behind_commit_delete" -q || err=1
  fi

  # Actualizar desde el remoto
  if [[ $err -eq 0 ]]; then
    git pull --ff-only -q origin "$target" || { log "pull falló"; err=1; }
  fi

  # Restaurar cambios guardados en el stash
  if [[ $stashed -eq 1 ]]; then
    if ! git stash pop -q 2>>"$LOG"; then
      mapfile -t conflicts < <(git diff --name-only --diff-filter=U)
      if [[ ${#conflicts[@]} -gt 0 ]]; then
        for f in "${conflicts[@]}"; do
          git checkout --theirs -- "$f" && git reset -q -- "$f"
        done
        git stash drop -q
        log "conflictos resueltos a favor del stash: ${conflicts[*]}"
      else
        log "stash pop falló sin conflictos; cambios guardados en 'git stash list'"
        return 1
      fi
    fi
  fi

  [[ $err -eq 0 ]] && log "OK ($target)"
  return $err
}

ok=(); fail=()

shopt -s nullglob

# Recorre todos los proyectos que empiecen con 'yappy-' en el workspace
for dir in "$ROOT"/yappy-*/; do
  project="$(basename "$dir")"

  # Valida que sea un repo o worktree Git (archivo o carpeta .git)
  [[ -e "$dir/.git" ]] || continue

  if sync_project; then
    ok+=("$project")
  else
    fail+=("$project")
  fi
done

shopt -u nullglob

echo ""
echo "=========================================="
echo "OK:    ${ok[*]:-ninguno}"
echo "FALLÓ: ${fail[*]:-ninguno} (detalle en $LOG)"
echo "=========================================="

[[ ${#fail[@]} -eq 0 ]]