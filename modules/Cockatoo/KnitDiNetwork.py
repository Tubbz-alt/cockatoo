"""
Directional KnitNetwork for finding faces (cycles) of a KnitNetwork.

Author: Max Eschenbach
License: Apache License 2.0
Version: 200503
"""

# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from collections import deque
import math
from operator import itemgetter

# LOCAL MODULE IMPORTS ---------------------------------------------------------
from .Environment import IsRhinoInside
from .KnitNetworkBase import KnitNetworkBase
from .Utilities import is_ccw_xy
from .Utilities import pairwise

# THIRD PARTY MODULE IMPORTS ---------------------------------------------------
import networkx as nx

# RHINO IMPORTS ----------------------------------------------------------------
if IsRhinoInside():
    import rhinoinside
    rhinoinside.load()
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Plane as RhinoPlane
    from Rhino.Geometry import Vector3d as RhinoVector3d
else:
    from Rhino.Geometry import Mesh as RhinoMesh
    from Rhino.Geometry import NurbsSurface as RhinoNurbsSurface
    from Rhino.Geometry import Plane as RhinoPlane
    from Rhino.Geometry import Vector3d as RhinoVector3d

# AUTHORSHIP -------------------------------------------------------------------
__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "KnitDiNetwork"
]

# ACTUAL CLASS -----------------------------------------------------------------
class KnitDiNetwork(nx.DiGraph, KnitNetworkBase):
    """
    Class for representing a mapping network that facilitates the automatic
    generation of knitting patterns based on Rhino geometry.
    This is intended only to be instanced by a fully segmented instance of
    KnitNetwork.
    """

    # INITIALIZATION -----------------------------------------------------------

    def __init__(self, data=None, **attr):
        """
        Initialize a KnitNetwork (inherits NetworkX graph with edges, name,
        graph attributes.

        Parameters
        ----------
        data : input graph
            Data to initialize graph.  If data=None (default) an empty
            graph is created.  The data can be an edge list, or any
            NetworkX graph object.  If the corresponding optional Python
            packages are installed the data can also be a NumPy matrix
            or 2d ndarray, a SciPy sparse matrix, or a PyGraphviz graph.
        name : string, optional (default='')
            An optional name for the graph.
        attr : keyword arguments, optional (default= no attributes)
            Attributes to add to graph as key=value pairs.
        """

        # initialize using original init method
        super(KnitDiNetwork, self).__init__(data=data, **attr)

        # also copy the MappingNetwork attribute if it is already available
        if data and isinstance(data, KnitDiNetwork) and data.MappingNetwork:
            self.MappingNetwork = data.MappingNetwork
        else:
            self.MappingNetwork = None

        # also copy or initialize the halfedge dict for finding faces
        if data and isinstance(data, KnitDiNetwork) and data.halfedge:
            self.halfedge = data.halfedge
        else:
            self.halfedge = {}

    # TEXTUAL REPRESENTATION OF NETWORK ----------------------------------------

    def ToString(self):
        """
        Return a textual description of the network.
        """

        name = "KnitDiNetwork"
        nn = len(self.nodes())
        ce = len(self.ContourEdges)
        wee = len(self.WeftEdges)
        wae = len(self.WarpEdges)
        data = ("({} Nodes, {} Segment Contours, {} Weft, {} Warp)")
        data = data.format(nn, ce, wee, wae)
        return name + data

    # FIND FACES (CYCLES) OF NETWORK -------------------------------------------

    def _sort_node_neighbors(self, key, nbrs, xyz, geo, cbp, nrm, ccw=True):
        """
        Sort the neighbors of a network node.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L132
        """

        # if there is only one neighbor we don't need to sort anything
        if len(nbrs) == 1:
            return nbrs

        # initialize the ordered list of neighbors with the first node
        ordered_nbrs = nbrs[0:1]

        # retrieve coordinates for current node
        a = xyz[key]

        # compute local orientation if geometrybase data is present
        if cbp and nrm:
            a_geo = geo[key]
            lclpln = RhinoPlane(a_geo, nrm[key])
            lcl_a = lclpln.RemapToPlaneSpace(a_geo)[1]
            a = (lcl_a.X, lcl_a.Y, lcl_a.Z)
            lcl_xyz = {}
            for nbr in nbrs:
                nbr_cp = lclpln.ClosestPoint(geo[nbr])
                lcl_nbr = lclpln.RemapToPlaneSpace(nbr_cp)[1]
                nbr_xyz = (lcl_nbr.X, lcl_nbr.Y, lcl_nbr.Z)
                lcl_xyz[nbr] = nbr_xyz
            xyz = lcl_xyz

        # loop over all neighbors except the first one (which is our basis for
        # the ordered list)
        for i, nbr in enumerate(nbrs[1:]):
            c = xyz[nbr]
            pos = 0
            b = xyz[ordered_nbrs[pos]]
            while not is_ccw_xy(a, b, c):
                pos += 1
                if pos > i:
                    break
                b = xyz[ordered_nbrs[pos]]
            if pos == 0:
                pos -= 1
                b = xyz[ordered_nbrs[pos]]
                while is_ccw_xy(a, b, c):
                    pos -= 1
                    if pos < -len(ordered_nbrs):
                        break
                    b = xyz[ordered_nbrs[pos]]
                pos += 1
            ordered_nbrs.insert(pos, nbr)

        # return the ordered neighbors in cw or ccw order
        if not ccw:
            return ordered_nbrs[::-1]
        return ordered_nbrs

    def _sort_neighbors(self, ccw=True):
        """
        Sort the neighbors of all network nodes.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L121
        """

        # initialize sorted neighbors dict
        sorted_neighbors = {}

        # get dictionary of all coordinates by node index
        xyz = {k: (d["x"], d["y"], d["z"]) for k, d in self.nodes_iter(True)}
        geo = {k: d["geo"] for k, d in self.nodes_iter(True)}

        # compute local orientation data when geometry base is present
        try:
            geometrybase = self.graph["geometrybase"]
        except KeyError:
            geometrybase = None

        if not geometrybase:
            cbp = None
            nrm = None
        elif isinstance(geometrybase, RhinoMesh):
            cbp = {k: geometrybase.ClosestMeshPoint(geo[k], 0) \
                   for k in self.nodes_iter()}
            nrm = {k: geometrybase.NormalAt(cbp[k]) \
                   for k in self.nodes_iter()}
        elif isinstance(geometrybase, RhinoNurbsSurface):
            cbp = {k: geometrybase.ClosestPoint(geo[k])[1:] \
                   for k in self.nodes_iter()}
            nrm = {k: geometrybase.NormalAt(cbp[k][0], cbp[k][1]) \
                   for k in self.nodes_iter()}

        # loop over all nodes in network
        for key in self.nodes_iter():
            nbrs = self[key].keys()
            sorted_neighbors[key] = self._sort_node_neighbors(key, nbrs, xyz, geo, cbp, nrm, ccw=ccw)

        # set the sorted neighbors list as an attribute to the nodes
        for key, nbrs in sorted_neighbors.items():
            self.node[key]["sorted_neighbors"] = nbrs[::-1]

        # return the sorted neighbors dict
        return sorted_neighbors

    def _find_first_node_neighbor(self, key):
        """
        Find the first neighbor for a given node in the network.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/e313502995b0dd86d460f86e622cafc0e29d1b75/src/compas/datastructures/network/duality.py#L103
        """

        # get all node neighbors
        nbrs = self[key].keys()
        # if there is only one neighbor, we have already found our candidate
        if len(nbrs) == 1:
            return nbrs[0]
        ab = [-1.0, -1.0, 0.0]
        rhino_ab = RhinoVector3d(*ab)
        a = self.NodeCoordinates(key)
        b = [a[0] + ab[0], a[1] + ab[1], 0]
        angles = []
        for nbr in nbrs:
            c = self.NodeCoordinates(nbr)
            ac = [c[0] - a[0], c[1] - a[1], 0]
            rhino_ac = RhinoVector3d(*ac)
            alpha = RhinoVector3d.VectorAngle(rhino_ab, rhino_ac)
            if is_ccw_xy(a, b, c, True):
                alpha = (2 * math.pi) - alpha
            angles.append(alpha)
        return nbrs[angles.index(min(angles))]

    def _find_edge_cycle(self, u, v):
        """
        Find a cycle based on the given edge.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/09153de6718fb3d49a4650b89d2fe91ea4a9fd4a/src/compas/datastructures/network/duality.py#L161
        """
        cycle = [u]
        while True:
            cycle.append(v)
            nbrs = self.node[v]["sorted_neighbors"]
            nbr = nbrs[nbrs.index(u) - 1]
            u, v = v, nbr
            if v == cycle[0]:
                break
        return cycle

    def FindCycles(self):
        """
        Finds the cycles (faces) of this network by utilizing a wall-follower
        mechanism.

        Notes
        -----
        Based on an implementation inside the COMPAS framework.
        For more info see [1]_.

        References
        ----------
        .. [1] Van Mele, Tom et al. *COMPAS: A framework for computational research in architecture and structures*.
               See: https://github.com/compas-dev/compas/blob/09153de6718fb3d49a4650b89d2fe91ea4a9fd4a/src/compas/datastructures/network/duality.py#L20
        """

        # initialize the halfedge dict of the directed network
        for u, v in self.edges_iter():
            try:
                self.halfedge[u][v] = None
            except KeyError:
                self.halfedge[u] = {}
                self.halfedge[u][v] = None
            try:
                self.halfedge[v][u] = None
            except KeyError:
                self.halfedge[v] = {}
                self.halfedge[v][u] = None

        # sort the all the neighbors for each node of the network
        self._sort_neighbors()

        # find start node
        u = sorted(self.nodes_iter(data=True), key=lambda n: (n[1]["y"], n[1]["x"]))[0][0]

        # initialize found and cycles dict
        cycles = {}
        found = {}
        ckey = 0

        # find the very first cycle
        v = self._find_first_node_neighbor(u)
        cycle = self._find_edge_cycle(u, v)
        frozen = frozenset(cycle)
        found[frozen] = ckey
        cycles[ckey] = cycle

        for a, b in pairwise(cycle + cycle[:1]):
            self.halfedge[a][b] = ckey
        ckey += 1

        for u, v in self.edges_iter():
            if self.halfedge[u][v] is None:
                cycle = self._find_edge_cycle(u, v)
                frozen = frozenset(cycle)
                if frozen not in found:
                    found[frozen] = ckey
                    cycles[ckey] = cycle
                    ckey += 1
                for a, b in pairwise(cycle + cycle[:1]):
                    self.halfedge[a][b] = found[frozen]
            if self.halfedge[v][u] is None:
                cycle = self._find_edge_cycle(v, u)
                frozen = frozenset(cycle)
                if frozen not in found:
                    found[frozen] = ckey
                    cycles[ckey] = cycle
                    ckey += 1
                for a, b in pairwise(cycle + cycle[:1]):
                    self.halfedge[a][b] = found[frozen]

        return cycles
