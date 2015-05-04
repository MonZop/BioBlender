geList = []


class BB2_PHYSICS_SIM_PANEL(types.Panel):
    bl_label = "BioBlender2 Game Engine Sim"
    bl_idname = "BB2_PHYSICS_SIM_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}
    bpy.types.Scene.BBDeltaPhysicRadius = bpy.props.FloatProperty(attr="BBDeltaPhysicRadius", name="Radius", description="Value of radius for collisions in physics engine", default=0.7, min=0.1, max=2, soft_min=.1, soft_max=2)
    bpy.types.Scene.BBRecordAnimation = bpy.props.BoolProperty(attr="BBRecordAnimation", name="RecordAnimation", description="Use the physics engine to calculate protein motion and record the IPO")

    def draw(self, context):
        global activeObj
        global activeobjOld
        scene = context.scene
        layout = self.layout
        r = layout.row()
        r.operator("ops.bb2_operator_ge_refresh")
        r = layout.row()
        split = r.split(percentage=0.50)
        try:
            for m in geList:
                split.label(str(m))
                split.prop(bpy.context.scene.objects[str(m)].game, "physics_type")
                r = layout.row()
                split = r.split(percentage=0.50)
        except Exception as E:
            print("An error occured in SIM_PANEL.draw while drawing geList")
        r = layout.row()
        split = r.split(percentage=0.50)
        split.prop(scene, "BBRecordAnimation")
        split.prop(scene, "BBDeltaPhysicRadius")
        r = layout.row()
        r.operator("ops.bb2_operator_interactive")


class bb2_operator_interactive(types.Operator):
    bl_idname = "ops.bb2_operator_interactive"
    bl_label = "Run in Game Engine"
    bl_description = "Enter Interactive View Mode"

    def invoke(self, context, event):
        for o in bpy.data.objects:
            try:
                if o.bb2_objectType == "SURFACE":
                    o.select = True
                    bpy.context.scene.objects.active = o
                    bpy.ops.object.delete(use_global=False)
            except Exception as E:
                print("No ShapeIndexedFaceSet in scene (or renamed...)")
        try:
            if(bpy.context.scene.BBViewFilter == "4"):
                bpy.context.scene.BBViewFilter = "3"
                updateView()
            geStart()
        except Exception as E:
            s = "Start Game Failed: " + str(E)
            print(s)
            return {'CANCELLED'}
        else:
            return{'FINISHED'}
bpy.utils.register_class(bb2_operator_interactive)


class bb2_operator_ge_refresh(types.Operator):
    bl_idname = "ops.bb2_operator_ge_refresh"
    bl_label = "Refresh GE List"
    bl_description = "Refresh GE List"

    def invoke(self, context, event):
        global geList
        geList = []
        for o in bpy.data.objects:
            try:
                bpy.context.scene.render.engine = 'BLENDER_GAME'
                if(o.bb2_objectType == "PDBEMPTY"):
                    pe = copy.copy(o.name)
                    geList.append(pe)
            except Exception as E:
                str7 = str(E)   # Do nothing...
        return{'FINISHED'}
bpy.utils.register_class(bb2_operator_ge_refresh)


def geStart():
    tmpFPS = bpy.context.scene.render.fps
    bpy.context.scene.render.fps = 1
    bpy.context.scene.game_settings.fps = bpy.context.scene.render.fps
    bpy.context.scene.game_settings.physics_engine = "BULLET"
    bpy.context.scene.game_settings.logic_step_max = 1
    if bpy.context.vertex_paint_object:
        bpy.ops.paint.vertex_paint_toggle()
    # for i, obj in enumerate(bpy.data.objects):
    #    obj.game.radius=bpy.context.scene.BBDeltaPhysicRadius      # Done in createModels! Do not overwrite (Hydrogens problem!)
    # setViewShading("TEXTURED")
    bpy.context.scene.render.engine = 'BLENDER_GAME'
    bpy.context.scene.game_settings.physics_gravity = 0.0
    # Setting dynamic-static type...
    for m in geList:
        tmpEmpty = bpy.data.objects[str(m)]
        tmpID = copy.copy(tmpEmpty.bb2_pdbID)
        for o in bpy.data.objects:
            try:
                if((o.bb2_pdbID == tmpID) and (o.bb2_objectType == 'ATOM')):
                    tmpType = copy.copy(tmpEmpty.game.physics_type)
                    o.game.physics_type = str(tmpType)
            except Exception as E:
                str8 = str(E)   # Do nothing...
        tmpEmpty.game.physics_type = "NO_COLLISION"

    # START!
    bpy.ops.view3d.game_start()
    # setViewShading("SOLID")
    bpy.context.scene.render.fps = tmpFPS
