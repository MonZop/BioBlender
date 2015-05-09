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

# this is the list of modules, add here if needed.
bio_files = """\
app_storage
app_bootstrap
utils
bioblender_main
gui_panel_pdb_import
gui_panel_view
gui_panel_physics_sim
gui_panel_ep
gui_panel_mlp
gui_panel_output_animation
gui_panel_pdb_output
"""

import sys

'''
The following if/else exists only to deal with F8 reloads, and is
handy for development, and essential even essential for co-existing
on a Blender install where F8 is used frequently. Not all kinds of
code changes can be dealt with by this reload strategy, in that case
the only path is to close/reopen Blender.
'''

if 'bpy' in globals():
    print(__package__, 'detected reload event')
    if 'app_storage' in globals():
        import imp
        for f in bio_files.split():
            exec('imp.reload({file})'.format(file=f))
        print('reloaded modules')
else:
    import bpy
    for f in bio_files.split():
        exec('from . import {file}'.format(file=f))
    print('imported bio blender modules.')


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
    bpy.types.Scene.bb25_importReady = BoolProperty(default=False)
    bpy.types.Scene.bb25_bootstrap = IntProperty(default=-1)
    bpy.types.Scene.bb25_opSystem = StringProperty(default=opSystem)
    bpy.types.Scene.bb25_homepath = StringProperty(attr='bb25_homepath', default=homePath)
    bpy.types.Scene.bb25_blenderPath = StringProperty(default=str(sys.executable))

    pyPath, pyMolPath = utils.get_pyPath_pyMolPath(opSystem)
    bpy.types.Scene.bb25_pyPath = StringProperty(default=pyPath)
    bpy.types.Scene.bb25_pyMolPath = StringProperty(default=pyMolPath)

    # global reference to the index of a pdb model, each new import is +1
    # it might be more subtle than that, like a new index per molecule imported,
    # but I don't know for certain.
    bpy.types.Scene.bb25_pdbID = IntProperty(default=0)

    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

    # del any scene or obj props
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
    del Scn.bb25_importReady
    del Scn.bb25_bootstrap
    del Scn.bb25_pdbID
