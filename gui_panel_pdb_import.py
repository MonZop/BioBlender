import os
import copy

import bpy
from bpy import (types, props)

import mathutils
from mathutils import Vector, Matrix

# import bpy.path
from bpy.path import abspath

from .utils import (PDBString, file_append)
from .app_bootstrap import (
    bootstrapping,
    C, N, O, S, H, CA, P, FE, MG, ZN, CU, NA, K, CL, MN, F
)

from .app_storage import (
    pdbIDmodelsDictionary,
    mainChainCacheDict,
    mainChainCache_NucleicDict,
    mainChainCache_Nucleic_FilteredDict,
    chainCacheDict,
    chainCache_NucleicDict,
    pdbIDmodelsDictionary,
    pdbID
)

from .tables import (
    color,
    values_fi,
    molecules_structure,
    scale_vdw, scale_cov,
    NucleicAtoms, NucleicAtoms_Filtered)

importReady = False
bootstrap = -1


class BB2_GUI_PDB_IMPORT(bpy.types.Panel):
    bl_idname = "BB2_GUI_PDB_IMPORT"
    bl_label = "BioBlender 2 PDB import"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    types.Scene.BBDeltaFrame = props.IntProperty(attr="BBDeltaFrame", name="Keyframe Interval", description="The number of in-between frames between each model for animation", default=100, min=1, max=200, soft_min=5, soft_max=50)
    types.Scene.BBLayerImport = props.BoolVectorProperty(attr="BBLayerImport", size=20, subtype='LAYER', name="Import on Layer", description="Import on Layer")
    types.Scene.BBImportPath = props.StringProperty(attr="BBImportPath", description="", default="", subtype="FILE_PATH")
    types.Scene.BBModelRemark = props.StringProperty(attr="BBModelRemark", description="Model name tag for multiple imports", default="protein0")
    types.Scene.BBImportFeedback = props.StringProperty(attr="BBImportFeedback", description="Import Feedback", default="")
    types.Scene.BBImportChain = props.StringProperty(attr="BBImportChain", description="Import Chain", default="")
    types.Scene.BBImportChainOrder = props.StringProperty(attr="BBImportChainOrder", description="List of chains to be imported", default="")
    types.Scene.BBImportOrder = props.StringProperty(attr="BBImportOrder", description="List of models to be imported", default="")
    types.Scene.BBImportHydrogen = props.BoolProperty(attr="BBImportHydrogen", name="Import Hydrogen", description="Import hydrogen atoms (Slower)", default=False)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        split = layout.split(percentage=0.7)
        split.prop(scene, "BBImportPath", text="")
        split.operator("ops.bb2_operator_make_preview")
        row = layout.row()
        row.prop(scene, "BBModelRemark", text="")
        row = layout.row()
        row.prop(scene, "BBImportFeedback", text="", emboss=False)
        row = layout.row()
        # left column
        split = layout.split(percentage=0.7)
        col = split.column()
        col.prop(scene, "BBImportOrder", text="")
        # right column
        col = split.column()
        col.prop(scene, "BBDeltaFrame")
        # next row
        row = layout.row()
        row.prop(scene, "BBImportChain", text="", emboss=False)
        row = layout.row()
        row.prop(scene, "BBImportChainOrder", text="")
        row = layout.row()
        row.prop(scene, "BBLayerImport")
        row = layout.row()
        row.prop(scene, "BBImportHydrogen")
        row = layout.row()
        row.scale_y = 2
        if importReady:
            # row.operator_context = 'INVOKE_REGION_WIN'
            row.operator("ops.bb2_operator_import")
        else:
            row.active = False
            row.operator("ops.bb2_operator_import", text="Error: Not Ready to Import", icon="X")


class bb2_operator_make_preview(types.Operator):
    bl_idname = "ops.bb2_operator_make_preview"
    bl_label = "Make Preview"
    bl_description = "Make Preview"

    def invoke(self, context, event):
        try:
            if bootstrap == -1:
                bootstrapping()  # context)

            global importReady
            importReady = False
            bpy.context.scene.BBImportFeedback = ""
            bpy.context.scene.BBImportChain = ""
            bpy.context.scene.BBImportOrder = ""
            bpy.context.scene.BBImportChainOrder = ""
            importReady = importPreview(retrieved=False)
            print("Import Ready: " + str(importReady))
        except Exception as E:
            s = "Import Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return{'FINISHED'}


class bb2_operator_import(types.Operator):
    bl_idname = "ops.bb2_operator_import"
    bl_label = "Import PDB"
    bl_description = "generate 3D Model"

    def invoke(self, context, event):
        try:
            if bootstrap == 0:
                bootstrap()
            bpy.context.user_preferences.edit.use_global_undo = False
            core_importFile()
            bpy.context.user_preferences.edit.use_global_undo = True
        except Exception as E:
            s = "Import Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return{'FINISHED'}


# validate and get the number of models in the BBImportOrder string
def getNumModel():
    try:
        tmpPDBmodelsList = [int(tmpPDBmodelsBBio) for tmpPDBmodelsBBio in bpy.context.scene.BBImportOrder.split(',')]
        print("get_num_model: " + str(tmpPDBmodelsList))
        return len(tmpPDBmodelsList)
    except:
        return -1


