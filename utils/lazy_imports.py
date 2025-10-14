"""
Lazy Imports - Importa módulos solo cuando se necesitan
"""

import importlib
from typing import Any


class LazyImport:
    """Importa módulos de forma lazy"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            self._module = importlib.import_module(self.module_name)
        
        return getattr(self._module, name)


# Módulos pesados que se cargan solo cuando se necesitan
pd = LazyImport('pandas')
np = LazyImport('numpy')
plt = LazyImport('matplotlib.pyplot')