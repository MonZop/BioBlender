import sys
import os

import bpy
from bpy.path import abspath


def file_append(Path, objName, Directory):
    '''
    for the time being this will permit older
    versions of Blender to use the append feature
    '''
    # stored_type = bpy.context.area.type

    try:
        print('appending file')
        # bpy.context.area.type = 'FILE_BROWSER'
        wm = bpy.ops.wm

        if 'link_append' in dir(wm):
            wm.link_append(filepath=Path, filename=objName, directory=Directory, link=False)
        else:
            wm.append(filepath=Path, filename=objName, directory=Directory)

    except Exception as err:
        sys.stderr.write('ERROR: %s\n' % str(err))

    # bpy.context.area.type = stored_type


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


def quotedPath(stringaInput):
    opSystem = bpy.context.scene.bb25_opSystem

    if stringaInput == "":
        return stringaInput
    else:
        if((stringaInput.startswith("\"")) and (stringaInput.endswith("\""))):
            return stringaInput

    if opSystem == "linux":
        return stringaInput
    elif opSystem == "darwin":
        return stringaInput
    else:
        stringaOutput = "\"" + stringaInput + "\""
        return stringaOutput


def setup(verbose=False, clear=True, setupPDBid=0):
    # PDB Path is retrieved from parent EMPTY
    scn = bpy.context.scene
    homePath = scn.bb25_homepath
    opSystem = scn.bb25_opSystem

    pE = None
    for o1 in scn.objects:
        try:
            if(o1.bb2_pdbID == setupPDBid):
                if(o1.bb2_objectType == "PDBEMPTY"):
                    pE = copy.copy(o1.name)
        except Exception as E:
            str3 = str(E)   # Do not print...
    print("pE: " + str(pE))
    PDBPath = abspath(bpy.data.objects[pE].bb2_pdbPath)
    print("pdppath: " + str(PDBPath))

    if clear:
        if opSystem == "linux":
            if os.path.isdir(quotedPath(homePath + "tmp" + os.sep)):
                shutil.rmtree(quotedPath(homePath + "tmp" + os.sep))
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
            else:
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
        elif opSystem == "darwin":
            if os.path.isdir(quotedPath(homePath + "tmp" + os.sep)):
                shutil.rmtree(quotedPath(homePath + "tmp" + os.sep))
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
            else:
                os.mkdir(quotedPath(homePath + "tmp" + os.sep))
        else:
            if os.path.isdir(r"\\?\\" + homePath + "tmp" + os.sep):
                print("There is a TMP folder!")
            else:
                print("Trying to making dir on Win (no TMP folder)...")
                os.mkdir(r"\\?\\" + homePath + "tmp")

    if opSystem in {"linux", "darwin"}:
        shutil.copy(PDBPath, quotedPath(homePath + "tmp" + os.sep + "original.pdb"))
    else:
        print("Precopy")
        shutil.copy(r"\\?\\" + PDBPath, r"\\?\\" + homePath + "tmp" + os.sep + "original.pdb")

    print("Exporting PDB...")
    exportPDB(tag=bpy.data.objects[pE].name.split("#")[0], sPid=setupPDBid)


# export scene to PDB file; if no path is specified, it writes to tmp.pdb
def exportPDB(path=None, tag=None, verbose=False, sPid=None):
    homePath = bpy.context.scene.bb25_homepath

    if not path:
        path = homePath + "tmp" + os.sep + "tmp.pdb"

    print("=============== exporting PDB")
    print("Exporting model '%s' to %s" % (tag, path))

    outPath = abspath(path)
    # Questo e' un singolo PDB, di un singolo MODEL (quello corrente), quindi penso si possa procedere in maniera molto semplice...
    # if not tag:
    #   for model in modelContainer:
    #       tag = model
    # model = modelContainer[tag]
    # ordered = sorted(model.keys())
    print("=======outPath = " + str(outPath))
    with open(outPath, "w") as outFile:
        for o in bpy.data.objects:
            try:
                if((o.bb2_pdbID == sPid) and (o.bb2_objectType == "ATOM")):
                    loc = o.location
                    info = o.BBInfo
                    x = "%8.3f" % loc[0]
                    y = "%8.3f" % loc[1]
                    z = "%8.3f" % loc[2]
                    # convert line to pdbstring class
                    line = PDBString(info)
                    # clear location column
                    line = line.set(30, "                         ")  # wtf.
                    # insert new location
                    line = line.set(30, x)
                    line = line.set(38, y)
                    line = line.set(46, z)
                    outFile.write(line + "\n")
            except Exception as E:
                str4 = str(E)   # Do nothing...
        outFile.write("ENDMDL" + "\n")