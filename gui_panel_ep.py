class BB2_EP_PANEL(types.Panel):
    bl_label = "BioBlender2 EP Visualization"
    bl_idname = "BB2_EP_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBForceField = bpy.props.EnumProperty(
        attr="BBForceField", name="ForceField",
        description="Select a forcefield type for EP calculation",
        items=(
            ("0", "amber", ""),
            ("1", "charmm", ""),
            ("2", "parse", ""),
            ("3", "tyl06", ""),
            ("4", "peoepb", ""),
            ("5", "swanson", "")),
        default="0")
    bpy.types.Scene.BBEPIonConc = bpy.props.FloatProperty(attr="BBEPIonConc", name="Ion concentration", description="Ion concentration of the solvent", default=0.15, min=0.01, max=1, soft_min=0.01, soft_max=1)
    bpy.types.Scene.BBEPGridStep = bpy.props.FloatProperty(attr="BBEPGridStep", name="Grid Spacing", description="EP Calculation step size (Smaller is better, but slower)", default=1, min=0.01, max=10, soft_min=0.5, soft_max=5)
    bpy.types.Scene.BBEPMinPot = bpy.props.FloatProperty(attr="BBEPMinPot", name="Minimum Potential", description="Minimum Potential on the surface from which start the calculation of the field lines", default=0.0, min=0.0, max=10000, soft_min=0, soft_max=1000)
    bpy.types.Scene.BBEPNumOfLine = bpy.props.FloatProperty(attr="BBEPNumOfLine", name="n EP Lines*eV/Å² ", description="Concentration of lines", default=0.05, min=0.01, max=0.5, soft_min=0.01, soft_max=0.1, precision=3, step=0.01)
    bpy.types.Scene.BBEPParticleDensity = bpy.props.FloatProperty(attr="BBEPParticleDensity", name="Particle Density", description="Particle Density", default=1, min=0.1, max=10.0, soft_min=0.1, soft_max=5.0)

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        split = layout.split()
        c = split.column()
        c.prop(scene, "BBForceField")
        c = c.column(align=True)
        c.label("Options:")
        c.prop(scene, "BBEPIonConc")
        c.prop(scene, "BBEPGridStep")
        c.prop(scene, "BBEPMinPot")
        c.prop(scene, "BBEPNumOfLine")
        c.prop(scene, "BBEPParticleDensity")
        c = split.column()
        c.scale_y = 2
        c.operator("ops.bb2_operator_ep")
        c.operator("ops.bb2_operator_ep_clear")


class bb2_operator_ep(types.Operator):
    bl_idname = "ops.bb2_operator_ep"
    bl_label = "Show EP"
    bl_description = "Calculate and Visualize Electric Potential"

    def invoke(self, context, event):
        try:
            bpy.context.user_preferences.edit.use_global_undo = False
            cleanEPObjs()
            scenewideEP(animation=False)
            bpy.context.scene.BBViewFilter = "4"
            bpy.context.user_preferences.edit.use_global_undo = True
            todoAndviewpoints()
        except Exception as E:
            s = "Generate EP Visualization Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return{'FINISHED'}
bpy.utils.register_class(bb2_operator_ep)


class bb2_operator_ep_clear(types.Operator):
    bl_idname = "ops.bb2_operator_ep_clear"
    bl_label = "Clear EP"
    bl_description = "Clear the EP Visualization"

    def invoke(self, context, event):
        try:
            bpy.context.user_preferences.edit.use_global_undo = False
            cleanEPObjs()
            bpy.context.user_preferences.edit.use_global_undo = True
            todoAndviewpoints()
        except Exception as E:
            s = "Clear EP Visualization Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return{'FINISHED'}
bpy.utils.register_class(bb2_operator_ep_clear)


# delete EP related objects
def cleanEPObjs(deletionList=None):
    global epOBJ
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select = False
    # use deletionList if supplied
    if deletionList:
        for obj in deletionList:
            obj.select = True
    # otherwise delete everything in EPOBJ list
    else:
        for list in epOBJ:
            for obj in list:
                obj.select = True
        epOBJ = []
    # call delete operator
    bpy.ops.object.delete()