def index_element(this_list, elemen_list):
    print("index_element")
    for ik in range(len(this_list)):
        if elemen_list == this_list[ik]:
            return ik


def importPreview(verbose=False, retrieved=False):
    global chainCount
    global importChainID
    print("Import Preview")
    tmpPreviewFilePath = abspath(str(bpy.context.scene.BBImportPath))
    # get PDB straight from PDB.org
    if (len(tmpPreviewFilePath) == 4) and not(retrieved):
        retrievedFile = pdbdotorg(tmpPreviewFilePath)
        if retrievedFile:
            bpy.context.scene.BBImportFeedback = "Found matching Protein on PDB.org"
        else:
            bpy.context.scene.BBImportFeedback = "Nothing matching this ID found on PDB.org"
            return False
    extension = str(bpy.context.scene.BBImportPath).lower().endswith
    try:
        # file = open(tmpPreviewFilePath,"r")
        file = open(str(bpy.context.scene.BBImportPath), "r")
    except:
        bpy.context.scene.BBImportFeedback = "File not found"
        return False
    else:
        if extension(".pdb") or extension(".pqr") or extension(".txt"):
            bpy.context.scene.BBModelRemark = bpy.context.scene.BBImportPath[-8:-4]
        else:
            bpy.context.scene.BBModelRemark = bpy.context.scene.BBImportPath[-4:]
        # open is successful, check file extension
        if extension(".pdb") or extension(".pqr"):
            modelCount = 0
            importFileModel = []
            # read the chain id
            chainCount = 0
            importChainID = []
            # read file
            for line in file:
                line = PDBString(line)
                # count number of models in file using the start tag MODEL
                if line.get("tag") == "MODEL":
                    tmpPreviewModelID = line.get("modelID")
                    importFileModel.append(tmpPreviewModelID)
                # count number of models in file using the end tag MODEL
                elif line.get("tag") == "ENDMDL":
                    modelCount += 1
                # count number of chains in file using the start tag ATOM    1
                if line.get("tag") == "ATOM":
                    currentChainID = line.get("chainID")
                    if currentChainID not in importChainID:
                        chainCount += 1
                        importChainID.append(currentChainID)
            # Special case for files containing 1 model with no opening model tag
            if len(importFileModel) == 0:
                importFileModel.append(0)

            # show list of models for importer to load
            bpy.context.scene.BBImportOrder = str(importFileModel)[1:-1]
            # if all okay, display feedback message
            bpy.context.scene.BBImportFeedback = "File contains " + str(len(importFileModel)) + " PDB Models"
            # if all okay, display feedback message
            bpy.context.scene.BBImportChain = "File contains chains " + str(importChainID)
            tmpChainOrderString = ",".join(importChainID)
            bpy.context.scene.BBImportChainOrder = str(tmpChainOrderString)
            file.close()
            return True
        if extension(".txt") or extension(".csv"):
            # simply get list of all files from a th specified directory
            fileList = os.listdir(os.path.dirname(tmpPreviewFilePath))
            fileListClean = []
            for f in fileList:
                # find only matching extensions
                ext = f[-4:].lower()
                if ext == '.txt' or ext == '.csv':
                    fileListClean.append(f)
            bpy.context.scene.BBImportOrder = ", ".join(fileListClean)
            # if all okay, display feedback message
            bpy.context.scene.BBImportFeedback = "Folder contains " + str(len(fileListClean)) + " text Files"
            file.close()
            return True
        # otherwise...
        bpy.context.scene.BBImportFeedback = "Error: Unrecognized File Extension"
        file.close()
        return False


# retrieve PDB from pdb.org
def pdbdotorg(id):
    print("pdbdotorg")
    url1 = str("http://www.pdb.org/pdb/files/" + id + ".pdb")
    save1 = str(homePath + "fetched" + os.sep + id + ".pdb")
    if opSystem == "linux":
        if not os.path.isdir(quotedPath(homePath + "fetched")):
            os.mkdir(quotedPath(homePath + "fetched"))
    elif opSystem == "darwin":
        if not os.path.isdir(quotedPath(homePath + "fetched")):
            os.mkdir(quotedPath(homePath + "fetched"))
    else:
        if not os.path.isdir(r"\\?\\" + homePath + "fetched"):
            os.mkdir(r"\\?\\" + homePath + "fetched")
    # get file from the web
    try:
        filename, header = urlretrieve(url1, save1)
        bpy.context.scene.BBImportPath = save1
        importPreview(False, True)
        return filename
    except:
        return False


def core_importFile():
    print("core_import_File")
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select = False
    bpy.context.scene.objects.active = None
    tmpFilePath = abspath(bpy.context.scene.BBImportPath)
    extension = tmpFilePath.lower().endswith
    # user input sanity check
    if getNumModel() == -1:
        raise Exception("Error: Invalid user ordering of model sequence.  Use comma to separate values")
    if extension(".pdb") or extension(".pqr"):
        core_parsePDB(tmpFilePath)
    elif extension(".txt") or extension(".csv"):
        core_parseTXT(tmpFilePath)


