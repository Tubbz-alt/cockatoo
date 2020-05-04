"""
Cockatoo library and class interface for automatic generation of cnc-knitting
patterns from 3D surfaces and meshes.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200503
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from . import Autoknit
from . import Environment
from . import Exceptions
from .KnitNetworkBase import KnitNetworkBase
from .KnitNetwork import KnitNetwork
from .KnitDiNetwork import KnitDiNetwork
from .KnitMappingNetwork import KnitMappingNetwork

# AUTHORSHIP -------------------------------------------------------------------

__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "Autoknit",
    "Environment",
    "Exceptions",
    "KnitNetworkBase",
    "KnitNetwork",
    "KnitDiNetwork",
    "KnitMappingNetwork",
]

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass
