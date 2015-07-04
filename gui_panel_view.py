import copy

import bpy
from bpy import (types, props)
from bpy.path import abspath

from .utils import (
    quotedPath, todoAndviewpoints, select, launch,
    surface, setup, PDBString)

from .app_bootstrap import (
    C, N, O, S, H, CA, P, FE, MG, ZN, CU, NA, K, CL, MN, F
)

from .tables import (scale_vdw, scale_cov)


# depending on view mode, selectively hide certain object based on atom definition
def updateView(residue=None, verbose=False):
    objects = bpy.data.objects

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
            residue_info = PDBString(residue.BBInfo)
            seq = residue_info.get("chainSeq")
            id = residue_info.get("chainID")
            for o in objects:
                if not o.BBInfo:
                    continue

                bbinfo = PDBString(o.BBInfo)
                if((bbinfo.get("chainSeq") == seq) and (bbinfo.get("chainID") == id)):
                    o.select = True
                else:
                    o.select = False

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
                        if not (
                            # these 4 characteristics must be checked first
                            atomName in {N, C} or
                            (atomName == CA and elementName != CA) or
                            (atomName in NucleicAtoms) or
                            (atomName in NucleicAtoms_Filtered)
                        ):
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


def get_selected_pdbids():
    selectedPDBids = set()
    for b in bpy.context.scene.objects:
        if b.select and b.bb2_pdbID:
            if (b.bb2_pdbID not in selectedPDBids):
                t = copy.copy(b.bb2_pdbID)
                selectedPDBids.add(t)
    return selectedPDBids


def make_object_iterator(selectedPDBids):
    for obj in bpy.data.objects:
        if obj.bb2_objectType == 'ATOM':
            if obj.bb2_pdbID in selectedPDBids:
                yield obj


def set_radii(caller, context, bbinfo):
    lookup = scale_vdw if caller.show_type == 'vdw' else scale_cov

    selectedPDBids = get_selected_pdbids()
    objects_of_interest = make_object_iterator(selectedPDBids)

    for obj in objects_of_interest:
        atom = obj.BBInfo[76:78].strip()
        s = lookup[atom][0]
        obj.scale = [s, s, s]


class bb2_view_panel_set_radii(types.Operator):
    bl_idname = "ops.bb2_view_panel_set_radii"
    bl_label = "Set radii"
    bl_description = "Show VdW or Cov radii"

    show_type = props.StringProperty()

    def execute(self, context):
        active = bpy.context.scene.objects.active
        if active and active.BBInfo:
            set_radii(self, context, active.BBInfo)

        return{'FINISHED'}


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


class BB2_PANEL_VIEW(types.Panel):
    bl_label = "BioBlender2 View"
    bl_idname = "BB2_PANEL_VIEW"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    bpy.types.Scene.BBMLPSolventRadius = bpy.props.FloatProperty(
        attr="BBMLPSolventRadius",
        name="Solvent Radius",
        description="Solvent Radius used for Surface Generation",
        default=1.4, min=0.2, max=5, soft_min=0.4, soft_max=4)

    bpy.types.Scene.BBViewFilter = bpy.props.EnumProperty(
        attr="BBViewFilter",
        name="View Filter",
        description="Select a view mode",
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

        l = self.layout
        col = l.column()
        col.separator()
        row = l.row()

        op_name = 'ops.bb2_view_panel_set_radii'
        row.operator(op_name, text='VdW').show_type = 'vdw'
        row.operator(op_name, text='covalent').show_type = 'cov'

    @classmethod
    def poll(cls, context):
        scn = context.scene

        try:
            active = bpy.context.scene.objects.active
            if active.name:
                # do a view update when the selected/active obj changes
                if active.name != scn.bb25_oldActiveObj:
                    # get the ModelRemark of the active model
                    if active.name:
                        scn.bb25_activeModelRemark = active.name.split("#")[0]
                        scn.bb25_currentActiveObj = scn.bb25_activeModelRemark
                    scn.bb25_oldActiveObj = active.name
        except Exception as E:
            s = "Context Poll Failed: " + str(E)
        return (context)
