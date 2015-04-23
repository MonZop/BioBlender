import bpy


def file_append(Path, objName, Directory):
    '''
    permit older versions of Blender to use the append feature
    '''
    print('attempting to append file')
    wm = bpy.ops.wm

    if 'link_append' in dir(wm):
        wm.link_append(filepath=Path, filename=objName, directory=Directory, link=0)
    else:
        wm.append(filepath=Path, filename=objName, directory=Directory)

    print('appended', Path)
