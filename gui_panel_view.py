currentActiveObj = ""
oldActiveObj = ""
activeModelRemark = ""
viewFilterOld = ""


class BB2_PANEL_VIEW(types.Panel):
    bl_label = "BioBlender2 View"
    bl_idname = "BB2_PANEL_VIEW"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBMLPSolventRadius = bpy.props.FloatProperty(attr="BBMLPSolventRadius", name="Solvent Radius", description="Solvent Radius used for Surface Generation", default=1.4, min=0.2, max=5, soft_min=0.4, soft_max=4)
    bpy.types.Scene.BBViewFilter = bpy.props.EnumProperty(
        attr="BBViewFilter", name="View Filter", description="Select a view mode",
        items=(
            ("1", "Main Chain", ""),
            ("2", "+ Side Chain", ""),
            ("3", "+ Hydrogen", ""),
            ("4", "Surface", "")),
        default="3")

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        r = layout.column(align=False)
        if bpy.context.scene.objects.active:
            if(bpy.context.scene.objects.active.BBInfo):
                r.label("Currently Selected Model: " + str(bpy.context.scene.objects.active.name))
            else:
                r.label("No model selected")
            r.alignment = 'LEFT'
            r.prop(bpy.context.scene.objects.active, "BBInfo", icon="MATERIAL", emboss=False)
        split = layout.split(percentage=0.5)
        r = split.row()
        r.prop(scene, "BBViewFilter", expand=False)
        split = split.row(align=True)
        split.prop(scene, "BBMLPSolventRadius")
        r = layout.row()
        r.operator("ops.bb2_view_panel_update", text="APPLY")

    @classmethod
    def poll(cls, context):
        global tag
        global currentActiveObj
        global oldActiveObj
        try:
            if bpy.context.scene.objects.active.name:
                # do a view update when the selected/active obj changes
                if bpy.context.scene.objects.active.name != oldActiveObj:
                    # get the ModelRemark of the active model
                    if bpy.context.scene.objects.active.name:
                        activeModelRemark = bpy.context.scene.objects.active.name.split("#")[0]
                        # load previous sessions from cache
                        # if not modelContainer:
                        #    # sessionLoad()
                        #    # print("Sessionload")
                        currentActiveObj = activeModelRemark
                    oldActiveObj = bpy.context.scene.objects.active.name
        except Exception as E:
            s = "Context Poll Failed: " + str(E)    # VEEEEEERY ANNOYING...
        return (context)


class bb2_view_panel_update(types.Operator):
    bl_idname = "ops.bb2_view_panel_update"
    bl_label = "Show Surface"
    bl_description = "Show Surface model"

    def invoke(self, context, event):
        print("invoke surface")
        try:
            if bpy.context.scene.objects.active:
                updateView(residue=bpy.context.scene.objects.active)
        except Exception as E:
            s = "Generate Surface Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return{'FINISHED'}


