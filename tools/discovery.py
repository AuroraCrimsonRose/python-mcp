from __future__ import annotations

import importlib
import pkgutil

import tools as tools_pkg


def load_all_tools():
    """
    Explicit tool loader.

    Imports all modules inside /tools so they register
    themselves into the registry.
    """

    for module in pkgutil.iter_modules(
        tools_pkg.__path__
    ):
        importlib.import_module(
            f"tools.{module.name}"
        )