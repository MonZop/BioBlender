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

    with open(filepath) as pdb_file:

        for line in pdb_file:
            pdl = line.strip()
            if not pdl.startswith('ATOM'):
                continue

            values = pdl.split()
            x, y, z = values[6:9]
            xyz = (float(x) * scalex, float(y) * scaley, float(z) * scalez)
            atom_type = values[-1]
            atom_dict[atom_type].append(xyz)

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


def set_autosmooth(obj):
    mesh = obj.data
    smooth_states = [True] * len(mesh.polygons)
    mesh.polygons.foreach_set('use_smooth', smooth_states)
    mesh.update()


def add_empty(basename, coordinate, kind='PLAIN_AXES'):
    empty = bpy.data.objects.new('MT_' + basename, None)
    empty.location = coordinate
    empty.empty_draw_size = 0.45
    empty.empty_draw_type = kind
    scn = bpy.context.scene
    scn.objects.link(empty)
    scn.update()
    return empty


def generate_parent(scn, atom_type, verts):
    meshes = bpy.data.meshes
    objects = bpy.data.objects

    # every atom of certain type goes into the same mesh
    mesh = meshes.new('atoms_' + atom_type)
    mesh.from_pydata(verts, [], [])
    mesh.update()

    # create an object to assign the mesh data to
    obj = objects.new('atoms_' + atom_type, mesh)
    scn.objects.link(obj)
    return obj


def generate_child(scn, atom_type):
    meshes = bpy.data.meshes
    objects = bpy.data.objects

    # create a donor mesh (child) to represent each of these atoms
    # this mesh is duplicated onto each vertex of the atoms_* parent mesh
    diameter = scale_cov[atom_type][0] * scalex  # unified
    verts, edges, faces = create_icospehere(2, diameter)
    mesh = meshes.new('repr_atom_' + atom_type)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # child must be an object too
    obj_child_repr = objects.new('repr_atoms_' + atom_type, mesh)
    scn.objects.link(obj_child_repr)
    set_autosmooth(obj_child_repr)
    return obj_child_repr


def set_child_material(atom_type, obj_child_repr):
    # make material and assign to child as active material.
    mat = bpy.data.materials.new('bb_material_' + atom_type)
    mat.use_nodes = True
    mat.use_fake_user = True  # usually handy
    obj_child_repr.active_material = mat

    # set the diffuse color for the node-based material
    atom_color = color[atom_type] + [1.0]
    node = mat.node_tree.nodes['Diffuse BSDF']
    node.inputs[0].default_value = atom_color


def generate_meshes_from(atom_dict, pdb_name):
    '''
    : makes an Empty called mt
        - parent of all atom clouds of this pdb

    : obj
        - the cloud used to store all atoms of one kind
        - set duplication to Vertices so it can take
          obj_child on each vertex.

    : obj_child
        - the atom representation for this atom_type
        - has material unique this atom_type
    '''

    scn = bpy.context.scene

    mt = add_empty(pdb_name, (0, 0, 0))

    for atom_type, verts in atom_dict.items():

        obj = generate_parent(scn, atom_type, verts)
        obj.parent = mt
        obj.dupli_type = 'VERTS'

        obj_child_repr = generate_child(scn, atom_type)
        obj_child_repr.parent = obj
        set_child_material(atom_type, obj_child_repr)