def scenewideEP(animation):
    global epOBJ
    scene = bpy.context.scene

    scenewideSetup()    # In BB1, it was a call to "Setup"; now, Setup is 'per id', so we need a scenewide setup function...

    if (not animation):
        print("Generating scenewide surface")
        scenewideSurface()

    if (not animation) or (bpy.context.scene.frame_current % 5 == 1):
        print("Generating EP Curves")
        tmpPathOpen = homePath + "tmp" + os.sep + "scenewide.pdb"  # former tmp.pdb

        with open(tmpPathOpen, "r") as file:
            for line in file:
                line = line.replace("\n", "")
                line = line.replace("\r", "")
                line = PDBString(line)
                tag = line.get("tag")

                # if tag is ATOM, load column data
                if(tag == "ATOM" or tag == "HETATM"):
                    # check for element type
                    if line.get("element") == H:
                        extraCommand = "--assign-only"
                        break

        # select the forcefield
        forcefield = bpy.context.scene.BBForceField
        if forcefield == "0":
            method = "amber"
        elif forcefield == "1":
            method = "charmm"
        elif forcefield == "2":
            method = "parse"
        elif forcefield == "3":
            method = "tyl06"
        elif forcefield == "4":
            method = "peoepb"
        elif forcefield == "5":
            method = "swanson"

        print("Running PDB2PQR")
        if opSystem == "linux":
            os.chdir(quotedPath(homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep))
        elif opSystem == "darwin":
            os.chdir(quotedPath(homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep))
        else:
            os.chdir(r"\\?\\" + homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep)
        tmpPathPar1 = "python"
        tmpPathPar2 = homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep + "pdb2pqr.py"
        tmpPathPar3 = homePath + "tmp" + os.sep + "scenewide.pqr"
        tmpPathPar4 = homePath + "tmp" + os.sep + "scenewide.pdb"
        if opSystem == "linux":
            command = "%s %s --apbs-input --ff=%s %s %s" % (tmpPathPar1, tmpPathPar2, method, tmpPathPar4, tmpPathPar3)
        elif opSystem == "darwin":
            command = "%s %s --apbs-input --ff=%s %s %s" % (tmpPathPar1, tmpPathPar2, method, tmpPathPar4, tmpPathPar3)
        else:
            command = "%s %s --apbs-input --ff=%s %s %s" % (quotedPath(tmpPathPar1), quotedPath(tmpPathPar2), method, quotedPath(tmpPathPar4), quotedPath(tmpPathPar3))
        launch(exeName=command)

        print("Running inputgen.py")
        tmp1PathPar1 = "python"
        tmp1PathPar2 = homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep + "src" + os.sep + "inputgen.py"
        tmp1PathPar3 = homePath + "tmp" + os.sep + "scenewide.pqr"
        if opSystem == "linux":
            command = "%s %s --istrng=%f --method=auto --space=%f %s" % (tmp1PathPar1, tmp1PathPar2, bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, tmp1PathPar3)
        elif opSystem == "darwin":
            command = "%s %s --istrng=%f --method=auto --space=%f %s" % (tmp1PathPar1, tmp1PathPar2, bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, tmp1PathPar3)
        else:
            command = "%s %s --istrng=%f --method=auto --space=%f %s" % (quotedPath(tmp1PathPar1), quotedPath(tmp1PathPar2), bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, quotedPath(tmp1PathPar3))
        launch(exeName=command)

        print("Running APBS")
        try:
            if opSystem == "linux":
                shutil.copy(quotedPath(homePath + "bin" + os.sep + "apbs-1.2.1" + os.sep + "apbs.exe"), quotedPath(homePath + "tmp" + os.sep + "apbs.exe"))
            elif opSystem == "darwin":
                shutil.copy(quotedPath(homePath + "bin" + os.sep + "apbs-1.2.1" + os.sep + "darwin_apbs"), quotedPath(homePath + "tmp" + os.sep + "darwin_apbs"))
            else:
                shutil.copy(r"\\?\\" + homePath + "bin" + os.sep + "apbs-1.2.1" + os.sep + "apbs.exe", r"\\?\\" + homePath + "tmp" + os.sep + "apbs.exe")
        except Exception as E:
            s = "APBS COPY failed: " + str(E)
            print(s)
        if opSystem == "linux":
            oPath = homePath + "tmp" + os.sep + "scenewide.in"
            f = open(oPath, "r")
            lines = f.readlines()
            f.close()
            lines[1] = "    mol pqr " + quotedPath(homePath + "tmp" + os.sep + "scenewide.pqr") + "\n"
            f = open(oPath, "w")
            f.writelines(lines)
            f.close()
            command = "chmod 755 %s" % (quotedPath(homePath + "tmp" + os.sep + "apbs.exe"))
            command = quotedPath(command)
            launch(exeName=command)
            command = homePath + "tmp" + os.sep + "apbs.exe" + " " + homePath + "tmp" + os.sep + "scenewide.in"
        elif opSystem == "darwin":
            oPath = homePath + "tmp" + os.sep + "scenewide.in"
            f = open(oPath, "r")
            lines = f.readlines()
            f.close()
            lines[1] = "    mol pqr " + quotedPath(homePath + "tmp" + os.sep + "scenewide.pqr") + "\n"
            f = open(oPath, "w")
            f.writelines(lines)
            f.close()
            command = "chmod 755 %s" % (quotedPath(homePath + "tmp" + os.sep + "darwin_apbs"))
            command = quotedPath(command)
            launch(exeName=command)
            command = homePath + "tmp" + os.sep + "darwin_apbs" + " " + homePath + "tmp" + os.sep + "scenewide.in"
        else:
            oPath = homePath + "tmp" + os.sep + "scenewide.in"
            f = open(oPath, "r")
            lines = f.readlines()
            f.close()
            lines[1] = "    mol pqr " + quotedPath(homePath + "tmp" + os.sep + "scenewide.pqr") + "\n"
            f = open(oPath, "w")
            f.writelines(lines)
            f.close()
            command = quotedPath(homePath + "tmp" + os.sep + "apbs.exe") + " " + quotedPath(homePath + "tmp" + os.sep + "scenewide.in")
        p = launch(exeName=command, async=True)
        print("APBS Ok")

        # sync
        wait(p)

        # write pot dx pot problems: writes the .dx file in user home path...
        print("============ POT DX POT COPY ================")
        envBoolean = False
        try:
            if opSystem == "linux":
                tmpP = quotedPath(homePath + "tmp" + os.sep + "pot.dx")
                if os.path.isfile(tmpP):
                    envBoolean = True
                    print("pot.dx in current directory; won't search in HOME or VIRTUALSTORE folders...")
            elif opSystem == "darwin":
                tmpP = quotedPath(homePath + "tmp" + os.sep + "pot.dx")
                if os.path.isfile(tmpP):
                    envBoolean = True
                    print("pot.dx in current directory; won't search in HOME or VIRTUALSTORE folders...")
        except Exception as E:
            s = "pot.dx output rewrite failed in tmp.in, will search in some folders...: " + str(E)
            print(s)
        if not envBoolean:
            if opSystem == "linux":
                print("user home: ", os.path.expanduser("~"))
                try:
                    print("BB stays here: ")
                    homeutente = os.path.expanduser("~")
                    shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/pot.dx"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/pot.dx"))
                    shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/io.mc"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/io.mc"))
                except Exception as E:
                    s = "pot.dx not found in HOME: " + str(E)
                    print(s)
            elif opSystem == "darwin":
                print("user home: ", os.path.expanduser("~"))
                try:
                    print("BB stays here: ")
                    homeutente = os.path.expanduser("~")
                    shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/pot.dx"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/pot.dx"))
                    shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/io.mc"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/io.mc"))
                except Exception as E:
                    s = "pot.dx not found in HOME: " + str(E)
                    print(s)
            else:
                try:
                    envHome = str(os.environ['USERPROFILE'])
                    print("envHome: " + envHome)
                    shutil.move(r"\\?\\" + envHome + os.sep + "pot.dx", r"\\?\\" + homePath + "tmp" + os.sep + "pot.dx")
                    shutil.move(r"\\?\\" + envHome + os.sep + "io.mc", r"\\?\\" + homePath + "tmp" + os.sep + "io.mc")
                    envBoolean = True
                except Exception as E:
                    s = "No pot.dx in HOME: " + str(E)
                    print(s)
                if not envBoolean:
                    print("Win problem; will search in Windows...")
                    try:
                        envHome = "C:" + os.sep + "Windows"
                        print("envHome: " + envHome)
                        shutil.move(envHome + os.sep + "pot.dx", homePath + "tmp" + os.sep + "pot.dx")
                        shutil.move(envHome + os.sep + "io.mc", homePath + "tmp" + os.sep + "io.mc")
                        envBoolean = True
                    except Exception as E:
                        s = "Windows home failed too; no pot.dx, sorry: " + str(E)
                        print(s)
                if not envBoolean:
                    print("Win problem; will search in AppData - Local - VirtualStore...")
                    try:
                        envHome = str(os.environ['USERPROFILE']) + os.sep + "AppData" + os.sep + "Local" + os.sep + "VirtualStore"
                        print("envHome: " + envHome)
                        shutil.move(envHome + os.sep + "pot.dx", homePath + "tmp" + os.sep + "pot.dx")
                        shutil.move(envHome + os.sep + "io.mc", homePath + "tmp" + os.sep + "io.mc")
                        envBoolean = True
                    except Exception as E:
                        s = "VirtualStore failed too; no pot.dx, sorry: " + str(E)
                        print(s)
                if not envBoolean:
                    print("Win problem; will search in AppData - Local - VirtualStore - Windows...")
                    try:
                        envHome = str(os.environ['USERPROFILE']) + os.sep + "AppData" + os.sep + "Local" + os.sep + "VirtualStore" + os.sep + "Windows"
                        print("envHome: " + envHome)
                        shutil.move(envHome + os.sep + "pot.dx", homePath + "tmp" + os.sep + "pot.dx")
                        shutil.move(envHome + os.sep + "io.mc", homePath + "tmp" + os.sep + "io.mc")
                        envBoolean = True
                    except Exception as E:
                        s = "VirtualStore - Windows failed too; no pot.dx, sorry: " + str(E)
                        print(s)
                        print("=========== SORRY: CANNOT FIND POT.DX ============")
        print("Saving obj")
        exportOBJ(homePath + "tmp" + os.sep + "scenewide")

        if len(epOBJ) >= maxCurveSet:
            # delete the oldest curve-sets out of the list.
            epOBJ.reverse()
            deletionList = epOBJ.pop()
            cleanEPObjs(deletionList)
            epOBJ.reverse()

        print("Running Scivis")
        if opSystem == "linux":
            command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "scivis" + os.sep + "SCIVIS.exe"))
            command = quotedPath(command)
            launch(exeName=command)
            command = "%s %s %s %s %f %f %f %f %f" % (homePath + "bin" + os.sep + "scivis" + os.sep + "SCIVIS.exe", homePath + "tmp" + os.sep + "scenewide.obj", homePath + "tmp" + os.sep + "pot.dx", homePath + "tmp" + os.sep + "tmp.txt", bpy.context.scene.BBEPNumOfLine / 10, bpy.context.scene.BBEPMinPot, 45, 1, 3)
        elif opSystem == "darwin":
            command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "scivis" + os.sep + "darwin_SCIVIS"))
            command = quotedPath(command)
            launch(exeName=command)
            command = "%s %s %s %s %f %f %f %f %f" % (homePath + "bin" + os.sep + "scivis" + os.sep + "darwin_SCIVIS", homePath + "tmp" + os.sep + "scenewide.obj", homePath + "tmp" + os.sep + "pot.dx", homePath + "tmp" + os.sep + "tmp.txt", bpy.context.scene.BBEPNumOfLine / 10, bpy.context.scene.BBEPMinPot, 45, 1, 3)
        else:
            command = "%s %s %s %s %f %f %f %f %f" % (quotedPath(homePath + "bin" + os.sep + "scivis" + os.sep + "SCIVIS.exe"), quotedPath(homePath + "tmp" + os.sep + "scenewide.obj"), quotedPath(homePath + "tmp" + os.sep + "pot.dx"), quotedPath(homePath + "tmp" + os.sep + "tmp.txt"), bpy.context.scene.BBEPNumOfLine / 10, bpy.context.scene.BBEPMinPot, 45, 1, 3)
        launch(exeName=command)

        print("Importing data into Blender")

        list = importEP(homePath + "tmp" + os.sep + "tmp.txt")

        epOBJ.append(list)

        ob = select("Emitter")

        # Positioning and rotating the Emitter
        try:
            if(False):
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select = False
                bpy.context.scene.objects.active = None
                bpy.data.objects['SCENEWIDESURFACE'].select = True
                bpy.context.scene.objects.active = bpy.data.objects['SCENEWIDESURFACE']
                tmpRot = copy.copy(oE.rotation_euler)
                tmpLoc = copy.copy(oE.location)
                ob = select("Emitter")
                ob.rotation_euler = tmpRot
                ob.location = tmpLoc
            else:
                ob.location = [0, 0, 0]
        except Exception as E:
            print("An error occured while positioning and rotating the Emitter: " + str(E))

        print("Current frame before if animation: " + str(bpy.context.scene.frame_current))
        if animation:
            ob.particle_systems[0].settings.frame_start = bpy.context.scene.frame_current
            ob.particle_systems[0].settings.frame_end = bpy.context.scene.frame_current
            ob.particle_systems[0].settings.frame_end = 20
            ob.particle_systems[0].settings.count = len(ob.data.vertices)
            print("Animation")
        else:
            if not bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()

        # Destroy the surface
        try:
            if "SCENEWIDESURFACE" in bpy.data.objects.keys():
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select = False
                bpy.context.scene.objects.active = None
                bpy.data.objects['SCENEWIDESURFACE'].select = True
                bpy.context.scene.objects.active = bpy.data.objects['SCENEWIDESURFACE']
                bpy.ops.object.delete(use_global=False)
        except Exception as E:
            print("Warning: SCENEWIDESURFACE removing not performed properly: " + str(E))


