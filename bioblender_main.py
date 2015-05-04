'''
bioblender_main.py
for license see LICENSE.txt

'''
import sys
import bpy

from bpy.props import (StringProperty, EnumProperty)

from .utils import (
    file_append,
    detect_os,
    get_homepath,
    get_pyPath_pyMolPath)

# from .tables import (
#     color,
#     values_fi,
#     molecules_structure,
#     scale_vdw, scale_cov,
#     NucleicAtoms, NucleicAtoms_Filtered)

# from .ui_panels import ImportDisposablePDB
from .gui_panel_pdb_import import (
    BB2_GUI_PDB_IMPORT,
    bb2_operator_make_preview,
    bb2_operator_import)

from .gui_panel_view import (
    BB2_PANEL_VIEW, bb2_view_panel_update)

from .gui_panel_physics_sim import (
    BB2_PHYSICS_SIM_PANEL,
    bb2_operator_interactive,
    bb2_operator_ge_refresh)

from .gui_panel_ep import (
    BB2_EP_PANEL,
    bb2_operator_ep,
    bb2_operator_ep_clear)

from .gui_panel_mlp import (
    BB2_MLP_PANEL,
    bb2_operator_atomic_mlp,
    bb2_operator_mlp,
    bb2_operator_mlp_render)

from .gui_panel_output_animation import (
    BB2_OUTPUT_PANEL,
    bb2_operator_movie_refresh,
    bb2_operator_anim)

from .gui_panel_pdb_output import (
    BB2_PDB_OUTPUT_PANEL, bb2_operator_export_pdb)


BIOBLENDER_CLASSES = [
    bb2_operator_make_preview,
    bb2_operator_import,
    BB2_GUI_PDB_IMPORT,
    #
    bb2_view_panel_update,
    BB2_PANEL_VIEW,
    #
    bb2_operator_interactive,
    bb2_operator_ge_refresh,
    BB2_PHYSICS_SIM_PANEL,
    #
    bb2_operator_ep,
    bb2_operator_ep_clear,
    BB2_EP_PANEL,
    #
    bb2_operator_atomic_mlp,
    bb2_operator_mlp,
    bb2_operator_mlp_render,
    BB2_MLP_PANEL,
    #
    bb2_operator_movie_refresh,
    bb2_operator_anim,
    BB2_OUTPUT_PANEL,
    #
    bb2_operator_export_pdb,
    BB2_PDB_OUTPUT_PANEL
]


def register():
    # register any scene and obj props.
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

    # register operators first, then the panel.
    for cls in BIOBLENDER_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(BIOBLENDER_CLASSES):
        bpy.utils.register_class(cls)

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