# depending on view mode, selectively hide certain object based on atom definition
def updateView(residue=None, verbose=False):
    selectedPDBidS = []
    for b in bpy.context.scene.objects:
        if b.select:
            try:
                if(b.bb2_pdbID not in selectedPDBidS):
                    t = copy.copy(b.bb2_pdbID)
                    selectedPDBidS.append(t)
            except Exception as E:
                str1 = str(E)   # Do not print...
    viewMode = bpy.context.scene.BBViewFilter
    # select amino acid by group
    if residue:
        # skip none atomic object
        if residue.BBInfo:
            seq = PDBString(residue.BBInfo).get("chainSeq")
            id = PDBString(residue.BBInfo).get("chainID")
            for o in bpy.data.objects:
                if(o.BBInfo):
                    if((PDBString(o.BBInfo).get("chainSeq") == seq) and (PDBString(o.BBInfo).get("chainID") == id)):
                        bpy.data.objects[o.name].select = True
                    else:
                        bpy.data.objects[o.name].select = False
    # ================================= SURFACES GENERATION - START ==============================
    # Check if there are SURFACES in the Scene...
    existingSurfaces = []
    for s in bpy.data.objects:
        if(s.BBInfo):
            if(s.bb2_objectType == "SURFACE"):
                existingSurfaces.append(s.name)
    if viewMode == "4":
        bpy.data.worlds[0].light_settings.use_environment_light = False
        # If there are not surfaces in Scene...
        if not existingSurfaces:
            # generate surface if does not exist... a different Surface for EVERY pdbID selected...
            # Deselect all; iteratively select objects whose IDs are in selectedPDBidS and launch setup and surface
            for id in selectedPDBidS:
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select = False
                for obj in bpy.context.scene.objects:
                    try:
                        if obj.bb2_pdbID == id:
                            obj.select = True
                    except Exception as E:
                        str2 = str(E)   # Do not print...
                tID = copy.copy(id)
                setup(setupPDBid=tID)
                print("first setup made")
                surface(sPid=tID)
                print("surface made")
        else:
            # unhide surface if it's hidden
            for ob in existingSurfaces:
                if ob.hide:
                    obj.hide = False
                    obj.hide_render = False
        todoAndviewpoints()
    # ================================= SURFACES GENERATION - END ==============================
    else:
        bpy.data.worlds[0].light_settings.use_environment_light = True
        # hide surface if already exist
        if existingSurfaces:
            for o in existingSurfaces:
                bpy.data.objects[o].hide = True
                bpy.data.objects[o].hide_render = True
    # Check for hiding / reveal objects in Scene
    for obj in bpy.context.scene.objects:
        try:
            if(obj.bb2_pdbID in selectedPDBidS):
                obj.hide = False
                obj.hide_render = False
                obj.draw_type = "TEXTURED"
                if re.search("#", obj.name):
                    line = obj.BBInfo
                    line = PDBString(line)
                    elementName = line.get("element")
                    atomName = line.get("name")
                    # hide all
                    if viewMode == "0":
                        obj.hide = True
                        obj.hide_render = True
                    # Main Chain Only
                    elif viewMode == "1":
                        if not (atomName == N or atomName == C or (atomName == CA and elementName != CA) or (atomName in NucleicAtoms) or (atomName in NucleicAtoms_Filtered)):
                            obj.hide = True
                            obj.hide_render = True
                    # Main Chain and Side Chain Only
                    elif viewMode == '2' and elementName == H:
                        obj.hide = True
                        obj.hide_render = True
                    # Main Chain and Side Chain Only and H, everything.
                    elif viewMode == '4':
                        obj.hide = True
                        obj.hide_render = True
        except Exception as E:
            str5 = str(E)   # Do nothing


def setup(verbose=False, clear=True, setupPDBid=0):
    # PDB Path is retrieved from parent EMPTY
    pE = None
    for o1 in bpy.context.scene.objects:
        try:
            if(o1.bb2_pdbID == setupPDBid):
                if(o1.bb2_objectType == "PDBEMPTY"):
                    pE = copy.copy(o1.name)
        except Exception as E:
            str3 = str(E)   # Do not print...
    print("pE: " + str(pE))
    PDBPath = abspath(bpy.data.objects[pE].bb2_pdbPath)
    print("pdppath: " + str(PDBPath))

    if clear:
        if opSystem == "linux":
            if os.path.isdir(quotedPath(homePath + "tmp" + os.sep)):
                shutil.rmtree(quotedPath(homePath + "tmp" + os.sep))
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
            else:
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
        elif opSystem == "darwin":
            if os.path.isdir(quotedPath(homePath + "tmp" + os.sep)):
                shutil.rmtree(quotedPath(homePath + "tmp" + os.sep))
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
            else:
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
        else:
            if os.path.isdir(r"\\?\\" + homePath + "tmp" + os.sep):
                # shutil.rmtree(r"\\?\\" + homePath+"tmp" + os.sep, ignore_errors=True)
                # os.mkdir(r"\\?\\" + homePath+"tmp")
                print("There is a TMP folder!")
            else:
                # os.mkdir(r"\\?\\" + homePath+"tmp" + os.sep)
                print("Trying to making dir on Win (no TMP folder)...")
                os.mkdir(r"\\?\\" + homePath + "tmp")

    if opSystem == "linux":
        shutil.copy(PDBPath, quotedPath(homePath + "tmp" + os.sep + "original.pdb"))
    elif opSystem == "darwin":
        shutil.copy(PDBPath, quotedPath(homePath + "tmp" + os.sep + "original.pdb"))
    else:
        print("Precopy")
        shutil.copy(r"\\?\\" + PDBPath, r"\\?\\" + homePath + "tmp" + os.sep + "original.pdb")

    print("Exporting PDB...")
    exportPDB(tag=bpy.data.objects[pE].name.split("#")[0], sPid=setupPDBid)

    # clear zero-user datablocks
    # try:
    #   if True:
    #       for datablock in bpy.data.meshes:
    #           if datablock.users == 0:
    #               bpy.data.meshes.remove(datablock)
    #       for datablock in bpy.data.curves:
    #               if datablock.users == 0:
    #                   bpy.data.curves.remove(datablock)
    #       for datablock in bpy.data.objects:
    #           if datablock.users == 0:
    #               bpy.data.objects.remove(datablock)
    # except Exception as E:
    #   print("Warning: an error occured in setup while clearing zero-user datablocks")
    # print("Setup is complete!")


