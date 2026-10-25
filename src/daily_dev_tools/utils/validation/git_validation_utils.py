import subprocess


def is_not_local_branch_(branch: str) -> bool:
    response = subprocess.run(
        ["git", "branch", '--list', branch],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    return not response or response == ''