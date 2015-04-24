# disposable_pdb_import.py

import os
from collections import defaultdict

import bpy
import bmesh

from .tables import (color, scale_cov)

''' Handle PDB import '''

scalex = 0.12
scaley = 0.12
scalez = 0.12


def import_pdb(filepath):

    atom_dict = defaultdict(list)

    def inspect_line_by_line(pdb_file):
        for line in pdb_file:
            # protein data line: pdl
            pdl = line.strip()
            if not pdl.startswith('ATOM'):
                continue

            values = pdl.split()
            x, y, z = values[6:9]
            xyz = (float(x) * scalex, float(y) * scaley, float(z) * scalez)
            atom_type = values[-1]
            atom_dict[atom_type].append(xyz)

    def pdb_import_intermediate():
        with open(filepath) as pdb_file:
            inspect_line_by_line(pdb_file)

    pdb_import_intermediate()
    return atom_dict


''' Handle mesh construction '''


def pydata_from_bmesh(bm):
    v = [v.co[:] for v in bm.verts]
    e = [[i.index for i in e.verts] for e in bm.edges[:]]
    p = [[i.index for i in p.verts] for p in bm.faces[:]]
    return v, e, p


def create_icospehere(subdiv, d):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, diameter=d)
    v, e, p = pydata_from_bmesh(bm)
    bm.free()
    return v, e, p


def add_empty(basename, coordinate, kind='PLAIN_AXES'):
    empty = bpy.data.objects.new('MT_' + basename, None)
    empty.location = coordinate
    empty.empty_draw_size = 0.45
    empty.empty_draw_type = kind
    scn = bpy.context.scene
    scn.objects.link(empty)
    scn.update()
    return empty


def generate_meshes_from(atom_dict, pdb_name):

    ''' Aliases and variables and constants '''

    meshes = bpy.data.meshes
    objects = bpy.data.objects
    scene = bpy.context.scene
    mt = add_empty(pdb_name, (0, 0, 0))

    for atom_type, verts in atom_dict.items():

        ''' parent '''
        # generate a new mesh, ever atom of certain type goes into the same
        # mesh
        mesh = meshes.new('atoms_' + atom_type)
        mesh.from_pydata(verts, [], [])
        mesh.update()

        # create an object to assign the mesh data to
        obj = objects.new('atoms_' + atom_type, mesh)
        scene.objects.link(obj)
        obj.parent = mt

        ''' child '''
        # create a donor mesh (child) to represent each of these atoms
        # this mesh is duplicated onto each vertex of the atoms_* parent mesh
        diameter = scale_cov[atom_type][0] * scalex  # unified
        verts, edges, faces = create_icospehere(2, diameter)
        mesh = meshes.new('repr_atom_' + atom_type)
        mesh.from_pydata(verts, [], faces)
        mesh.update()

        # child must be an object too
        obj_child_repr = objects.new('repr_atoms_' + atom_type, mesh)
        scene.objects.link(obj_child_repr)

        # make material and assign to child as active material.
        mat = bpy.data.materials.new('bb_material_' + atom_type)
        mat.use_nodes = True
        mat.use_fake_user = True  # usually handy
        obj_child_repr.active_material = mat

        # set the diffuse color for the node-based material
        atom_color = color[atom_type] + [1.0]
        node = mat.node_tree.nodes['Diffuse BSDF']
        node.inputs[0].default_value = atom_color

        # attach the child to the parent object's vertices
        obj.dupli_type = 'VERTS'
        obj_child_repr.parent = obj

        def set_autosmooth(obj):
            mesh = obj.data
            smooth_states = [True] * len(mesh.polygons)
            mesh.polygons.foreach_set('use_smooth', smooth_states)
            mesh.update()

        set_autosmooth(obj_child_repr)