def core_parsePDB(filePath):
    print("core_parse_pdb")
    tmpPDBmodelDictionary = {}      # key: atom name; value: String, the Atom BBInfo; for the CURRENT model
    tmpPDBmodelID = 0
    tmpPDBmodelImportOrder = [int(tmpM) for tmpM in bpy.context.scene.BBImportOrder.split(',')]
    global mainChainCacheDict
    global mainChainCache_NucleicDict
    global mainChainCache_Nucleic_FilteredDict
    global chainCacheDict
    global chainCache_NucleicDict
    global pdbIDmodelsDictionary

    # New, due to multi-pdb version wrapped on a single-pdb one
    mainChainCache = []        # a cache to that contains only mainchain atoms
    mainChainCache_Nucleic = []
    mainChainCache_Nucleic_Filtered = []
    chainCache = {}            # a cache to that contains all non-H atoms
    chainCache_Nucleic = {}

    pdbIDmodelsDictionary[pdbID] = {}

    global importChainOrderList
    importChainOrderList = []
    importChainOrderList = [tmpCOLI for tmpCOLI in bpy.context.scene.BBImportChainOrder.split(',')]

    # 2013-06-28 ---  Removes "1+" and "1-"... hoping it will not affect "standard" files...
    try:
        f = open(filePath, "r")
        lines = f.readlines()
        lineCounter = 0
        for line in lines:
            if(line.startswith("ATOM")):
                line = line.replace("1+", "  ")
                line = line.replace("1-", "  ")
            lines[lineCounter] = line
            lineCounter = lineCounter + 1
        f.close()
        f = open(filePath, "w")
        f.writelines(lines)
        f.close()
    except Exception as E:
        s = "Unable to fix tmp.pdb: " + str(E)
        print(s)

    print("A")
    # open file (assuming input is valid)
    with open(filePath, "r") as file:
        for line in file:
            line = line.replace("\n", "")
            line = line.replace("\r", "")
            line = PDBString(line)
            tag = line.get("tag")
            # if tag is tmpPDBmodelDictionary, load tmpPDBmodelDictionary id
            if tag == "MODEL":
                tmpPDBmodelID = line.get("modelID")
            # if tag is ATOM, load column data (skip this if tmpPDBmodelID is not in list of models)
            elif (tmpPDBmodelID in tmpPDBmodelImportOrder) and (tag == "ATOM" or tag == "HETATM"):
                # check for element type
                atomName = line.get("name")
                elementName = line.get("element")
                elementTypeResidue = line.get("aminoName").strip()
                atomtype = line.get("tag")
                # skip water
                if line.get("aminoName") == "HOH":
                    continue
                # decide if hydrogen should be skipped
                if not bpy.context.scene.BBImportHydrogen and elementName == H:
                    continue
                # decide if current Chain should be skipped
                if (line.get("chainID") not in importChainOrderList):
                    continue
                tmpPDBobjectName = bpy.context.scene.BBModelRemark
                key = str(tmpPDBobjectName) + "#" + line.get("serial").rjust(5, "0")
                tmpPDBmodelDictionary[key] = line

                # add mchain atom data to dictionary for building bonds
                if atomName == N or atomName == C or (atomName == CA and elementName != CA):
                    if key not in mainChainCache:
                        mainChainCache.append(key)

                if atomName in NucleicAtoms:
                    if atomName in NucleicAtoms_Filtered:
                        if key not in mainChainCache_Nucleic_Filtered:
                            mainChainCache_Nucleic_Filtered.append(key)
                    else:
                        if key not in mainChainCache_Nucleic:
                            mainChainCache_Nucleic.append(key)

                    if atomName == "C3'":
                        mainChainCache_Nucleic.append(key)

                # add all atom data to dictionary for building bonds
                elementTypeNucleic = ["D", "A", "U", "G", "C", "DC", "DG", "DA", "DT"]
                if elementName != H and not (elementTypeResidue in elementTypeNucleic) and atomtype == "ATOM":
                    chainCache[key] = line.get("aminoName") + "#" + line.get("chainSeq") + "#" + line.get("name") + "#" + line.get("chainID") + "#" + line.get("element")
                if elementName != H and (elementTypeResidue in elementTypeNucleic) and atomtype == "ATOM":
                    chainCache_Nucleic[key] = line.get("aminoName") + "#" + line.get("chainSeq") + "#" + line.get("name") + "#" + line.get("chainID") + "#" + line.get("element")
                # To multi-pdb: insert caches above in global chain caches dictionaries, using pdbID as key:
            # when the end of a tmpPDBmodelDictionary is reached, add the tmpPDBmodelDictionary dictionary to the list
            if tag == "ENDMDL" or tag == "END" or tag == "MODEL" and (tmpPDBmodelID in tmpPDBmodelImportOrder):
                # We add a new MODEL entry to the global pdbIDmodelsDictionary[pdbID],
                # based on the current MODEL ID, and we assign the tmpPDBmodelDictionary to this entry.
                (pdbIDmodelsDictionary[pdbID])[tmpPDBmodelID] = tmpPDBmodelDictionary
                # So now pdbIDmodelsDictionary[pdbID] is a Dictionary: model-dict; the second dict is [atomName]-BBInfo
                tmpPDBmodelDictionary = {}
    mainChainCacheDict[pdbID] = mainChainCache
    mainChainCache_NucleicDict[pdbID] = mainChainCache_Nucleic
    mainChainCache_Nucleic_FilteredDict[pdbID] = mainChainCache_Nucleic_Filtered
    chainCacheDict[pdbID] = chainCache
    chainCache_NucleicDict[pdbID] = chainCache_Nucleic
    core_sort_hr()


