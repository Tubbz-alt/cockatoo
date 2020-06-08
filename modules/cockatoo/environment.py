"""
.. currentmodule:: cockatoo.environment

.. autosummary::
    :nosignatures:

    RHINOINSIDE
    NXVERSION
    is_rhino_inside
    networkx_version
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import print_function

# DUNDER -----------------------------------------------------------------------
__author__ = """Max Eschenbach (post@maxeschenbach.com)"""
__all__ = [
    "RHINOINSIDE",
    "NXVERSION",
    "is_rhino_inside",
    "networkx_version"
]

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from cockatoo.exception import *

# CHECKING FOR RHINO DEPENDENCY AND ENVIRONMENT --------------------------------

def is_rhino_inside():
    """
    Check if Rhino is running using rhinoinside.
    """
    try:
        import Rhino
    except ImportError:
        try:
            import rhinoinside
            rhinoinside.load()
            import Rhino
            return True
        except Exception:
            errMsg = "Rhino could not be loaded! Please make sure the " + \
                     "RhinoCommon API is available to continue."
            raise RhinoNotPresentError(errMsg)
    return False

RHINOINSIDE = is_rhino_inside()
"""
bool: ``True`` if Rhino is running using rhinoinside, ``False`` otherwise.
"""

# CHECKING FOR NETWORKX DEPENDENCY AND VERSION ---------------------------------

def networkx_version():
    """
    Return the version of the used networkx module.
    """
    try:
        import networkx
        version = networkx.__version__
    except ImportError:
        errMsg = "Could not load NetworkX. Please make sure the networkx " + \
                 "module is available to continue."
        raise NetworkXNotPresentError(errMsg)

    return version

NXVERSION = networkx_version()
"""
str: The version string of the networkx module that is being used.
"""

# MAIN -------------------------------------------------------------------------
if __name__ == '__main__':
    pass