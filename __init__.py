bl_info = {
    "name": "BioBlender 2.5",
    "author": "SciVis, IFC-CNR, et all",
    "version": (2, 5),
    "blender": (2, 7, 4),
    "location": "Properties Window > Scene",
    "description": "BioBlender 2.5 - rewrite of 2.0",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "http://bioblender.eu/?page_id=665",
    "category": "Add Mesh"
}

'''
the following if/else exists only to deal with
F8 reloads, handy for development, and essential
for co-existing on a Blender install where F8 is
used frequently. Not all kinds of code changes can
be dealt with by this reload strategy, in that case
the only path is to close/reopen Blender.

'''

import sys

if 'bpy' in globals():
    print(__package__, 'detected reload event')
    if 'bioblender_main' in globals():
        import imp

        imp.reload(app_storage)
        imp.reload(app_bootstrap)

        imp.reload(utils)
        imp.reload(operator_lite_pdb_import)
        imp.reload(func_lite_pdb_import)

        imp.reload(bioblender_main)
        imp.reload(gui_panel_pdb_import)
        imp.reload(gui_panel_view)
        imp.reload(gui_panel_physics_sim)
        imp.reload(gui_panel_ep)
        imp.reload(gui_panel_mlp)
        imp.reload(gui_panel_output_animation)
        imp.reload(gui_panel_pdb_output)

        print('reloaded modules')
else:
    import bpy

    from . import app_storage
    from . import app_bootstrap

    from . import utils
    from . import operator_lite_pdb_import
    from . import func_lite_pdb_import

    from . import bioblender_main
    from . import gui_panel_view
    from . import gui_panel_physics_sim
    from . import gui_panel_ep
    from . import gui_panel_mlp
    from . import gui_panel_output_animation
    from . import gui_panel_pdb_output


def register():
    from bpy.props import (StringProperty, EnumProperty, IntProperty, BoolProperty)

    bpy.types.Object.BBInfo = StringProperty()
    bpy.types.Object.bb2_pdbID = StringProperty()
    bpy.types.Object.bb2_objectType = StringProperty()
    bpy.types.Object.bb2_subID = StringProperty()
    bpy.types.Object.bb2_pdbPath = StringProperty()
    bpy.types.Object.bb2_outputOptions = EnumProperty(
        name="bb2_outputoptions", default="1",
        items=[
            ("0", "Main", ""), ("1", "+Side", ""), ("2", "+Hyd", ""),
            ("3", "Surface", ""), ("4", "MLP Main", ""), ("5", "MLP +Side", ""),
            ("6", "MLP +Hyd", ""), ("7", "MLP Surface", "")])

    opSystem = utils.detect_os()
    homePath = utils.get_homepath()
    print(opSystem, '\n', homePath)

    bpy.types.Scene.bb25_importReady = BoolProperty(default=False)
    bpy.types.Scene.bb25_bootstrap = IntProperty(default=-1)

    bpy.types.Scene.bb25_opSystem = StringProperty(default=opSystem)
    bpy.types.Scene.bb25_homepath = StringProperty(attr='bb25_homepath', default=homePath)
    bpy.types.Scene.bb25_blenderPath = StringProperty(default=str(sys.executable))

    pyPath, pyMolPath = utils.get_pyPath_pyMolPath(opSystem)
    bpy.types.Scene.bb25_pyPath = StringProperty(default=pyPath)
    bpy.types.Scene.bb25_pyMolPath = StringProperty(default=pyMolPath)

    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

    # del any scene props
    Obj = bpy.types.Object
    Scn = bpy.types.Scene
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
    del scn.bb25_importReady
    del scn.bb25_bootstrap