def core_parseTXT(filePath):
    tmpPDBmodelDictionary = {}
    global pdbIDmodelsDictionary
    # Parse text files sequence
    tmpPDBmodelImportOrder = bpy.context.scene.BBImportOrder.split(',')
    for fileName in tmpPDBmodelImportOrder:
        # open each file from the list
        with open(os.path.dirname(filePath) + "/" + fileName.strip(), "r") as f:
            atomCounter = 0
            # force the atom type
            char = C
            # for each line of the file
            for line in f:
                tmpPDBobjectName = bpy.context.scene.BBModelRemark
                key = str(tmpPDBobjectName) + "#" + str(atomCounter).rjust(5, "0")
                line = line.replace('"', "")    # cleanup some unconforming data
                split_line = line.split()
                x = "%8.3f" % float(split_line[0])
                y = "%8.3f" % float(split_line[1])
                z = "%8.3f" % float(split_line[2])
                # a somewhat hackish way to generate a PDB-conformant string for the unified reader to use
                line = PDBString("ATOM                                                                         " + char)
                # insert location in-situ
                line = line.set(30, x)
                line = line.set(38, y)
                line = line.set(46, z)
                tmpPDBmodelDictionary[key] = line
                atomCounter += 1
            (pdbIDmodelsDictionary[pdbID])[0] = tmpPDBmodelDictionary
            tmpPDBmodelDictionary = {}
    core_sort_hr()


def core_sort_hr():
    scene = bpy.context.scene
    homePath = scene.bb25_homepath

    print("core_sort_hr")
    # ======= IMPORT ON SELECTED LAYER = START =======================
    selectedLayer = 0
    tmp = 0
    for x in bpy.context.scene.BBLayerImport:
        if ((x) and not (tmp == 19)):
            selectedLayer = tmp
        tmp += 1
    bpy.context.scene.layers[selectedLayer] = True
    for i in range(0, 20):
        if not (i == selectedLayer):
            bpy.context.scene.layers[i] = False
    bpy.context.scene.layers[19] = True
    # ======= IMPORT ON SELECTED LAYER = END =========================
    # loading the Atom from library.blend
    try:
        objName = "atom"
        Directory = homePath + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep
        Path = os.sep + os.sep + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep + objName
        file_append(Path, objName, Directory)

        bpy.data.objects[objName].name = objName
        bpy.data.objects[objName].select = True
        bpy.context.scene.objects.active = bpy.data.objects[objName]

    except Exception as E:
        raise Exception("Template atom object cannot be loaded from library: ", E)
    # Make high res atom model
    bpy.ops.object.modifier_add(type='SUBSURF')
    modificatore = bpy.context.scene.objects.active.modifiers[0]
    modificatore.levels = 1
    modificatore.render_levels = 1
    modificatore.name = "SubSurf1"
    bpy.ops.object.modifier_apply(modifier="SubSurf1")
    # Models (3D) creation
    core_createModels()


