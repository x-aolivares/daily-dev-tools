"""Todos los módulos de este paquete se registran solos al importar.

Por eso `ddt new` solo tiene que crear el archivo: no hay que tocar este
archivo ni el pyproject para agregar un comando.
"""
from __future__ import annotations

import importlib
import pkgutil

for _module in pkgutil.iter_modules(__path__):
    if not _module.name.startswith("_"):
        importlib.import_module(f"{__name__}.{_module.name}")

del _module, importlib, pkgutil
