import bpy


def file_append(Path, objName, Directory):
    '''
    this will permit older versions of Blender to use the append feature
    '''

    print('appending file')
    wm = bpy.ops.wm
    # if hasattr(wm, 'link_append'):
    if 'link_append' in dir(wm):
        wm.link_append(filepath=Path, filename=objName, directory=Directory, link=False)
    else:
        wm.append(filepath=Path, filename=objName, directory=Directory)
    print('appended', Path)
