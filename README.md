# daily-dev-tools (ddt)

Shortcuts del día a día para Git Bash. Los clonás donde sea, hacés `pip install -e .`
y te quedan comandos cortos (`gfp`, `gcp`, ...) en la terminal, en cualquier carpeta.

## Instalación

```bash
git clone git@github.com:x-aolivares/daily-dev-tools.git
cd daily-dev-tools
pip install -e .
eval "$(ddt setup)"        # una sola vez: instala bloque + aplica en esta terminal
```

`ddt setup` hace tres cosas:

1. escribe `~/.config/ddt/shortcuts.sh` (los aliases)
2. deja un bloque idempotente en `~/.bashrc` que agrega `Scripts/` al PATH y sourcea ese archivo
3. asegura que `~/.bash_profile` cargue `~/.bashrc` (Git Bash arranca como *login shell*, si no, el bloque nunca corre)

Como un proceso hijo no puede cambiar el entorno de su shell madre, el paso 3 se
aplica con `eval "$(...)"`: el stdout de `ddt setup` es código shell, y toda
salida humana va a stderr. Si lo corrés a pelo (sin `eval`), te imprime el
comando exacto que tenés que correr.

## Uso

```bash
gfp                     # git fetch --prune + git pull (rama actual)
gfp develop             # git pull origin develop (sin tocar tu rama)
gfp develop --checkout  # fetch + checkout develop + pull

gcp develop abc123      # fetch + checkout + pull --rebase + cherry-pick -x
gcp develop abc123 def  # varios commits
gcp develop abc123 --no-pull

gco develop             # git checkout
gco develop -b          # git checkout -b
gsync                   # fetch --prune + pull --rebase
gs                      # git status -sb
gl                      # git log --oneline -n 10
gl 30                   # -n 30

groot                   # cd a la raíz del repo
ggl 5                   # git log --stat de los últimos 5
```

Todos funcionan igual con el prefijo (`ddt gfp develop`): el alias es un wrapper
de una línea, así que no hay forma de que diverjan.

## Crear un comando nuevo

```bash
ddt new gdeploy
# → creado commands/gdeploy.py
# escribí ahí y corré:
ddt-reload
gdeploy
```

El archivo que te deja es este:

```python
"""gdeploy — descripción corta."""

from ..registry import command
# from ..params import branch, checkout


@command(
    "gdeploy",
    "Qué hace (aparece en `ddt list` y en `ddt --help`)",
    # args=[branch],
)
def gdeploy(a) -> int:
    print("TODO: implementar gdeploy")
    return 1
```

No hay que tocar `pyproject.toml`, ni `cli.py`, ni el `.bashrc`. Los módulos de
`commands/` se importan solos.

### Dos tipos de comando

| | `@command(...)` | `shell(...)` |
|---|---|---|
| Lógica en | Python (proceso hijo) | bash (la misma shell) |
| Para | git, flags, validación, mensajes | `cd`, `export`, `source` |
| Se invoca como | `ddt foo` y alias `foo` | solo alias `foo` |

```python
# commands/nav.py — un proceso hijo no le puede hacer cd a tu terminal
shell(
    "groot",
    "cd a la raíz del repo",
    bash='cd "$(git rev-parse --show-toplevel)"',
)
```

Argumentos compartidos viven en `params.py` (`branch`, `target_branch`, `create`,
`checkout`, `remote`, `commits`, `no_pull`, `limit`) y se reutilizan con
`args=[branch, checkout]`.

## Comandos de ddt

| | |
|---|---|
| `ddt setup` | instala integración (ver arriba) |
| `ddt-reload` | regenera aliases y los recarga en la terminal |
| `ddt new <nombre>` | crea un comando nuevo |
| `ddt list [--all]` | qué shortcuts hay |
| `ddt doctor` | diagnóstico: git, PATH, bloque, archivo |
| `ddt teardown` | desinstala todo (`eval "$(ddt teardown)"` limpia la sesión) |

## Estructura

```
src/daily_dev_tools/
├── registry.py        # @command y shell(): un comando = un bloque
├── params.py          # argumentos reutilizables
├── git.py             # helpers: git(), must(), current_branch()
├── cli.py             # el dispatcher ddt (armado desde el registro)
├── scaffold.py        # ddt new
├── config.py          # rutas
├── shell/
│   ├── block.py       # bloque idempotente con marcadores >>> ddt >>>
│   ├── generate.py    # escribe ~/.config/ddt/shortcuts.sh (100% derivado)
│   └── install.py     # setup / reload / teardown
└── commands/          # acá vive todo lo tuyo
    ├── git.py         # gfp, gcp, gco, gsync, gs, gl
    ├── nav.py         # groot, ggl (nativos de shell)
    └── admin.py       # setup, new, list, doctor...
```

## Desinstalar

```bash
eval "$(ddt teardown)"
pip uninstall daily-dev-tools
```

## Requisitos

- Python >= 3.10
- git
- Git Bash (probado en Windows; el bloque de `.bashrc` funciona igual en Linux/macOS)