# import curve description text into Blender
def importEP(path):
    global curveCount
    global objList

    curveCount = 0
    scene = bpy.context.scene
    pts = []
    objList = []
    # read the file once to generate curves
    with open(path, "r") as file:
        for file_line in file:
            line = file_line.split()
            if line[0] == "n":
                if curveCount != 0:
                    # for every n encountered creates a new curve
                    cu = bpy.data.curves.new("Curve%3d" % curveCount, "CURVE")
                    ob = bpy.data.objects.new("CurveObj%3d" % curveCount, cu)
                    bpy.context.scene.objects.link(ob)
                    bpy.context.scene.objects.active = ob
                    # set all the properties of the curve
                    spline = cu.splines.new("NURBS")
                    cu.dimensions = "3D"
                    cu.use_path = True
                    cu.resolution_u = 1
                    spline.points.add(len(pts) // 4 - 1)
                    spline.points.foreach_set('co', pts)
                    spline.use_endpoint_u = True
                    ob.field.type = "GUIDE"
                    ob.field.use_max_distance = True
                    ob.field.distance_max = 0.05
                    # objList keeps a list of all EP related objects for easy deletion
                    objList.append(ob)
                    pts = []
                curveCount += 1
            elif line[0] == "v":
                pts.append(float(line[1]))
                pts.append(float(line[2]))
                pts.append(float(line[3]))
                pts.append(1)

    # rename current emitter
    if select("Emitter"):
        for list in epOBJ:
            for obj in list:
                if obj.name == "Emitter":
                    obj.name = "Emitter%d" % curveCount

    # read the file again to generate the particle emitter object
    with open(path, "r") as file:
        verts = []
        for line in file:
            # read the first line after each 'n' identifier
            if "n" in line:
                next = file.readline()
                coord = next.split()
                verts.append([float(i) for i in coord[1:]])

        # make mesh
        mesh = bpy.data.meshes.new("Emitter")
        mesh.from_pydata(verts[:-1], [], [])        # [:-1] to fix the off by one error somewhere...

        # append emitter object with particle sytem into scene, and assign mesh to the object
        # this is a workaround to avoid having to add a particle system from the scene context (impossible)
        Directory = homePath + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep
        Path = os.sep + os.sep + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep + "Emitter"
        objName = "Emitter"

        file_append(Path, objName, Directory)

        ob = bpy.data.objects["Emitter"]
        print("EMITTER in ob: " + ob.name)
        ob.data = mesh

        # 2013-06-27 - Particle Settings End Frame
        # try:
        #   bpy.data.particles['ParticleSettings'].frame_end = bpy.context.scene.frame_end
        #    #bpy.data.particles['ParticleSettings'].frame_end = bpy.context.scene.frame_end
        #    #lifetime
        # except Exception as E:
        #   s = "Emitter Particle System frame_end NOT SET: " + str(E)
        #   print(s)

        # add material if does not exist
        if not ob.data.materials:
            mat = bpy.data.materials["Particles"]
            ob.data.materials.append(mat)

        # change particle density according to curve count
        ob.particle_systems[0].settings.count = int(bpy.context.scene.BBEPNumOfLine * 50000 * bpy.context.scene.BBEPParticleDensity)
        # reset location
        # ob.location = [0,0,0]
        # add object to deletion list
        objList.append(ob)
    return objList


# Convert WRL to OBJ for scivis.exe
def exportOBJ(path):
    vertexData = []     # list of list[3] (wrl vertices data)
    # read wrl file
    with open(path + ".wrl") as wrl:
        found = False
        for line in wrl:
            # skip to coord section of the file
            if not found:
                if "coord" in line:
                    wrl.readline()
                    found = True
            # when in the coord section of the file
            else:
                if "]" not in line:
                    # convert vertexData from string to a list of float
                    entry = line[:-2].split()
                    entryFloat = [float(coord) for coord in entry]
                    vertexData.append(entryFloat)
                else:
                    # end document processing
                    break

    # write obj file: vertex data
    with open(path + ".obj", mode="w") as obj:
        for entry in vertexData:
            out = "v %f %f %f\n" % (entry[0], entry[1], entry[2])
            obj.write(out)

        # face data
        i = 0
        while (i < len(vertexData)):
            out = "f %d/%d %d/%d %d/%d\n" % (i + 1, i + 1, i + 2, i + 2, i + 3, i + 3)
            obj.write(out)
            i = i + 3


def scenewideSetup():
    path = homePath + "tmp" + os.sep + "scenewide.pdb"
    # Actually, this is a custom "exportPDB" function, without instructions which were present in original "setup" function...
    print("=============== exporting PDB")
    print("Exporting scene to: " + str(path))

    outPath = abspath(path)
    print("=======outPath = " + str(outPath))
    i = 1
    with open(outPath, "w") as outFile:
        for o in bpy.data.objects:
            try:
                if(o.bb2_objectType == "ATOM"):
                    loc = trueSphereOrigin(o)
                    info = o.BBInfo
                    x = "%8.3f" % loc[0]
                    y = "%8.3f" % loc[1]
                    z = "%8.3f" % loc[2]
                    # convert line to pdbstring class
                    line = PDBString(info)
                    # Recalculate ATOM id number...
                    line = line.set(1, "           ")
                    if (i < 10):
                        tmpString = "ATOM      " + str(i)
                    elif(i > 9 and i < 100):
                        tmpString = "ATOM     " + str(i)
                    elif(i > 99 and i < 1000):
                        tmpString = "ATOM    " + str(i)
                    else:
                        tmpString = "ATOM   " + str(i)
                    line = line.set(0, tmpString)
                    # clear location column
                    line = line.set(30, "                         ")
                    # insert new location
                    line = line.set(30, x)
                    line = line.set(38, y)
                    line = line.set(46, z)
                    outFile.write(line + "\n")
                    i = i + 1
            except Exception as E:
                str4 = str(E)
                print("An error occured in sceneWideSetup: " + str4)
        outFile.write("ENDMDL" + "\n")
    print("scenewideSetup is complete!")


# Import the surface generated from PyMol
def scenewideSurface():
    res = bpy.context.scene.BBMLPSolventRadius
    quality = "1"

    # 2013-06-28 -Trying to fix pdb ending with 1- or 1+...
    try:
        oPath = homePath + "tmp" + os.sep + "scenewide.pdb"
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
        s = "Unable to fix scenewide.pdb: " + str(E)
        print(s)

    tmpPathO = homePath + "tmp" + os.sep + "surface.pml"
    tmpPathL = "load " + homePath + "tmp" + os.sep + "scenewide.pdb" + "\n"
    tmpPathS = "save " + homePath + "tmp" + os.sep + "scenewide.wrl" + "\n"

    # 2013-06-28
    # f.write("cmd.move('z',-cmd.get_view()[11])\n")
    with open(tmpPathO, mode="w") as f:
        f.write("# This file is automatically generated by BioBlender at runtime.\n")
        f.write("# Modifying it manually might not have an effect.\n")
        f.write(tmpPathL)
        f.write('cmd.hide("lines"  ,"scenewide")\n')
        f.write('cmd.set("surface_quality"  ,"%s")\n' % quality)
        f.write('cmd.show("surface","scenewide")\n')
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

    bpy.ops.import_scene.x3d(filepath=homePath + "tmp" + os.sep + "scenewide.wrl", axis_forward="Y", axis_up="Z")

    try:
        ob = bpy.data.objects['ShapeIndexedFaceSet']
        ob.name = "SCENEWIDESURFACE"
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
