'''
bioblender_main.py
for license see LICENSE.txt

'''
import sys
import bpy

# from .utils import (
#     file_append,
#     detect_os,
#     get_homepath,
#     get_pyPath_pyMolPath)

# from .tables import (
#     color,
#     values_fi,
#     molecules_structure,
#     scale_vdw, scale_cov,
#     NucleicAtoms, NucleicAtoms_Filtered)

# from .ui_panels import ImportDisposablePDB
from .gui_panel_pdb_import import (
    BB2_GUI_PDB_IMPORT,
    bb2_operator_make_preview, bb2_operator_import)

from .gui_panel_view import (
    BB2_PANEL_VIEW, bb2_view_panel_update)

from .gui_panel_physics_sim import (
    BB2_PHYSICS_SIM_PANEL,
    bb2_operator_interactive, bb2_operator_ge_refresh)

from .gui_panel_ep import (
    BB2_EP_PANEL,
    bb2_operator_ep, bb2_operator_ep_clear)

from .gui_panel_mlp import (
    BB2_MLP_PANEL,
    bb2_operator_atomic_mlp, bb2_operator_mlp, bb2_operator_mlp_render)

from .gui_panel_output_animation import (
    BB2_OUTPUT_PANEL,
    bb2_operator_movie_refresh, bb2_operator_anim)

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
    for cls in BIOBLENDER_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(BIOBLENDER_CLASSES):
        bpy.utils.unregister_class(cls)
