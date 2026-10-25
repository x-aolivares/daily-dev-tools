def clean_branch_name(branch: str) -> str:
    if branch.startswith("origin/"):
        branch = branch[len("origin/"):]
        return branch

    else:
        return branch
