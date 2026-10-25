"""Shortcuts de git.

Para crear uno nuevo:  ddt new <nombre>   (crea el archivo)
                       ddt-reload        (aparece como alias corto)
"""
from __future__ import annotations

import sys

from ..git import git, must
from ..params import branch, checkout, commits, create, limit, no_pull, remote, target_branch
from ..registry import command


@command("gfp", "git fetch --prune + git pull", args=[branch, checkout, remote])
def gfp(a) -> int:
    must(git("fetch", "--prune", a.remote))

    if a.checkout:
        if not a.branch:
            raise SystemExit("gfp --checkout necesita una rama: gfp develop --checkout")
        must(git("checkout", a.branch))
        return git("pull")

    if a.branch:                                  # pull sin tocar tu rama actual
        return git("pull", a.remote, a.branch)

    return git("pull")                            # rama actual, respeta upstream


@command("gcp", "Cherry-pick: rama destino primero, después los commits",
         args=[target_branch, commits, no_pull, remote])
def gcp(a) -> int:
    must(git("fetch", "--prune", a.remote))

    must(git("checkout", a.branch))

    if not a.no_pull:
        must(git("pull", "--rebase", a.remote))

    rc = git("cherry-pick", "-x", *a.commits)
    if rc:
        print("conflicto en cherry-pick: resolvé y corré `git cherry-pick --continue`",
              file=sys.stderr)
        return rc
    print(f"✔ {len(a.commits)} commit(s) sobre {a.branch}")
    return 0


@command("gco", "git checkout de rama", args=[branch, create])
def gco(a) -> int:
    if not a.branch:
        raise SystemExit("uso: gco <rama>  |  gco <rama> -b")
    if a.create:
        return git("checkout", "-b", a.branch)
    return git("checkout", a.branch)


@command("gsync", "fetch --prune + pull --rebase", args=[branch, remote])
def gsync(a) -> int:
    must(git("fetch", "--prune", a.remote))
    if a.branch:
        return git("pull", "--rebase", a.remote, a.branch)
    return git("pull", "--rebase")


@command("gs", "git status corto")
def gs(a) -> int:
    return git("status", "-sb")


@command("gl", "git log compacto", args=[limit])
def gl(a) -> int:
    return git("log", "--oneline", "--decorate", "-n", str(a.n))
