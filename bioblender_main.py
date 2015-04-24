'''
bioblender_main.py
for license see LICENSE.txt

'''

from .utils import file_append
from .tables import (
    color,
    values_fi,
    molecules_structure,
    scale_vdw, scale_cov,
    NucleicAtoms, NucleicAtoms_Filtered)

from .ui_panels import ImportDisposablePDB


C = "C"
N = "N"
O = "O"
S = "S"
H = "H"
CA = "CA"
P = "P"
FE = "FE"
MG = "MG"
ZN = "ZN"
CU = "CU"
NA = "NA"
K = "K"
CL = "CL"
MN = "MN"
F = "F"


def register():
    # register any scene props
    # ....
    # ...

    # register operators first
    # ---
    # --
    # -

    # then register the UI for those operators
    bpy.utils.register_class(ImportDisposablePDB)
    # ---
    # --
    # -


def unregister():
    # unregister UI
    bpy.utils.unregister_class(ImportDisposablePDB)
    # ---
    # --
    # -

    # unregister operators.
    # ---
    # --
    # -

    # del any scene props
    # ....
    # ...