# export scene to PDB file; if no path is specified, it writes to tmp.pdb
def exportPDB(path=homePath + "tmp" + os.sep + "tmp.pdb", tag=None, verbose=False, sPid=None):
    print("=============== exporting PDB")
    print("Exporting model '%s' to %s" % (tag, path))

    outPath = abspath(path)
    # Questo e' un singolo PDB, di un singolo MODEL (quello corrente), quindi penso si possa procedere in maniera molto semplice...
    # if not tag:
    #   for model in modelContainer:
    #       tag = model
    # model = modelContainer[tag]
    # ordered = sorted(model.keys())
    print("=======outPath = " + str(outPath))
    with open(outPath, "w") as outFile:
        for o in bpy.data.objects:
            try:
                if((o.bb2_pdbID == sPid) and (o.bb2_objectType == "ATOM")):
                    loc = o.location
                    info = o.BBInfo
                    x = "%8.3f" % loc[0]
                    y = "%8.3f" % loc[1]
                    z = "%8.3f" % loc[2]
                    # convert line to pdbstring class
                    line = PDBString(info)
                    # clear location column
                    line = line.set(30, "                         ")  # wtf.
                    # insert new location
                    line = line.set(30, x)
                    line = line.set(38, y)
                    line = line.set(46, z)
                    outFile.write(line + "\n")
            except Exception as E:
                str4 = str(E)   # Do nothing...
        outFile.write("ENDMDL" + "\n")


# Import the surface generated from PyMol
def surface(sPid=0, optName=""):
    res = bpy.context.scene.BBMLPSolventRadius
    quality = "1"

    # 2013-06-28 -Trying to fix pdb ending with 1- or 1+...
    try:
        oPath = homePath + "tmp" + os.sep + "tmp.pdb"
        f = open(oPath, "r")
        lines = f.readlines()
        lineCounter = 0
        for line in lines:
            if(line.startswith("ATOM")):
                line = line.replace("1+", "  ")
                line = line.replace("1-", "  ")
            lines[lineCounter] = line
            lineCounter = lineCounter + 1
        f.close()
        f = open(oPath, "w")
        f.writelines(lines)
        f.close()
    except Exception as E:
        s = "Unable to fix tmp.pdb: " + str(E)
        print(s)

    tmpPathO = homePath + "tmp" + os.sep + "surface.pml"
    tmpPathL = "load " + homePath + "tmp" + os.sep + "tmp.pdb" + "\n"
    tmpPathS = "save " + homePath + "tmp" + os.sep + "tmp.wrl" + "\n"

    # 2013-06-28
    # f.write("cmd.move('z',-cmd.get_view()[11])\n")

    with open(tmpPathO, mode="w") as f:
        f.write("# This file is automatically generated by BioBlender at runtime.\n")
        f.write("# Modifying it manually might not have an effect.\n")
        f.write(tmpPathL)
        f.write('cmd.hide("lines"  ,"tmp")\n')
        f.write('cmd.set("surface_quality"  ,"%s")\n' % quality)
        f.write('cmd.show("surface","tmp")\n')
        f.write('set solvent_radius,' + str(res) + '\n')
        f.write('cmd.reset()\n')
        f.write('cmd.origin(position=[0,0,0])\n')
        f.write('cmd.center("origin")\n')
        f.write(tmpPathS)
        f.write("quit")
    print("Making Surface using PyMOL")

    command = "%s -c -u %s" % (quotedPath(pyMolPath), quotedPath(homePath + "tmp" + os.sep + "surface.pml"))

    command = quotedPath(command)
    launch(exeName=command)

    bpy.ops.import_scene.x3d(filepath=homePath + "tmp" + os.sep + "tmp.wrl", axis_forward="Y", axis_up="Z")

    try:
        ob = bpy.data.objects['ShapeIndexedFaceSet']
        if(optName):
            ob.name = copy.copy(optName)
        else:
            ob.name = "SURFACE"
        ob.bb2_pdbID = copy.copy(sPid)
        ob.bb2_objectType = "SURFACE"
        ob.select = True
        bpy.context.scene.objects.active = ob

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.shade_smooth()

        for oE in bpy.data.objects:
            try:
                if((oE.bb2_pdbID == ob.bb2_pdbID) and (oE.bb2_objectType == "PDBEMPTY")):
                    ob.rotation_euler = copy.copy(oE.rotation_euler)
                    ob.location = copy.copy(oE.location)
            except Exception as E:
                print("An error occured while translating and rotating the surface")
    except Exception as E:
        print("An error occured after importing the WRL ShapeIndexedFaceSet in surface")


