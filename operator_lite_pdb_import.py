# operator_lite_import.py
import os

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from .func_lite_pdb_import import (import_pdb, generate_meshes_from)


class PDBLiteImport(Operator, ImportHelper):
    '''
    : PDBLiteImport launches a file open dialogue to pick pdb files
    '''

    bl_idname = "scene.import_pdb_lite"
    bl_label = "LightWeight PDB importer"
    # bl_options = {'REGISTER', 'UNDO'}
    # shall be private

    filename_ext = ".pdb"

    filter_glob = StringProperty(
        default="*.pdb",
        options={'HIDDEN'},
    )

    def execute(self, context):
        bpy.context.scene.render.engine = 'CYCLES'
        pdb_name = os.path.basename(self.filepath)

        atom_dict = import_pdb(self.filepath)
        generate_meshes_from(atom_dict, pdb_name)

        return {'FINISHED'}
