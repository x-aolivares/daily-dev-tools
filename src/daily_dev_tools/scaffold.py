"""ddt new <nombre> — crea el archivo de un comando y te deja listo para escribirlo."""
from __future__ import annotations

from .config import COMMANDS_DIR
from .registry import COMMANDS, NAME_RE

TEMPLATE = '''\
"""{name} — descripción corta."""

from ..registry import command
# from ..params import branch, checkout


@command(
    "{name}",
    "Qué hace (aparece en `ddt list` y en `ddt --help`)",
    # args=[branch],
)
def {fn}(a) -> int:
    print("TODO: implementar {name}")
    return 1
'''


def new(name: str) -> str:
    """Crea commands/<name>.py. Devuelve la ruta relativa al repo."""
    if not NAME_RE.match(name):
        raise SystemExit(f"nombre inválido: {name!r} (usa letras, números, _ y -)")
    if name in COMMANDS:
        raise SystemExit(f"el comando {name!r} ya existe")

    path = COMMANDS_DIR / f"{name}.py"
    if path.exists():
        raise SystemExit(f"ya existe el archivo {path.name}")

    fn = name.replace("-", "_")
    path.write_text(TEMPLATE.format(name=name, fn=fn), encoding="utf-8")

    editable = (COMMANDS_DIR / ".." / ".." / "..").joinpath(".git").exists()
    where = "repo (install editable)" if editable else "site-packages"
    return f"creado commands/{path.name}  [{where}]\nescribí ahí y corré:  ddt-reload"
