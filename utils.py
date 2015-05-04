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


class PDBString(str):
    print("PDB String")
    # Parses PDB line using column attribute
    # file definition is taken from www.wwpdb.org/documentation/format32/sect9.html
    # The function tries to be smart by striping out whitespaces
    # and converts certain properties to list

    def get(self, property):
        if property == "tag":
            return self[0:6].strip()
        if property == "serial":
            return self[6:11].strip()
        if property == "name":
            return self[12:16].strip()
        if property == "altLoc":
            return self[16:17].strip()
        if property == "aminoName":
            return self[17:20].strip()
        if property == "chainID":
            return self[21:22].strip()
        if property == "chainSeq":
            return self[22:26].strip()
        if property == "iCode":
            return self[26:27].strip()
        if property == "loc":
            x = float(self[29:38])
            y = float(self[38:46])
            z = float(self[46:54])
            # return [float(coord) for coord in self[30:54].split()]
            return [x, y, z]
        # if property == "occupancy": return self[54:60].strip()
        if property == "tempFactor":
            return self[60:66].strip()
        if property == "element":
            return self[76:78].strip()
        if property == "charge":
            return self[78:80].strip()
        if property == "modelID":
            return int(self[6:20].strip())
        # if no match found:
        return None

    # insert data into a 80 column pdb string
    def set(self, loc, prop):
        # insert prop into self[loc], but not changing the length of the string
        newStr = self[0:loc] + str(prop) + self[loc + len(str(prop)):]
        return PDBString(newStr)