def core_createModels():
    print("core_create_Models")
    # Empty creation
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.context.scene.objects.active.name = copy.copy(str(bpy.context.scene.BBModelRemark))
    parentEmpty = bpy.data.objects[str(bpy.context.scene.BBModelRemark)]
    bpy.context.scene.objects.active.bb2_pdbID = copy.copy(str(pdbID))
    bpy.context.scene.objects.active.bb2_objectType = "PDBEMPTY"
    bpy.context.scene.objects.active.bb2_outputOptions = "1"
    bpy.context.scene.objects.active.bb2_pdbPath = copy.copy(str(bpy.context.scene.BBImportPath))
    bpy.data.objects[str(bpy.context.scene.BBModelRemark)].location = ((0.0, 0.0, 0.0))

    global chainCache
    global curFrame
    id = bpy.context.scene.BBModelRemark
    curFrame = 1
    # Build 3D scene from pdbIDmodelsDictionary
    for m in pdbIDmodelsDictionary[pdbID]:
        model = (pdbIDmodelsDictionary[pdbID])[m]
        # Prova: se il dizionario-model in esame e' vuoto, saltalo (non e' stato selezionato il relativo model nella lista)
        if not (model):
            continue
        # =======
        # reset
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            o.select = False
        bpy.context.scene.objects.active = None
        bpy.context.scene.frame_set(curFrame)
        # on first model, Place atoms in scene
        if curFrame == 1:
            modelCopy = model.copy()
            # select and temporary rename template atom
            bpy.data.objects["atom"].hide = False
            bpy.data.objects["atom"].select = True
            bpy.data.objects["atom"].name = str(id)
            # (count - 1) because there is the original template object.
            for i in range(len(model) - 1):
                bpy.ops.object.duplicate(linked=True, mode='DUMMY')
            try:
                # walk through list of objects and set name, location and material for each atom
                for i, obj in enumerate(bpy.data.objects):
                    # if the object is the one of those we just created (i.e. if name matches xx.0000)
                    if (obj.name.split(".")[0] == id) and (obj.type == "MESH"):
                        # descructively walk through the modelCopy varible
                        entry = modelCopy.popitem()
                        # assign obj name, material, etc.  object Locations are assigned later
                        obj.name = entry[0]
                        index = str(entry[1])[76:78].strip()
                        obj.material_slots[0].material = bpy.data.materials[index]
                        # adjust radius
                        obj.scale = [scale_cov[index][0], scale_cov[index][0], scale_cov[index][0]]
                        obj.game.radius = scale_cov[index][1]
                        # add atom info as RNA string to each object
                        obj.BBInfo = str(entry[1])
                        obj.bb2_pdbID = copy.copy(str(pdbID))
                        obj.bb2_objectType = "ATOM"
                        # Setting EMPTY as parent for this object
                        obj.select = True
                        obj.parent = bpy.data.objects[str(parentEmpty.name)]
            except Exception as E:
                raise Exception("Unable to generate 3D model from PDB File", E)

            # MAKE BONDS
            try:
                mainChainCache = mainChainCacheDict[pdbID]
                mainChainCache_Nucleic = mainChainCache_NucleicDict[pdbID]
                mainChainCache_Nucleic_Filtered = mainChainCache_Nucleic_FilteredDict[pdbID]
                chainCache = chainCacheDict[pdbID]
                chainCache_Nucleic = chainCache_NucleicDict[pdbID]
                tmpModel = (pdbIDmodelsDictionary[pdbID])[m]
                # =====
                cacheSize = len(mainChainCache) - 1
                for i, entry in enumerate(mainChainCache):
                    # Skipping Last Atom to avoid cyclic dependency
                    if i < cacheSize:
                        # Adding constraints, using atom position to correctly orient hinge x axis
                        obj = bpy.data.objects[entry]
                        nextEntry = bpy.data.objects[mainChainCache[i + 1]]
                        # line=tmpModel[0][entry]
                        line = tmpModel[entry]
                        obj.location = line.get("loc")
                        # line=tmpModel[0][mainChainCache[i+1]]
                        line = tmpModel[mainChainCache[i + 1]]
                        nextEntry.location = line.get("loc")
                        addRigidBodyRotamer(obj, nextEntry)
                # bonds for Nucleic Acids
                cacheSize = len(mainChainCache_Nucleic_Filtered) - 1
                for i, entry in enumerate(mainChainCache_Nucleic_Filtered):
                    # Skipping Last Atom to avoid cyclic dependency
                    if i < cacheSize:
                        # Adding constraints, using atom position to correctly orient hinge x axis
                        obj = bpy.data.objects[entry]
                        nextEntry = bpy.data.objects[mainChainCache_Nucleic_Filtered[i + 1]]
                        # line=tmpModel[0][entry]
                        line = tmpModel[entry]
                        obj.location = line.get("loc")
                        # line=tmpModel[0][mainChainCache_Nucleic_Filtered[i+1]]
                        line = tmpModel[mainChainCache_Nucleic_Filtered[i + 1]]
                        nextEntry.location = line.get("loc")
                        addRigidBodyRotamer(obj, nextEntry)
                chainCache = sorted(chainCache.items())
                for entry in chainCache:
                    line = entry[1].split("#")
                    amac = line[0]
                    chainSeq = line[1]
                    atom = line[2]
                    chainID = line[3]
                    # skip mainchain atoms
                    if (atom != C and atom != CA and atom != N and atom != H):
                        # for side chain, look up parents based on rules
                        parent = bondLookUp(atom=atom, amac=amac)
                        # generate name of parents
                        target = amac + "#" + chainSeq + "#" + parent[0] + "#" + chainID + "#" + parent[1]
                        # lookup name of blenderobject based on parent name
                        targetKey = "atom"
                        for item in chainCache:
                            if item[1] == target:
                                targetKey = item[0]
                                break
                        # set up the constraint
                        # 2013-06-27 --- if targetKey == CA, skip...
                        if targetKey == "atom":
                            print("TargetKey not set, will skip Rigid Body Joint")
                        else:
                            obj = bpy.data.objects[entry[0]]
                            # line=tmpModel[0][entry[0]]
                            line = tmpModel[entry[0]]
                            obj.location = line.get("loc")
                            # line=tmpModel[0][targetKey]
                            line = tmpModel[targetKey]
                            nextEntry.location = line.get("loc")
                            addRigidBodyRotamer(obj, bpy.data.objects[targetKey])

                chainCache = sorted(chainCache_Nucleic.items())
                for entry in chainCache:
                    line = entry[1].split("#")
                    amac = line[0]
                    chainSeq = line[1]
                    atom = line[2]
                    chainID = line[3]
                    # skip mainchain atoms
                    # if atom=="O2P" or atom=="O1P" or atom=="C3'" or atom=="C2'"or atom=="C1'" or atom=="O4'":
                    if not (atom in NucleicAtoms):
                        # for side chain, look up parents based on rules
                        parent = bondLookUp_NucleicMain(atom=atom, amac=amac)
                        # generate name of parents
                        target = amac + "#" + chainSeq + "#" + parent[0] + "#" + chainID + "#" + parent[1]
                        # lookup name of blenderobject based on parent name
                        targetKey = "atom"
                        for item in chainCache:
                            if item[1] == target:
                                targetKey = item[0]
                                break
                        # set up the constraint
                        if targetKey == "atom":
                            print("TargetKey not set, will skip Rigid Body Joint")
                        else:
                            obj = bpy.data.objects[entry[0]]
                            line = tmpModel[entry[0]]
                            obj.location = line.get("loc")
                            line = tmpModel[targetKey]
                            nextEntry.location = line.get("loc")
                            addRigidBodyRotamer(obj, bpy.data.objects[targetKey])
            except Exception as E:
                raise Exception("Unable to generate all bonds and constraints:", E)
        # for all models, insert key frame
        try:
            for key, line in ((pdbIDmodelsDictionary[pdbID])[m]).items():
                OBJ = bpy.data.objects[key]
                OBJ.select = True
                OBJ.location = line.get("loc")
        except Exception as E:
                raise Exception("Unable to place 3D atoms:", E)
        if len(pdbIDmodelsDictionary[pdbID]) != 1:
            # insert keyframe for animations
            try:
                bpy.ops.anim.keyframe_insert_menu(type='LocRotScale')
            except Exception as E:
                print("Exception: " + str(E))
            # advance frame
            bpy.context.scene.frame_end = curFrame
            curFrame += bpy.context.scene.BBDeltaFrame
    core_EmptyChainsCreation()


