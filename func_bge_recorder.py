import bpy
import bge


# record physics engine movement to FCurve
def recorder():
    # tread softly, for you tread on two APIs
    from bge import logic
    from bge import render
    from bpy import data
    from bpy import context
    from bpy import ops

    if bpy.context.scene.BBRecordAnimation:
        cont = logic.getCurrentController()
        scene = logic.getCurrentScene()
        own = cont.owner

        # In the original (v0.6v), Timer was a float, but there was no increment on this value,
        # so no steps forwards, just frame 1... now, in Empty Set, there is an always actuator which
        # increments (frame after frame) the value...
        time = own["timer"]
        # record to a new region of the timeline
        offset = 200 + bpy.context.scene.frame_end

        # for all object
        for bgeOBJ in scene.objects:
            try:
                # lookup BPY object from  BGE object name
                bpyOBJ = bpy.data.objects[bgeOBJ.name]
            except Exception as E:
                print("GE_Recorder problem: " + str(E))
                continue

            # ignore non-atom object (lamps, cameras, etc)
            if bpyOBJ.BBInfo:
                bpyOBJ.location = bgeOBJ.position
                bpyOBJ.select = True

        # jump to new position for recording
        bpy.context.scene.frame_current = int(time + offset)
        # insert keyframe
        bpy.ops.anim.keyframe_insert_menu(type="LocRotScale")
        # jump back to the playback position
        bpy.context.scene.frame_current = int(time)

        # end game if done
        if time > bpy.context.scene.frame_end:
            logic.endGame()
        else:
            print("\rRecording protein motion %.0f%%" % (time / bpy.context.scene.frame_end * 100), end="")
