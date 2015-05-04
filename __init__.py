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

if 'bpy' in globals():
    print(__package__, 'detected reload event')
    if 'bioblender_main' in globals():
        import imp

        imp.reload(app_storage)
        imp.reload(app_bootstrap)

        imp.reload(bioblender_main)
        imp.reload(utils)
        imp.reload(operator_lite_pdb_import)
        imp.reload(func_lite_pdb_import)
        # imp.reload(ui_panels)
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

    from . import bioblender_main
    from . import utils
    from . import operator_lite_pdb_import
    from . import func_lite_pdb_import
    # from . import ui_panels
    from . import gui_panel_view
    from . import gui_panel_physics_sim
    from . import gui_panel_ep
    from . import gui_panel_mlp
    from . import gui_panel_output_animation
    from . import gui_panel_pdb_output


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)
