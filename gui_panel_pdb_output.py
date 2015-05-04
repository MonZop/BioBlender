class BB2_PDB_OUTPUT_PANEL(types.Panel):
    bl_label = "BioBlender2 PDB Output"
    bl_idname = "BB2_PDB_OUTPUT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBPDBExportStep = bpy.props.IntProperty(attr="BBPDBExportStep", name="PDB Export Step", description="PDB Export step", default=1, min=1, max=100, soft_min=1, soft_max=50)

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        r = layout.row()
        r.prop(bpy.context.scene.render, "filepath", text="")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_start")
        r = layout.row()
        r.prop(bpy.context.scene, "frame_end")
        r = layout.row()
        r.prop(bpy.context.scene, "BBPDBExportStep")
        r = layout.row()
        r.operator("ops.bb2_operator_export_pdb")
        r = layout.row()
        num = ((bpy.context.scene.frame_end - bpy.context.scene.frame_start) / bpy.context.scene.BBPDBExportStep) + 1
        r.label("A total of %d frames will be exported." % num)


class bb2_operator_export_pdb(types.Operator):
    bl_idname = "ops.bb2_operator_export_pdb"
    bl_label = "Export PDB"
    bl_description = "Export current view to PDB"

    def invoke(self, context, event):
        try:
            if((bpy.context.scene.objects.active.bb2_objectType == "ATOM") or (bpy.context.scene.objects.active.bb2_objectType == "PDBEMPTY")):
                bpy.context.user_preferences.edit.use_global_undo = False
                selectedPDBidS = []
                for b in bpy.context.scene.objects:
                    if b.select:
                        try:
                            if((b.bb2_pdbID not in selectedPDBidS) and ((b.bb2_objectType == "ATOM") or (b.bb2_objectType == "PDBEMPTY"))):
                                t = copy.copy(b.bb2_pdbID)
                                selectedPDBidS.append(t)
                        except Exception as E:
                            str1 = str(E)   # Do not print...
                context.user_preferences.edit.use_global_undo = False
                for id in selectedPDBidS:
                    tID = copy.copy(id)
                    for o in bpy.data.objects:
                        try:
                            if((o.bb2_pdbID == tID) and (o.bb2_objectType == "PDBEMPTY")):
                                tmpName = copy.copy(str(o.name))
                                exportPDBSequence(tmpName, tID)
                        except Exception as E:
                            print("PDB seq error: " + str(E))
                bpy.context.user_preferences.edit.use_global_undo = True
            else:
                print("No PDB Empty or Atom selected")
        except Exception as E:
            s = "Export PDB Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return{'FINISHED'}


def trueSphereOrigin(object):
    tmpSphere = bpy.data.objects[object.name]
    coord = [(object.matrix_world[0])[3], (object.matrix_world[1])[3], (object.matrix_world[2])[3]]
    return coord


def exportPDBSequence(curPDBpath="", tID=0):
    step = bpy.context.scene.BBPDBExportStep
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    bpy.context.scene.render.engine = 'BLENDER_RENDER'

    a = time.time()

    cu = bpy.context.scene.render.filepath + "_" + ((curPDBpath.split("."))[0]) + ".pdb"
    pdbPath = abspath(cu)

    print("=======outPath = " + str(pdbPath))
    with open(pdbPath, "w") as outFile:
        # outFile.write("NUMMDL    " + str(int(((bpy.context.scene.frame_end - bpy.context.scene.frame_start)/bpy.context.scene.BBPDBExportStep)+1)) + "\n")
        i = start
        while i <= end:
            bpy.context.scene.frame_set(i)
            # PRINT MODEL n
            if(i < 10):
                currentModelString = "MODEL " + "       " + str(i)
            elif(i > 9 and i < 100):
                currentModelString = "MODEL " + "      " + str(i)
            elif(i > 99 and i < 1000):
                currentModelString = "MODEL " + "     " + str(i)
            else:
                currentModelString = "MODEL " + "    " + str(i)
            outFile.write(currentModelString + "\n")
            for o in bpy.data.objects:
                try:
                    if((o.bb2_pdbID == tID) and (o.bb2_objectType == "ATOM")):
                        loc = trueSphereOrigin(o)
                        info = o.BBInfo
                        x = "%8.3f" % loc[0]
                        y = "%8.3f" % loc[1]
                        z = "%8.3f" % loc[2]
                        # convert line to pdbstring class
                        line = PDBString(info)
                        # clear location column
                        line = line.set(30, "                         ")
                        # insert new location
                        line = line.set(30, x)
                        line = line.set(38, y)
                        line = line.set(46, z)
                        outFile.write(line + "\n")
                except Exception as E:
                    print("An error occured while exporting PDB sequence: " + str(E))
            outFile.write("ENDMDL" + "\n")
            i += step
        outFile.write("ENDMDL" + "\n")
    # clean up
    bpy.context.scene.frame_set(start)
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    print(time.time() - a)
