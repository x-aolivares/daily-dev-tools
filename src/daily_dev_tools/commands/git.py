"""Shortcuts de git.

Para crear uno nuevo:  ddt new <nombre>   (crea el archivo)
                       ddt-reload        (aparece como alias corto)
"""
from __future__ import annotations

from time import sleep

from ..utils.git_utils import clean_branch_name
from ..utils.validation.git_validation_utils import is_not_local_branch_
from ..git import capture, git, must
from ..params import source_branch, checkout, no_pull, remote, target_branch
from ..registry import command


@command("gfp", "git fetch --prune + git pull", args=[source_branch, checkout, remote])
def gfp(a) -> int:
    must(git("fetch", "--prune", a.remote))

    if a.checkout:
        if not a.source_branch:
            raise SystemExit("gfp --checkout necesita una rama: gfp develop --checkout")
        must(git("checkout", a.source_branch))
        return git("pull")

    if a.source_branch:  # pull sin tocar tu rama actual
        return git("pull", a.remote, a.source_branch)

    return git("pull")  # rama actual, respeta upstream


# @command("gcp", "Cherry-pick: rama destino primero, después los commits",
#          args=[target_branch, commits, no_pull, remote])
# def gcp(a) -> int:
#     must(git("fetch", "--prune", a.remote))
#
#     must(git("checkout", a.branch))
#
#     if not a.no_pull:
#         must(git("pull", "--rebase", a.remote))
#
#     rc = git("cherry-pick", "-x", *a.commits)
#     if rc:
#         print("conflicto en cherry-pick: resolvé y corré `git cherry-pick --continue`",
#               file=sys.stderr)
#         return rc
#     print(f"✔ {len(a.commits)} commit(s) sobre {a.branch}")
#     return 0
#
#
# @command("gco", "git checkout de rama", args=[branch, create])
# def gco(a) -> int:
#     if not a.branch:
#         raise SystemExit("uso: gco <rama>  |  gco <rama> -b")
#     if a.create:
#         return git("checkout", "-b", a.branch)
#     return git("checkout", a.branch)
#
#
# @command("gsync", "fetch --prune + pull --rebase", args=[branch, remote])
# def gsync(a) -> int:
#     must(git("fetch", "--prune", a.remote))
#     if a.branch:
#         return git("pull", "--rebase", a.remote, a.branch)
#     return git("pull", "--rebase")
#
#
# @command("gs", "git status corto")
# def gs(a) -> int:
#     return git("status", "-sb")
#
#
# @command("gl", "git log compacto", args=[limit])
# def gl(a) -> int:
#     return git("log", "--oneline", "--decorate", "-n", str(a.n))

@command("gs", "git checkout", args=[target_branch, source_branch])
def git_switch(args) -> int:
    if not args.target_branch and not args.source_branch:
        print(f"se requiere al menos un parametro de entrada.")
        return 0

    if args.target_branch and args.source_branch:

        if is_not_local_branch_(args.target_branch):
            print(f"La rama ya existe o es invalida.")
            return 0

        must(git("stash", "-u"))
        must(git("checkout", args.source_branch))
        must(git("fetch"))
        must(git("pull"))
        must(git("checkout", "-b", args.target_branch))

        print(f"Borning from branch: {args.source_branch}")
        sleep(0.5)
        print(f"Switching to branch: {args.target_branch}")
        sleep(0.5)

        return 0

    source = clean_branch_name(capture("rev-parse", "--abbrev-ref", "origin/HEAD"))
    args.source_branch = source

    if not is_not_local_branch_(args.target_branch):
        must(git("checkout", args.target_branch))

        return 0

    must(git("stash", "-u"))
    must(git("checkout", source))
    must(git("fetch"))
    pull_result = capture("pull", "origin", source)

    if pull_result != "":
        must(git("checkout", "-b", args.target_branch))

        print(f"Borning from branch: {args.source_branch}")
        sleep(0.5)
        print(f"Switching to branch: {args.target_branch}")
        sleep(0.5)

    return 0


@command("gclean", "git clean -f for unused branches", args=[no_pull])
def git_prune_local_branches(args) -> int:
    current = capture("branch", "--show-current")
    branch_list = capture("branch", "--format=%(refname:short)")

    for item_branch in branch_list.splitlines():
        if item_branch.strip() and item_branch.strip() != current:
            git("branch", "-d", item_branch)
            print("Eliminando rama local: ", item_branch)

    return 0