# lookup sidechain parents
def bondLookUp(atom, amac):
    if(atom == "O" or atom == "OXT"):
        parent = ["C", C]
    elif(atom == "CB" or atom == "HA" or atom == "HA2" or atom == "HA3"):
        parent = ["CA", C]
    elif(atom == "SG" or "HB" in atom or "OG" in atom or "CG" in atom):
        parent = ["CB", C]
    elif(atom == "H" or atom == "H1" or atom == "H2" or atom == "H3"):
        parent = ["N", N]
    elif(atom == "HG1"):
        parent = ["OG1", O]
    elif(atom == "HG23" or atom == "HG22" or atom == "HG21"):
        parent = ["CG2", C]
    elif(atom == "SD" or "CD" in atom or "ND" in atom or atom == "HG2" or atom == "HG3" or atom == "OD1" or atom == "OD2" or atom == "HG12" or atom == "HG13" or atom == "HG13"):
        if(amac == "ILE" or amac == "VAL"):
            parent = ["CG1", C]
        else:
            parent = ["CG", C]
    elif(atom == "CE2" or atom == "CE3" or atom == "NE2" or atom == "HD2"):
        if(amac == "GLN"):
            parent = ["CD", C]
        elif(amac == "ARG" or amac == "LYS" or amac == "PRO"):
            parent = ["CD", C]
        elif(amac == "ASP"):
            parent = ["OD2", O]
        else:
            parent = ["CD2", C]
    elif(atom == "CE1" or atom == "HD11" or atom == "HD12" or atom == "HD13" or atom == "HD1" or atom == "NE1"):
        if(amac == "HIS"):
            parent = ["ND1", N]
        else:
            parent = ["CD1", C]
    elif(atom == "NE" or atom == "HD3" or atom == "CE" or atom == "OE1" or atom == "OE2"):
        if(amac == "MET"):
            parent = ["SD", S]
        else:
            parent = ["CD", C]
    elif(atom == "CZ" or atom == "HE" or atom == "HE1"):
        if(amac == "ARG"):
            parent = ["NE", N]
        elif(amac == "TRP"):
            parent = ["NE1", N]
        elif(amac == "MET"):
            parent = ["CE", C]
        elif(amac == "PHE" or amac == "HIS" or amac == "TYR"):
            parent = ["CE1", C]
    elif(atom == "NH1" or atom == "NH2" or atom == "HZ" or atom == "OH"):
        parent = ["CZ", C]
    elif(atom == "HH11" or atom == "HH12" or atom == "1HH1" or atom == "1HH2"):
        parent = ["NH1", N]
    elif(atom == "HH21" or atom == "HH22" or atom == "2HH2" or atom == "1HH2"):
        parent = ["NH2", N]
    elif(atom == "HD21" or atom == "HD22" or atom == "HD23"):
        if(amac == "LEU"):
            parent = ["CD2", C]
        else:
            parent = ["ND2", N]
    elif(atom == "HE3" or atom == "NZ"):
        if(amac == "TRP"):
            parent = ["CE3", C]
        else:
            parent = ["CE", C]
    elif(atom == "HZ1" or atom == "HZ2" or atom == "HZ3"):
        if(amac == "TRP" and atom == "HZ2"):
            parent = ["CZ2", S]
        elif(amac == "TRP" and atom == "HZ3"):
            parent = ["CZ3", S]
        else:
            parent = ["NZ", N]
    elif(atom == "HG"):
        if(amac == "LEU"):
            parent = ["CG", C]
        if(amac == "CYS"):
            parent = ["SG", S]
        else:
            parent = ["OG", O]
    elif(atom == "HE2" or atom == "CZ2" or atom == "HE21" or atom == "HE22"):
        if(amac == "HIS" or amac == "GLN"):
            parent = ["NE2", N]
        elif(amac == "PHE" or amac == "TYR" or amac == "TRP"):
            parent = ["CE2", C]
        elif(amac == "GLU"):
            parent = ["OE2", O]
        elif(amac == "MET" or amac == "LYS"):
            parent = ["CE", C]
    elif(atom == "HH"):
        parent = ["OH", O]
    elif(atom == "CZ3"):
        parent = ["CE3", C]
    elif(atom == "CH2"):
        parent = ["CZ2", C]
    elif(atom == "HH2"):
        parent = ["CH2", C]
    return parent


