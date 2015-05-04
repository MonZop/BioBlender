import os
import bpy


def file_append(Path, objName, Directory):
    '''permit older versions of Blender to use the append feature'''
    print('attempting to append file')

    wm = bpy.ops.wm
    params = dict(filepath=Path, filename=objName, directory=Directory)

    if not ('link_append' in dir(wm)):
        wm.append(*params)
    else:
        params['link'] = None
        wm.link_append(*params)

    print('appended', Path)


def detect_os():
    opSystem = ""
    if os.sys.platform == "linux":
        opSystem = "linux"
    elif os.sys.platform == "darwin":
        opSystem = "darwin"
    else:
        opSystem = "win"

    return opSystem