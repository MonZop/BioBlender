import sys
import os
import subprocess
import copy
import shutil
import time
import math
from math import fabs

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
            return [x, y, z]  # if property == "occupancy": return self[54:60].strip()
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

    print('type_check setupPDBid. (should be string):', setupPDBid.__class__)

    pE = None
    for o1 in scn.objects:
        try:
            if(o1.bb2_pdbID == setupPDBid):
                if(o1.bb2_objectType == "PDBEMPTY"):
                    pE = copy.copy(o1.name)
        except Exception as E:
            str3 = str(E)   # Do not print...
            print(str3)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

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
    homePath = str(bpy.context.scene.bb25_homepath)

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


def todoAndviewpoints():
    try:
        for ob in bpy.data.objects:
            if (ob.name).startswith("TODO"):
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select = False
                bpy.context.scene.objects.active = None
                ob.select = True
                bpy.context.scene.objects.active = ob
                bpy.ops.object.delete(use_global=False)
    except:
        print("Warning: TODOs removing not performed properly...")
    try:
        for ob in bpy.data.objects:
            if (ob.name).startswith("Viewpoint"):
                bpy.ops.object.select_all(action="DESELECT")
                for o in bpy.data.objects:
                    o.select = False
                bpy.context.scene.objects.active = None
                ob.select = True
                bpy.context.scene.objects.active = ob
                bpy.ops.object.delete(use_global=False)
    except:
        print("Warning: VIEWPOINTs removing not performed properly...")


def select(obj):
    try:
        ob = bpy.data.objects[obj]
        bpy.ops.object.select_all(action="DESELECT")
        for o in bpy.data.objects:
            o.select = False
        ob.select = True
        bpy.context.scene.objects.active = ob
    except:
        return None
    else:
        return ob


# launch app in separate process, for better performance on multithreaded computers
def launch(exeName, async=False):
    # try to hide window (does not work recursively)
    opSystem = detect_os()
    if opSystem == "linux":
        istartupinfo = None
    elif opSystem == "darwin":
        istartupinfo = None
    else:
        istartupinfo = subprocess.STARTUPINFO()
        istartupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        istartupinfo.wShowWindow = subprocess.SW_HIDE
    if async:
        # if running in async mode, return (the process object) immediately
        return subprocess.Popen(exeName, bufsize=8192, startupinfo=istartupinfo, shell=True)
    else:
        # otherwise wait until process is finished (and return None)
        subprocess.call(exeName, bufsize=8192, startupinfo=istartupinfo, shell=True)
        return None


# Wait until process finishes
def wait(process):
    while process.poll() == None:
        time.sleep(0.1)
        # needed if io mode is set to subprocess.PIPE to avoid deadlock
        # process.communicate()


# Import the surface generated from PyMol
def surface(sPid=0, optName=""):
    scn = bpy.context.scene
    res = scn.BBMLPSolventRadius
    homePath = scn.bb25_homepath
    pyMolPath = scn.bb25_pyMolPath

    # could offer user choice...and definitely provide higher for animation purposes.
    quality = "1"

    # 2013-06-28 -Trying to fix pdb ending with 1- or 1+...
    try:
        oPath = homePath + "tmp" + os.sep + "tmp.pdb"
        f = open(oPath, "r")
        lines = f.readlines()
        lineCounter = 0
        for line in lines:
            if(line.startswith("ATOM")):
                line = line.replace("1+", "  ")
                line = line.replace("1-", "  ")
            lines[lineCounter] = line
            lineCounter = lineCounter + 1
        f.close()
        f = open(oPath, "w")
        f.writelines(lines)
        f.close()
    except Exception as E:
        s = "Unable to fix tmp.pdb: " + str(E)
        print(s)

    tmpPathO = homePath + "tmp" + os.sep + "surface.pml"
    tmpPathL = "load " + homePath + "tmp" + os.sep + "tmp.pdb" + "\n"
    tmpPathS = "save " + homePath + "tmp" + os.sep + "tmp.wrl" + "\n"

    # 2013-06-28
    # f.write("cmd.move('z',-cmd.get_view()[11])\n")

    with open(tmpPathO, mode="w") as f:
        f.write("# This file is automatically generated by BioBlender at runtime.\n")
        f.write("# Modifying it manually might not have an effect.\n")
        f.write(tmpPathL)
        f.write('cmd.hide("lines"  ,"tmp")\n')
        f.write('cmd.set("surface_quality"  ,"%s")\n' % quality)
        f.write('cmd.show("surface","tmp")\n')
        f.write('set solvent_radius,' + str(res) + '\n')
        f.write('cmd.reset()\n')
        f.write('cmd.origin(position=[0,0,0])\n')
        f.write('cmd.center("origin")\n')
        f.write(tmpPathS)
        f.write("quit")
    print("Making Surface using PyMOL")

    command = "%s -c -u %s" % (quotedPath(pyMolPath), quotedPath(homePath + "tmp" + os.sep + "surface.pml"))

    command = quotedPath(command)
    launch(exeName=command)

    bpy.ops.import_scene.x3d(filepath=homePath + "tmp" + os.sep + "tmp.wrl", axis_forward="Y", axis_up="Z")

    try:
        ob = bpy.data.objects['ShapeIndexedFaceSet']
        if(optName):
            ob.name = copy.copy(optName)
        else:
            ob.name = "SURFACE"
        ob.bb2_pdbID = copy.copy(sPid)
        ob.bb2_objectType = "SURFACE"
        ob.select = True
        bpy.context.scene.objects.active = ob

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.shade_smooth()

        for oE in bpy.data.objects:
            try:
                if((oE.bb2_pdbID == ob.bb2_pdbID) and (oE.bb2_objectType == "PDBEMPTY")):
                    ob.rotation_euler = copy.copy(oE.rotation_euler)
                    ob.location = copy.copy(oE.location)
            except Exception as E:
                print("An error occured while translating and rotating the surface")
    except Exception as E:
        print("An error occured after importing the WRL ShapeIndexedFaceSet in surface")