def bondLookUp_NucleicMain(atom, amac):  # define skeleton atoms
    print("entrati nel bondlookupnucleicmain")
    print("atom")
    print(str(atom))
    print("amac")
    print(str(amac))
    print("---calculating----")
    if(atom == "O4\'"):
        parent = ["C4\'", C]
    elif(atom == "C2\'"):
        parent = ["C3\'", C]
    elif(atom == "O2\'"):
        parent = ["C2\'", C]
    elif(atom == "C1\'"):
        parent = ["C2\'", C]
    # define base atoms
    elif(atom == "N9"):
        parent = ["C1\'", C]
    elif(atom == "C8"):
        parent = ["N9", N]
    elif(atom == "N7"):
        parent = ["C8", C]
    elif(atom == "C4"):
        if(amac == "A" or amac == "DA" or amac == "G" or amac == "DG"):
            parent = ["N9", N]
        elif(amac == "C" or amac == "DC") or(amac == "U" or amac == "DT"):
            parent = ["N3", N]
    elif(atom == "C5"):
        parent = ["C4", C]
    elif(atom == "N3"):
        if(amac == "A" or amac == "DA" or amac == "G" or amac == "DG"):
            parent = ["C4", C]
        elif(amac == "C" or amac == "DC" or amac == "U" or amac == "DT"):
            parent = ["C2", C]
    elif(atom == "C2"):
        if(amac == "A" or amac == "DA" or amac == "G" or amac == "DG"):
            parent = ["N3", N]
        elif(amac == "C" or amac == "DC" or amac == "U" or amac == "DT"):
            parent = ["N1", N]
    elif(atom == "N1"):
        if(amac == "A" or amac == "DA" or amac == "G" or amac == "DG"):
            parent = ["C2", C]
        elif(amac == "C" or amac == "DC" or amac == "U" or amac == "DT"):
            parent = ["C1\'", C]
    elif(atom == "C6"):
        if(amac == "A" or amac == "DA" or amac == "G" or amac == "DG"):
            parent = ["N1", N]
        elif(amac == "C" or amac == "DC" or amac == "U" or amac == "DT"):
            parent = ["C5", C]
    elif(atom == "N6" or atom == "O6"):
        parent = ["C6", C]
    elif(atom == "N2" or atom == "O2"):
        parent = ["C2", C]
    elif(atom == "N4" or atom == "O4"):
        parent = ["C4", C]
    elif(atom == "C7"):
        parent = ["C5", C]
    print("parent")
    print(str(parent))
    print("returned")
    return parent


# I suppose that the object's referential was not change (the same as the scene, with x (red axis)
#  to the right, z (blue axis) up and y (green axis) behing)
def addRigidBodyRotamer(objectparent, objecttarget):
    # Add the rigid body joint for rotamer
    # to define a rotamer, an hinge is use, with the axis vector which come from the atom parent to
    # the target and with a position at the center of the parent atom. This rotation transform the
    # Ox axis of the parent, to the euler angle to orient the x axes (the hinge axis) of the pivot
    # referential from this parent atom to the target
    parentxaxis = Vector((1.0, 0.0, 0.0))
    hingevector = Vector((
        objecttarget.location[0] - objectparent.location[0],
        objecttarget.location[1] - objectparent.location[1],
        objecttarget.location[2] - objectparent.location[2]))

    rotvec2mapx2hingevector = parentxaxis.cross(hingevector)
    rotvec2mapx2hingevector.normalize()
    angle2mapx2hingevector = parentxaxis.angle(hingevector)
    matrot = Matrix.Rotation(angle2mapx2hingevector, 3, rotvec2mapx2hingevector)
    euler = matrot.to_euler()
    # Add the rigid body join for rotamer
    objectparent.constraints["RigidBody Joint"].target = objecttarget
    # objectparent.constraints["RigidBody Joint"].show_pivot = True
    objectparent.constraints["RigidBody Joint"].pivot_x = 0.0
    objectparent.constraints["RigidBody Joint"].pivot_y = 0.0
    objectparent.constraints["RigidBody Joint"].pivot_z = 0.0
    objectparent.constraints["RigidBody Joint"].axis_x = euler[0]
    objectparent.constraints["RigidBody Joint"].axis_y = euler[1]
    objectparent.constraints["RigidBody Joint"].axis_z = euler[2]
    # objectparent.rotation_mode='XYZ'


