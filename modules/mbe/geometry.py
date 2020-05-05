"""
Geometry tools for GHPython scripts

Author: Max Eschenbach
License: Apache License 2.0
Version: 200414
"""
# PYTHON STANDARD LIBRARY IMPORTS ----------------------------------------------
from __future__ import absolute_import
from __future__ import division
import clr
from collections import deque
import math

# RHINO IMPORTS ----------------------------------------------------------------
import Rhino
import System
import scriptcontext

# AUTHORSHIP -------------------------------------------------------------------
__author__ = """Max Eschenbach (post@maxeschenbach.com)"""

# ALL DICTIONARY ---------------------------------------------------------------
__all__ = [
    "BreakPolyline"
]

def BreakPolyline(Polyline, BreakAngle):
    """
    Breaks a polyline at kinks based on a specified angle.
    """

    # get all the polyline segments
    segments = deque(Polyline.GetSegments())

    # initialize containers
    if Polyline.IsClosed:
        closedSeamAtKink = False
    else:
        closedSeamAtKink = True
    plcs = []
    pl = Rhino.Geometry.Polyline()

    # process all segments
    while len(segments) > 0:
        scriptcontext.escape_test()

        # if there is only one segment left, add the endpoint to the new pl
        if len(segments) == 1:
            ln = segments.popleft()
            pl.Add(ln.To)
            plcs.append(pl.ToPolylineCurve())
            break

        # get unitized directions of this and next segment
        thisdir = segments[0].Direction
        nextdir = segments[1].Direction
        thisdir.Unitize()
        nextdir.Unitize()

        # compute angle
        vdp = thisdir * nextdir
        angle = math.cos(vdp / (thisdir.Length * nextdir.Length))
        angle = Rhino.Geometry.Vector3d.VectorAngle(thisdir, nextdir)

        # check angles and execute breaks
        if angle >= BreakAngle:
            if not closedSeamAtKink:
                segments.rotate(-1)
                pl.Add(segments.popleft().From)
                closedSeamAtKink = True
            elif closedSeamAtKink:
                ln = segments.popleft()
                pl.Add(ln.From)
                pl.Add(ln.To)
                plcs.append(pl.ToPolylineCurve())
                pl = Rhino.Geometry.Polyline()
        else:
            if not closedSeamAtKink:
                segments.rotate(-1)
            else:
                pl.Add(segments.popleft().From)

    return plcs

def TweenPlanes(P1, P2, t):
        """
        Tweens between two planes using quaternion rotation.
        """

        # create the quternion rotation between the two input planes
        Q = Rhino.Geometry.Quaternion.Rotation(P1, P2)

        # prepare out parameters
        qAngle = clr.Reference[System.Double]()
        qAxis = clr.Reference[Rhino.Geometry.Vector3d]()

        # get the rotation of the quaternion
        Q.GetRotation(qAngle, qAxis)

        axis = Rhino.Geometry.Vector3d(qAxis.X, qAxis.Y, qAxis.Z)
        angle = float(qAngle) - 2 * math.pi if float(qAngle) > math.pi else float(qAngle)

        OutputPlane = P1.Clone()
        OutputPlane.Rotate(t * angle, axis, OutputPlane.Origin)
        Translation = Rhino.Geometry.Vector3d(P2.Origin - P1.Origin)
        OutputPlane.Translate(Translation * t)

        return OutputPlane
