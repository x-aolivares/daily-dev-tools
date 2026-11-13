"""gaw — worktrees por historia.

Estructura en disco:  <WORKTREES_PATH>/<rama>/<proyecto>

    gaw feature/X              # crea el worktree del proyecto actual
    gaw feature/X develop      # ... desde origin/develop
    gaw rm feature/X           # borra TODOS los proyectos de la historia
    gaw rm X --dry-run         # muestra qué borraría
    gaw rm X --force           # fuerza worktrees con cambios sin commitear

`rm` es una palabra reservada: no se puede crear una rama llamada así.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from ..config import shell_path
from ..git import capture, current_branch, git, must, repo_root
from ..registry import command
from ..utils.validation.git_validation_utils import is_not_local_branch_

DEFAULT_WORKTREES_PATH = "C:/Development/worktrees"
RESERVED = "rm"
MAX_DEPTH = 8

# Mismo criterio que commands/utils.py: el .env del repo en modo editable.
_REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = _REPO_ROOT / ".env"

_DRIVE_RE = re.compile(r"^/([A-Za-z])/(.*)$")
_DRIVE_ROOT_RE = re.compile(r"^/([A-Za-z])$")


# --------------------------------------------------------------- argumentos

def gaw_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "target",
        help="rama de trabajo, o 'rm' para eliminar una historia",
    )
    p.add_argument(
        "remainder",
        nargs="*",
        help="rama padre (al crear) o historia a borrar (con 'rm')",
    )
    p.add_argument("--remote", default="origin", help="remoto (default: origin)")
    p.add_argument(
        "--force",
        action="store_true",
        help="con 'rm': fuerza worktrees con cambios sin commitear",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="con 'rm': muestra qué borraría, sin tocar nada",
    )


# ------------------------------------------------------------------ comandos

@command(
    "gaw",
    "crea un worktree por rama; 'gaw rm <historia>' borra todos sus proyectos",
    args=[gaw_args],
)
def gaw(a) -> int:
    if a.target == RESERVED:
        if len(a.remainder) != 1:
            raise SystemExit("uso: gaw rm <historia> [--force] [--dry-run]")
        return remove_story(a.remainder[0], force=a.force, dry_run=a.dry_run)

    if len(a.remainder) > 1:
        raise SystemExit("uso: gaw <rama> [rama-padre]")
    if a.force or a.dry_run:
        raise SystemExit("--force y --dry-run solo aplican a 'gaw rm'")

    return create_worktree(a.target, a.remainder[0] if a.remainder else None, a.remote)


def create_worktree(work_branch: str, source_branch: str | None, remote: str) -> int:
    if not valid_branch_name(work_branch):
        raise SystemExit(f"Nombre de rama inválido: {work_branch}")

    try:
        project_root = Path(repo_root())
    except (subprocess.CalledProcessError, OSError):
        raise SystemExit("gaw: tenés que estar dentro de un repositorio git")

    project_name = project_root.name

    if not source_branch:
        print("WARN: No se recibió rama padre, se usa la rama actual.", file=sys.stderr)
        source_branch = current_branch()
        if source_branch == "HEAD":
            raise SystemExit("Detached HEAD: indica la rama padre explícitamente.")

    target = worktrees_root() / work_branch / project_name
    if target.exists():
        raise SystemExit(f"Ya existe el worktree: {target}")
    if not is_not_local_branch_(work_branch):
        raise SystemExit(f"Ya existe la rama local: {work_branch}")

    must(git("fetch", remote, source_branch))
    must(git("worktree", "add", "-b", work_branch, str(target), f"{remote}/{source_branch}"))

    print(f"Worktree creado en {target}")
    print(f'  cd "{shell_path(target)}"')
    return 0


def remove_story(name: str, *, force: bool = False, dry_run: bool = False) -> int:
    root = worktrees_root()
    if not root.is_dir():
        raise SystemExit(f"No existe el directorio de worktrees: {root}")
    root = root.resolve()

    story = resolve_story(root, name)
    children = sorted(p for p in story.iterdir() if p.is_dir())

    if dry_run:
        print(f"Historia: {story}")
        if not children:
            print("  (sin proyectos)")
        for child in children:
            if _es_worktree(child):
                print(f"  borraría {child}")
            else:
                print(f"  omite {child} (no es worktree)")
        return 0

    failures = 0
    cwd = Path.cwd().resolve()

    for child in children:
        if not _es_worktree(child):
            print(f"WARN: {child} no es un worktree, lo dejo", file=sys.stderr)
            continue

        if cwd.is_relative_to(child.resolve()):
            print(f"ERROR: no puedo borrar {child}: es tu directorio actual", file=sys.stderr)
            failures += 1
            continue

        main = _main_worktree(child)
        if main is None:
            print(f"ERROR: no encontré el repo principal de {child}", file=sys.stderr)
            failures += 1
            continue

        args = ["-C", str(main), "worktree", "remove"]
        if force:
            args.append("--force")
        args.append(str(child))

        if git(*args):
            failures += 1
        else:
            print(f"borrado {child}")

    _cleanup_empty(story, root)

    if failures:
        print(f"\n{failures} proyecto(s) no se pudieron borrar.", file=sys.stderr)
        return 1
    return 0


# -------------------------------------------------------------------- rutas

def worktrees_root() -> Path:
    load_dotenv(ENV_FILE)  # override=False: una variable real gana sobre el .env
    raw = os.getenv("WORKTREE_PATH") or os.getenv("WORKTREES_PATH")
    if raw:
        return Path(normalize_shell_path(raw))
    if os.name == "nt":
        return Path(DEFAULT_WORKTREES_PATH)
    return Path.home() / "worktrees"


def normalize_shell_path(raw: str) -> str:
    """Convierte rutas de Git Bash (/c/...) a rutas que git.exe entiende."""
    path = os.path.expanduser(raw)
    if os.name != "nt":
        return path

    normalized = path.replace("\\", "/")
    match = _DRIVE_RE.match(normalized)
    if match:
        return f"{match.group(1).upper()}:/{match.group(2)}"
    root = _DRIVE_ROOT_RE.match(normalized)
    if root:
        return f"{root.group(1).upper()}:/"
    return path


# --------------------------------------------------------- resolver historia

def find_story_dirs(root: Path, name: str) -> list[Path]:
    """Busca carpetas cuyo path termine en `name` (p. ej. YNC-1 -> feature/YNC-1).

    No entra dentro de repos: un worktree nunca es contenedor de una historia.
    """
    if not name or Path(name).is_absolute():
        return []

    suffix = tuple(p for p in Path(name).parts if p not in ("", "."))
    if not suffix or ".." in suffix:
        return []

    matches: list[Path] = []

    def walk(directory: Path, rel: tuple[str, ...]) -> None:
        if len(rel) > MAX_DEPTH:
            return
        try:
            children = sorted(directory.iterdir())
        except OSError:
            return
        for child in children:
            if not child.is_dir():
                continue
            if (child / ".git").exists():
                continue  # es un proyecto/worktree, no una historia
            rel_child = rel + (child.name,)
            if len(rel_child) >= len(suffix) and rel_child[-len(suffix):] == suffix:
                matches.append(child)
                continue
            walk(child, rel_child)

    walk(root, ())
    return sorted(matches)


def resolve_story(root: Path, name: str) -> Path:
    if not name or not name.strip():
        raise SystemExit("Falta el nombre de la historia.")

    root_resolved = root.resolve()
    exact = root / name
    if exact.is_dir():
        story = exact.resolve()
    else:
        matches = find_story_dirs(root, name)
        if not matches:
            raise SystemExit(f"No encontré ninguna historia para {name!r} en {root_resolved}")
        if len(matches) > 1:
            lista = "\n".join(f"  {m}" for m in matches)
            raise SystemExit(f"{name!r} es ambiguo, usá una ruta exacta:\n{lista}")
        story = matches[0].resolve()

    if story == root_resolved or not _is_under(story, root_resolved):
        raise SystemExit(f"{name!r} queda fuera del directorio de worktrees ({root_resolved})")
    return story


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


# ------------------------------------------------------------------ helpers

def valid_branch_name(name: str) -> bool:
    return subprocess.run(
        ["git", "check-ref-format", "--branch", name],
        capture_output=True,
        text=True,
    ).returncode == 0


def _es_worktree(path: Path) -> bool:
    return (path / ".git").exists()


def _main_worktree(worktree: Path) -> Path | None:
    try:
        out = capture("-C", str(worktree), "worktree", "list", "--porcelain")
    except subprocess.CalledProcessError:
        return None
    for line in out.splitlines():
        if line.startswith("worktree "):
            return Path(line[len("worktree "):])
    return None


def _cleanup_empty(story: Path, root: Path) -> None:
    current = story
    while current != root and current.is_dir():
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent
