import os
import shutil
import subprocess
from pathlib import Path

import pytest

from daily_dev_tools.cli import build_parser, main
from daily_dev_tools.commands.worktree import (
    find_story_dirs,
    normalize_shell_path,
    remove_story,
    resolve_story,
    worktrees_root,
)

GIT = shutil.which("git")
requires_git = pytest.mark.skipif(GIT is None, reason="git no está en el PATH")


# ------------------------------------------------------------------ parser

def test_gaw_crear_con_rama_y_padre():
    ns = build_parser().parse_args(["gaw", "feature/X", "develop"])
    assert ns.target == "feature/X"
    assert ns.remainder == ["develop"]
    assert ns.remote == "origin"
    assert ns.force is False
    assert ns.dry_run is False


def test_gaw_crear_sin_padre():
    ns = build_parser().parse_args(["gaw", "feature/X"])
    assert ns.target == "feature/X"
    assert ns.remainder == []


def test_gaw_rm_parsea_historia():
    ns = build_parser().parse_args(["gaw", "rm", "YNC-3250", "--force"])
    assert ns.target == "rm"
    assert ns.remainder == ["YNC-3250"]
    assert ns.force is True


def test_gaw_rm_sin_historia_falla():
    assert main(["gaw", "rm"]) == 1


def test_gaw_sin_target_falla():
    assert main(["gaw"]) == 2


# ------------------------------------------------------------------- rutas

def test_normalize_shell_path_ruta_normal(tmp_path):
    assert Path(normalize_shell_path(str(tmp_path))) == tmp_path


def test_normalize_shell_path_expande_home():
    assert Path(normalize_shell_path("~/worktrees")) == Path.home() / "worktrees"


@pytest.mark.skipif(os.name != "nt", reason="conversión MSYS solo en Windows")
def test_normalize_shell_path_convierte_drive():
    assert normalize_shell_path("/c/Development/worktrees") == "C:/Development/worktrees"


def test_worktrees_root_lee_env(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKTREES_PATH", str(tmp_path))
    assert worktrees_root() == tmp_path


# ------------------------------------------------------- resolver historia

def test_find_story_dirs_por_sufijo(tmp_path):
    story = tmp_path / "feature" / "YNC-3250"
    (story / "proj1").mkdir(parents=True)
    (story / "proj2").mkdir()

    assert find_story_dirs(tmp_path, "YNC-3250") == [story]
    assert find_story_dirs(tmp_path, "feature/YNC-3250") == [story]


def test_find_story_dirs_ambiguo(tmp_path):
    a = tmp_path / "a" / "YNC-1"
    b = tmp_path / "b" / "YNC-1"
    a.mkdir(parents=True)
    b.mkdir(parents=True)

    assert set(find_story_dirs(tmp_path, "YNC-1")) == {a, b}


def test_find_story_dirs_no_entra_en_repos(tmp_path):
    project = tmp_path / "feature" / "YNC-1" / "proj"
    project.mkdir(parents=True)
    (project / ".git").write_text("gitdir: /tmp/otro/.git/worktrees/proj\n")
    (project / "anidada").mkdir()

    assert find_story_dirs(tmp_path, "anidada") == []


def test_resolve_story_inexistente(tmp_path):
    with pytest.raises(SystemExit):
        resolve_story(tmp_path, "NO-EXISTE")


def test_resolve_story_fuera_del_root(tmp_path):
    root = tmp_path / "wt"
    root.mkdir()
    (tmp_path / "evil").mkdir()

    with pytest.raises(SystemExit):
        resolve_story(root, "../evil")


def test_resolve_story_root_vacio(tmp_path):
    with pytest.raises(SystemExit):
        resolve_story(tmp_path, "")


# --------------------------------------------------------- borrado real

def _git(*args: str, cwd: Path) -> None:
    subprocess.run([GIT, *args], cwd=cwd, check=True, capture_output=True, text=True)


def _repo_con_worktree(base: Path, project: str, branch: str) -> tuple[Path, Path]:
    main = base / "mains" / project
    main.mkdir(parents=True)
    _git("init", "-q", cwd=main)
    _git("config", "user.email", "test@example.com", cwd=main)
    _git("config", "user.name", "test", cwd=main)
    (main / "f.txt").write_text("hola")
    _git("add", ".", cwd=main)
    _git("commit", "-qm", "init", cwd=main)

    worktree = base / "wt" / branch / project
    worktree.parent.mkdir(parents=True, exist_ok=True)
    _git("worktree", "add", "-q", "-b", branch, str(worktree), cwd=main)
    return main, worktree


@requires_git
def test_rm_borra_todos_los_proyectos(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKTREES_PATH", str(tmp_path / "wt"))
    main1, wt1 = _repo_con_worktree(tmp_path, "proj1", "feature/YNC-1")
    main2, wt2 = _repo_con_worktree(tmp_path, "proj2", "feature/YNC-1")

    assert remove_story("YNC-1") == 0

    assert not wt1.exists()
    assert not wt2.exists()
    assert not (tmp_path / "wt" / "feature").exists()

    for main_repo in (main1, main2):
        out = subprocess.run(
            [GIT, "worktree", "list", "--porcelain"],
            cwd=main_repo, capture_output=True, text=True, check=True,
        ).stdout
        assert "wt/feature/YNC-1" not in out


@requires_git
def test_rm_sin_force_falla_con_cambios(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKTREES_PATH", str(tmp_path / "wt"))
    _, worktree = _repo_con_worktree(tmp_path, "proj1", "feature/YNC-1")
    (worktree / "f.txt").write_text("cambiado")

    assert remove_story("YNC-1") == 1
    assert worktree.exists()


@requires_git
def test_rm_con_force_borra_con_cambios(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKTREES_PATH", str(tmp_path / "wt"))
    _, worktree = _repo_con_worktree(tmp_path, "proj1", "feature/YNC-1")
    (worktree / "f.txt").write_text("cambiado")

    assert remove_story("YNC-1", force=True) == 0
    assert not worktree.exists()


@requires_git
def test_rm_dry_run_no_toca_nada(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKTREES_PATH", str(tmp_path / "wt"))
    _, worktree = _repo_con_worktree(tmp_path, "proj1", "feature/YNC-1")

    assert remove_story("YNC-1", dry_run=True) == 0
    assert worktree.exists()


def test_rm_deja_lo_que_no_es_worktree(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKTREES_PATH", str(tmp_path / "wt"))
    story = tmp_path / "wt" / "feature" / "YNC-1"
    (story / "raro").mkdir(parents=True)
    (story / "raro" / "archivo.txt").write_text("no soy un worktree")

    assert remove_story("YNC-1") == 0
    assert (story / "raro" / "archivo.txt").exists()