def core_EmptyChainsCreation():
    print("Empty Chains creation")
    chainsList = []
    for o in bpy.data.objects:
        if(o.bb2_pdbID == pdbID):
            if(o.bb2_objectType == "ATOM"):
                tmpChain = str(((o.BBInfo)[21:22]).strip())
                if tmpChain not in chainsList:
                    # Creo la Empty, con le opportune proprieta'
                    bpy.ops.object.empty_add(type='PLAIN_AXES')
                    bpy.context.scene.objects.active.name = copy.copy(str(bpy.context.scene.BBModelRemark))
                    bpy.context.scene.objects.active.bb2_pdbID = copy.copy(str(pdbID))
                    bpy.context.scene.objects.active.bb2_objectType = "CHAINEMPTY"
                    bpy.context.scene.objects.active.bb2_subID = copy.copy(str(tmpChain))
                    bpy.context.scene.objects.active.location = ((0.0, 0.0, 0.0))
                    tmpName = copy.copy(str(bpy.context.scene.objects.active.name))
                    cE = bpy.data.objects[tmpName]
                    # imposto la Empty come figlia della Parent Empty
                    for d in bpy.data.objects:
                        if(d.bb2_pdbID == pdbID):
                            if(d.bb2_objectType == "PDBEMPTY"):
                                cE.parent = bpy.data.objects[str(d.name)]
                    # imposto l'oggetto come figlio di questa Empty, non piu' della Parent Empty
                    o.parent = cE
                    # inserisco questa sigla nella lista di ID
                    chainsList.append(tmpChain)
                else:
                    for c in bpy.data.objects:
                        if(c.bb2_pdbID == pdbID):
                            if(c.bb2_objectType == "CHAINEMPTY"):
                                if(c.bb2_subID == tmpChain):
                                    o.parent = bpy.data.objects[str(c.name)]
    core_cleaningUp()


def core_cleaningUp():
    print("cleaning up")
    bpy.context.scene.frame_set(1)
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select = False

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].show_relationship_lines = False

    try:
        atomAction()
    except Exception as E:
        print("No models, no action")

    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select = False
    bpy.data.objects['BioBlender_Camera'].select = True
    bpy.context.scene.objects.active = bpy.data.objects['BioBlender_Camera']
    bpy.context.scene.camera = bpy.data.objects["BioBlender_Camera"]
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].region_3d.view_perspective = "CAMERA"

    global pdbID
    pdbID = pdbID + 1  # VERY IMPORTANT!!!
    print("pdbID: " + str(pdbID))

    sessionSave()

    bpy.context.scene.BBImportPath = ""
    bpy.context.scene.BBImportHydrogen = False

    global chainCount
    global importChainID
    global importChainOrderList
    chainCount = 0
    importChainID = []
    importChainOrderList = []

    print("Finished Importing!")


def atomAction():
    print("atom_action")
    for obj in bpy.data.objects:
        if obj.BBInfo:
            obj.select = True
            bpy.context.scene.objects.active = obj
            actionName = str(obj.name + "Action")
            if actionName in bpy.data.actions.keys():
                obj.game.actuators['F-Curve'].action = bpy.data.actions[actionName]
                obj.game.actuators['F-Curve'].frame_end = bpy.data.actions[actionName].frame_range[1]
            obj.select = False


# Save the session variables to disk
def sessionSave():
    print("session_save")
    try:
        # if the blender file is not saved yet, do nothing
        if not bpy.data.is_dirty:
            # Serialize the the data and save to disk
            with open(bpy.data.filepath + ".cache", "wb") as filedump:
                pickle.dump(pdbIDmodelsDictionary, filedump)
            print("Persistent Session Saved")
        else:
            print("Warning: Blender file needs to be saved first to create persistent session data")
    except Exception as E:
        print("An error occured in sessionSave()")


# Load the saved variables from disk
def sessionLoad(verbose=False):
    print("session_load")
    global pdbIDmodelsDictionary
    # if the blender file is not saved yet, do nothing
    # if there is already a 'large' number of object in the scene:
    if not bpy.data.is_dirty and len(bpy.data.objects) > 500:
        # try to load serialized data from disk or fail silently
        try:
            with open(bpy.data.filepath + ".cache", "rb") as filedump:
                pdbIDmodelsDictionary = pickle.load(filedump)
            select(bpy.data.objects[90].name)    # to select 'something' in the scene
            print("Persistent session loaded")
        except Exception as E:
            print("Warning: Error when loading session cache:", E)
