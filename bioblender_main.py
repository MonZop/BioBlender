'''
bioblender_main.py
for license see LICENSE.txt

'''
import os

from bpy.props import (StringProperty, EnumProperty)

from .utils import (file_append, detect_os)
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
    # register any scene, obj props
    Obj = bpy.types.Object
    Obj.BBInfo = StringProperty()
    Obj.bb2_pdbID = StringProperty()
    Obj.bb2_objectType = StringProperty()
    Obj.bb2_subID = StringProperty()
    Obj.bb2_pdbPath = StringProperty()
    Obj.bb2_outputOptions = EnumProperty(
        name="bb2_outputoptions", default="1",
        items=[
            ("0", "Main", ""), ("1", "+Side", ""), ("2", "+Hyd", ""),
            ("3", "Surface", ""), ("4", "MLP Main", ""), ("5", "MLP +Side", ""),
            ("6", "MLP +Hyd", ""), ("7", "MLP Surface", "")])
    Obj.bb25_opSystem = StringProperty(default=detect_os())

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
    Obj = bpy.types.Object
    del Obj.BBInfo
    del Obj.bb2_pdbID
    del Obj.bb2_objectType
    del Obj.bb2_subID
    del Obj.bb2_pdbPath
    del Obj.bb2_outputOptions
    del Obj.bb25_opSystem
