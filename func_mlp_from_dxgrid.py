# func_mlp_from_dxgrid.py
import numpy as np


def get_3dgrid_from_dx(filepath):
    '''
    Athours of this function:

        - Dealga McArdle (zeffii)  (may 2015)
        - comment prior to coding
        This intends to be a basic implementation of a dx grid reader which may be
        useful only for reading the .dx produced by pyMLP.py. I'm making heavy
        assumptions about the consistency of these .dx files.

    first a few definitions before continueing the comment

    cell:
        Defined by a 3d matrix, which is built from 3d grid blocks.

    surface:
        The scene object called SURFACE with is the wrl triangulated mesh that
        describes the 3d surface of the molecule. It comes in from pyMOL as separate
        triangles - subsequently it is edited using remove doubles,
        to make all vertices unique.

    vertex_colors:
        Are set in the mlp() function and that's what this function intends to adjust


    Problem ==

    A problem discussed in the bioblender github repo is that a vertex of the surface
    may lay in a cell which represents the inside of the molecule, and the value just
    above the surface of the cell can vary substantially from the very next nearest cell
    grid. This may be related to the numeric noise present in the 32 bit float
    storage, and frequently the first (blind) sampling of the closest vertex-grid cell
    gives a value which doesn't indicate what we're trying to communicate using the
    surface.

    Solution ==

    Well, that's the kicker. A few methods exist, and some of the best are slower due to
    vacinity checking and several extra calculations per surface vertex.

    '''
