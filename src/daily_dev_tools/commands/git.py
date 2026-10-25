"""Shortcuts de git.

Para crear uno nuevo:  ddt new <nombre>   (crea el archivo)
                       ddt-reload        (aparece como alias corto)
"""
from __future__ import annotations

from ..enums.code_catalog_enum import CodeCatalogEnum
from ..git import capture, git, must
from ..params import source_branch, checkout, no_pull, remote, target_branch
from ..registry import command
from ..utils.git_utils import clean_branch_name
from ..utils.validation.git_validation_utils import is_not_local_branch_


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


@command("gs", "git checkout", args=[target_branch, source_branch])
def git_switch(args) -> int:
    if not args.target_branch:
        print(CodeCatalogEnum.ONE_PARAM_REQUIRED.message)
        return 0

    current_branch = capture("branch", "--show-current")

    if args.target_branch == current_branch:
        print(f"Already on '{args.target_branch}'")
        return 0

    if not args.source_branch:
        args.source_branch = clean_branch_name(capture("rev-parse", "--abbrev-ref", "origin/HEAD"))

    if args.target_branch == args.source_branch and current_branch == args.source_branch :
        print(f"Already on '{args.source_branch}'")
        return 0

    if args.target_branch == args.source_branch and current_branch != args.source_branch :
        must(git("checkout", args.target_branch))
        return 0

    if not is_not_local_branch_(args.target_branch):
        must(git("checkout", args.target_branch))
        return 0

    must(git("stash", "-u"))
    must(git("checkout", args.source_branch))
    must(git("fetch"))
    must(git("pull", "origin", args.source_branch))
    must(git("checkout", "-b", args.target_branch))

    return 0


@command("gclean", "git clean -f for unused branches", args=[no_pull])
def git_prune_local_branches(args) -> int:
    current = capture("branch", "--show-current")
    branch_list = capture("branch", "--format=%(refname:short)")

    for item_branch in branch_list.splitlines():
        if item_branch.strip() and item_branch.strip() != current:
            git("branch", "-d", item_branch)
            print(CodeCatalogEnum.DELETING_BRANCH.message, item_branch)

    return 0
