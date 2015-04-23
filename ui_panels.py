import bpy


class ImportDisposablePDB(bpy.types.Panel):
    bl_label = "BioBlender2.5 DEBUG"
    bl_idname = "BB25_OUTPUT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        l = self.layout
        row = l.row()
        row.label(text='junk here')
