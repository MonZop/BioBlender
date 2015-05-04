'''
bioblender_main.py
for license see LICENSE.txt

'''
import sys

from bpy.props import (StringProperty, EnumProperty)

from .utils import (
    file_append,
    detect_os,
    get_homepath,
    get_pyPath_pyMolPath)

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
    Scn = bpy.types.Scene

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

    opSystem = detect_os()
    Scn.bb25_opSystem = StringProperty(default=opSystem)
    Scn.bb25_homepath = StringProperty(default=get_homepath())
    Scn.bb25_blenderPath = StringProperty(default=str(sys.executable))

    pyPath, pyMolPath = get_pyPath_pyMolPath(opSystem)
    Scn.bb25_pyPath = StringProperty(default=pyPath)
    Scn.bb25_pyMolPath = StringProperty(default=pyMolPath)

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
    del Scn.bb25_opSystem
    del Scn.bb25_homepath
    del Scn.bb25_blenderPath
    del Scn.bb25_pyPath
    del Scn.bb25_pyMolPath
