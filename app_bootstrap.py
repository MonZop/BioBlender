import bpy

from .tables import (
    color,
    values_fi,
    molecules_structure,
    scale_vdw, scale_cov,
    NucleicAtoms, NucleicAtoms_Filtered)


def bootstrapping():
    print("Bootstrapping")

    # aliases
    scene = bpy.context.scene
    materials = bpy.data.materials

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

    elencoMateriali = [CA, H, N, O, S, ZN, P, FE, MG, MN, CU, NA, K, CL, F]

    # Gravity, rendering engine
    scene.render.engine = 'BLENDER_GAME'
    scene.game_settings.physics_gravity = 0.0
    scene.render.engine = 'BLENDER_RENDER'

    # Materials
    if not("C" in materials):
        bpy.ops.material.new()
        materials[-1].name = "C"
        materials["C"].diffuse_color = color[C]
    for m in elencoMateriali:
        if not(m in materials):
            materials['C'].copy()
            materials['C.001'].name = m
            materials[m].diffuse_color = color[m]
    create_fi_materials()

    # get next PDB ID
    global pdbID
    pdbID = getNewPDBid()

    # EmptySet (Hemi, BBCamera)
    scene.layers[19] = True
    for i in range(0, 19):
        scene.layers[i] = False
    scene.layers[19] = True
    elementiDaImportare = ['Empty', 'Hemi']

    try:
        for objName in elementiDaImportare:
            Directory = homePath + "data" + os.sep + "EmptySet.blend" + "/" + "Object" + "/"
            Path = os.sep + os.sep + "data" + os.sep + "EmptySet.blend" + "/" + "Object" + "/" + objName
            file_append(Path, objName, Directory)
    except Exception as E:
        raise Exception("Problem in import EmptySet.blend: ", E)

    global bootstrap
    bootstrap = 2


def getNewPDBid():
    print("get_new_PDB_id")
    tmp = 0
    for o in bpy.data.objects:
        if(o.bb2_pdbID != ""):
            tmp = o.bb2_pdbID
    tmp = tmp + 1
    return tmp


def create_fi_materials():
    print("create_fi_materials")
    global dic_lipo_materials
    materials = bpy.data.materials

    try:
        for item in molecules_structure:
            for item_at in molecules_structure[item]:
                value_fi_returned = parse_fi_values(item, item_at)
                if not (value_fi_returned in dic_lipo_materials):
                    materials['C'].copy()
                    valuecolor = value_fi_returned
                    materials['C.001'].name = "matlipo_" + str(valuecolor)

                    v = float(valuecolor)
                    materials["matlipo_" + str(valuecolor)].diffuse_color = [v, v, v]
                    dic_lipo_materials[str(valuecolor)] = "matlipo_" + str(valuecolor)
    except Exception as E:
        raise Exception("Unable to create lipo materials", E)


def parse_fi_values(am_name, at_name):
    try:
        value_of_atom = values_fi[am_name][at_name]
        if float(value_of_atom) <= 0:
            value_final = (float(value_of_atom) + 2) / 4
        else:
            value_final = (float(value_of_atom) + 1) / 2
        value_final = "%5.3f" % float(value_final)
        return value_final
    except Exception as E:
        raise Exception("Unable to parse fi values", E)


def retrieve_fi_materials(am_name, at_name):
    material_value = parse_fi_values(am_name, at_name)
    material_name = dic_lipo_materials[material_value]
    return material_name
