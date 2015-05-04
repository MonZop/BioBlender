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


def get_homepath():
    return os.path.dirname(__file__) + os.sep


def get_pyPath_pyMolPath(opSystem):
    # Python Path
    if ((opSystem == "linux") or (opSystem == "darwin")):
        pyPath = "python"
    else:
        pyPath = ""
        pyPathSearch = [
            "%systemdrive%\\Python27\\python.exe",
            "%systemdrive%\\Python26\\python.exe",
            "%systemdrive%\\Python25\\python.exe",
            "/usr/bin/python"
        ]

    # Detecting PyMol path
    pyMolPath = ""
    pyMolPathSearch = [
        "%systemdrive%\\Python27\\Scripts\\pymol.cmd",
        "%programfiles%\\PyMOL\\PyMOL\\PymolWin.exe",
        "%programfiles%\\DeLano Scientific\\PyMOL Eval\\PymolWin.exe",
        "%programfiles%\\DeLano Scientific\\PyMOL\\PymolWin.exe",
        "%programfiles(x86)%\\PyMOL\\PyMOL\\PymolWin.exe",
        "%programfiles(x86)%\\DeLano Scientific\\PyMOL Eval\\PymolWin.exe",
        "%programfiles(x86)%\\DeLano Scientific\\PyMOL\\PymolWin.exe",
    ]

    if ((opSystem == "linux") or (opSystem == "darwin")):
        pyMolPath = "pymol"
    else:
        from winreg import ExpandEnvironmentStrings
        # auto detect pymol path
        if not pyMolPath:
            for i in pyMolPathSearch:
                if os.path.exists(ExpandEnvironmentStrings(i)):
                    pyMolPath = ExpandEnvironmentStrings(i)
                    break
        # auto detect python path
        if not pyPath:
            for i in pyPathSearch:
                if os.path.exists(ExpandEnvironmentStrings(i)):
                    pyPath = ExpandEnvironmentStrings(i)
                    break

    return pyPath, pyMolPath
