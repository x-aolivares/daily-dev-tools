#!/usr/bin/env bash
# Uso: /c/Development/config/daily-dev-tools/src/sh/sync-projects.sh <rama_default> [rama_a_traer] [rama_local_trabajo]
# Ejemplos:
#   # Si estás parado en wb/workspace-config y quieres traer performance/... o development:
#   sh sync-projects.sh development performance/springboot-4.2.0-upgrade
#
#   # Si quieres asegurarte explícitamente de que se quede en wb/workspace-config:
#   sh sync-projects.sh development performance/springboot-4.2.0-upgrade wb/workspace-config

set -u
default_branch="${1:?Falta rama_default (ej: development)}"
update_from_branch="${2:-$default_branch}"
desired_local_branch="${3:-}"

ROOT="$(pwd)"
LOG="$ROOT/sync.log"
: > "$LOG"

log() { echo "[$(date +%T)] [$project] $*" | tee -a "$LOG"; }

sync_project() {
  cd "$dir" || return 1
  git fetch origin --prune -q || { log "fetch falló"; return 1; }

  # 1. Asegurar la rama local de trabajo
  local current_branch
  current_branch="$(git branch --show-current 2>/dev/null || echo "")"

  # Si se especificó una rama local y no estamos en ella, cambiamos
  if [[ -n "$desired_local_branch" && "$current_branch" != "$desired_local_branch" ]]; then
    if git show-ref --verify --quiet "refs/heads/$desired_local_branch"; then
      git checkout -q --ignore-other-worktrees "$desired_local_branch" 2>/dev/null || \
      git checkout -q "$desired_local_branch" || { log "No se pudo cambiar a $desired_local_branch"; return 1; }
    else
      # Si no existe localmente, la creamos desde HEAD actual o default
      git checkout -q -b "$desired_local_branch" || { log "No se pudo crear $desired_local_branch"; return 1; }
    fi
    current_branch="$desired_local_branch"
  fi

  # 2. Determinar la fuente remota: ¿existe en remoto?
  local source_branch="$default_branch"
  if git ls-remote --exit-code --heads origin "$update_from_branch" >/dev/null 2>&1; then
    source_branch="$update_from_branch"
  else
    log "'$update_from_branch' no existe en remoto -> fusionando desde 'origin/$default_branch'"
  fi

  # 3. Stash preventivo si hay cambios sin commitear
  local stashed=0
  if [[ -n "$(git status --porcelain)" ]]; then
    git stash push -u -m "sync-projects $(date +%F_%T)" -q || { log "stash falló"; return 1; }
    stashed=1
  fi

  local err=0

  # 4. Traer/fusionar los cambios de origin/<source_branch> en tu rama local actual
  log "Fusionando origin/$source_branch en $current_branch..."
  if ! git merge --no-edit -q "origin/$source_branch" 2>>"$LOG"; then
    log "conflicto al fusionar origin/$source_branch"
    err=1
  fi

  # 5. Restaurar stash si se hizo
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

  [[ $err -eq 0 ]] && log "OK ($current_branch <- origin/$source_branch)"
  return $err
}

ok=(); fail=()

shopt -s nullglob

for dir in "$ROOT"/yappy-*/; do
  project="$(basename "$dir")"
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