def quotedPath(stringaInput):
    if stringaInput == "":
        return stringaInput
    else:
        if((stringaInput.startswith("\"")) and (stringaInput.endswith("\""))):
            return stringaInput
    if opSystem == "linux":
        return stringaInput
    elif opSystem == "darwin":
        return stringaInput
    else:
        stringaOutput = "\"" + stringaInput + "\""
        return stringaOutput


# launch app in separate process, for better performance on multithreaded computers
def launch(exeName, async=False):
    # try to hide window (does not work recursively)
    if opSystem == "linux":
        istartupinfo = None
    elif opSystem == "darwin":
        istartupinfo = None
    else:
        istartupinfo = subprocess.STARTUPINFO()
        istartupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        istartupinfo.wShowWindow = subprocess.SW_HIDE
    if async:
        # if running in async mode, return (the process object) immediately
        return subprocess.Popen(exeName, bufsize=8192, startupinfo=istartupinfo, shell=True)
    else:
        # otherwise wait until process is finished (and return None)
        subprocess.call(exeName, bufsize=8192, startupinfo=istartupinfo, shell=True)
        return None


def select(obj):
    try:
        ob = bpy.data.objects[obj]
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            o.select = False
        ob.select = True
        bpy.context.scene.objects.active = ob
    except:
        return None
    else:
        return ob


def todoAndviewpointsOLD():
    try:
        if "TODO" in bpy.data.objects.keys():
            bpy.ops.object.select_all(action="DESELECT")
            for o in bpy.data.objects:
                o.select = False
            bpy.context.scene.objects.active = None
            bpy.data.objects['TODO'].select = True
            bpy.context.scene.objects.active = bpy.data.objects['TODO']
            bpy.ops.object.delete(use_global=False)
    except:
        print("Warning: TODOs removing not performed properly...")
    try:
        if "Viewpoint" in bpy.data.objects.keys():
            bpy.ops.object.select_all(action="DESELECT")
            for o in bpy.data.objects:
                o.select = False
            bpy.context.scene.objects.active = None
            bpy.data.objects['Viewpoint'].select = True
            bpy.context.scene.objects.active = bpy.data.objects['Viewpoint']
            bpy.ops.object.delete(use_global=False)
    except:
        print("Warning: VIEWPOINTs removing not performed properly...")


def todoAndviewpoints():
    try:
        for ob in bpy.data.objects:
            if (ob.name).startswith("TODO"):
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select = False
                bpy.context.scene.objects.active = None
                ob.select = True
                bpy.context.scene.objects.active = ob
                bpy.ops.object.delete(use_global=False)
    except:
        print("Warning: TODOs removing not performed properly...")
    try:
        for ob in bpy.data.objects:
            if (ob.name).startswith("Viewpoint"):
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select = False
                bpy.context.scene.objects.active = None
                ob.select = True
                bpy.context.scene.objects.active = ob
                bpy.ops.object.delete(use_global=False)
    except:
        print("Warning: VIEWPOINTs removing not performed properly...")