def getVar(rawID, local_vars=[]):
    dimension, delta, origin, dxData, dxCache, ob = local_vars

    try:
        val = dxCache[rawID]
    except:

        v = ob.data.vertices[rawID].co
        dimx = dimension[0]
        dimy = dimension[1]
        dimz = dimension[2]
        deltax = delta[0]
        deltay = delta[1]
        deltaz = delta[2]
        cellx = int((v[0] - origin[0]) / deltax)
        celly = int((v[1] - origin[1]) / deltay)
        cellz = int((v[2] - origin[2]) / deltaz)

        mmm = dxData[cellz + ((celly) * dimz) + ((cellx) * dimz * dimy)]
        pmm = dxData[cellz + ((celly) * dimz) + ((cellx + 1) * dimz * dimy)]
        mpm = dxData[cellz + ((celly + 1) * dimz) + ((cellx) * dimz * dimy)]
        mmp = dxData[cellz + 1 + ((celly) * dimz) + ((cellx) * dimz * dimy)]
        ppm = dxData[cellz + ((celly + 1) * dimz) + ((cellx + 1) * dimz * dimy)]
        mpp = dxData[cellz + 1 + ((celly + 1) * dimz) + ((cellx) * dimz * dimy)]
        pmp = dxData[cellz + 1 + ((celly) * dimz) + ((cellx + 1) * dimz * dimy)]
        ppp = dxData[cellz + 1 + ((celly + 1) * dimz) + ((cellx + 1) * dimz * dimy)]

        wxp = 1.0 - (fabs(v[0] - (origin[0] + (deltax * (cellx + 1))))) / deltax
        wxm = 1.0 - (fabs(v[0] - (origin[0] + (deltax * (cellx))))) / deltax
        wyp = 1.0 - (fabs(v[1] - (origin[1] + (deltay * (celly + 1))))) / deltay
        wym = 1.0 - (fabs(v[1] - (origin[1] + (deltay * (celly))))) / deltay
        wzp = 1.0 - (fabs(v[2] - (origin[2] + (deltaz * (cellz + 1))))) / deltaz
        wzm = 1.0 - (fabs(v[2] - (origin[2] + (deltaz * (cellz))))) / deltaz

        onz_xmym = (wzp * mmp) + (wzm * mmm)
        onz_xpym = (wzp * pmp) + (wzm * pmm)
        onz_xmyp = (wzp * mpp) + (wzm * mpm)
        onz_xpyp = (wzp * ppp) + (wzm * ppm)
        onx_yp = (wxp * onz_xpyp) + (wxm * onz_xmyp)
        onx_ym = (wxp * onz_xpym) + (wxm * onz_xmym)
        val = (wyp * onx_yp) + (wym * onx_ym)
        dxCache[rawID] = val

    # map values
    if(val >= 0.0):
        val = (val + 1.0) / 2.0
    else:
        val = (val + 3.0) / 6.0
    return [val, val, val]


def trueSphereOrigin(object):
    # tmpSphere = bpy.data.objects[object.name]

    # coord = list(object.matrix_world.to_translation()[:3])   # is the same...
    coord = [(object.matrix_world[0])[3], (object.matrix_world[1])[3], (object.matrix_world[2])[3]]
    return coord
