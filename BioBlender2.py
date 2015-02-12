# Blender modules
import bpy
from bpy import *
import bpy.path
from bpy.path import abspath
import mathutils
from mathutils import *

# Python standard modules
from urllib.parse import urlencode
from urllib.request import *
from html.parser import *
from smtplib import *
from email.mime.text import MIMEText
import time
import platform
import os
import codecs
import base64
from math import *
import pickle
import shutil
import subprocess
import sys
import traceback
import copy

# BioBlender Tables and Utils
from .table_values import (
	values_fi, 
	molecules_structure	 # Define animoacids structure
)

# ===== Fixes & Mods =================
'''

2015 / feb / 04
- [added 'append_file_to_current_blend`] use instead of link_append
- fixed reference to modelList -> tmpModel
- added pymol.cmd to pyMolPathSearch
'''

# ===== HELPERS ===============


def append_file_to_current_blend(Path, objName, Directory):
	'''
	for the time being this will permit older versions of Blender to use the append feature
	'''

	print('appending file')
	wm = bpy.ops.wm
	# if hasattr(wm, 'link_append'):
	if 'link_append' in dir(wm):
		wm.link_append(filepath=Path, filename=objName, directory=Directory, link=False)
	else:
		wm.append(filepath=Path, filename=objName, directory=Directory)


# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================

bpy.types.Object.BBInfo = bpy.props.StringProperty()  # From BioBlender1
bpy.types.Object.bb2_pdbID = bpy.props.StringProperty()  # bb2_pdbID / Numerical, incremental
bpy.types.Object.bb2_objectType = bpy.props.StringProperty()  # bb2_objectType / ATOM, PDBEMPTY, CHAINEMPTY, SURFACE
bpy.types.Object.bb2_subID = bpy.props.StringProperty()  # bb2_subID / e.g.: Chain ID
bpy.types.Object.bb2_pdbPath = bpy.props.StringProperty()  # bb2_pdbPath / just for Empties; e.g.: in Setup function
bpy.types.Object.bb2_outputOptions = bpy.props.EnumProperty(
	name="bb2_outputoptions",
	default="1",
	items=[
		("0", "Main", ""), ("1", "+Side", ""), ("2", "+Hyd", ""),
		("3", "Surface", ""),("4", "MLP Main", ""),("5", "MLP +Side", ""),
		("6", "MLP +Hyd", ""), ("7", "MLP Surface", "")]
)



# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



# OS detection
opSystem = ""
if os.sys.platform == "linux":
	opSystem = "linux"
elif os.sys.platform == "darwin":
	opSystem = "darwin"
else:
	opSystem = "win"


# Home Path
homePath = os.path.dirname(__file__) + os.sep 


# Blender Path
blenderPath = str(sys.executable)


# Python Path
if ((opSystem == "linux") or (opSystem=="darwin")):
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

if ((opSystem == "linux") or (opSystem=="darwin")):
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


# ==================================================================================================================

bootstrap = -1		# A way to avoid infamous RestricContext error on boot

# Generic BB2 "Global" variables
curFrame = 1
filePath = ""
activeTag = ""                # the active/selected model
projectLastFrame = 1		# Used in multi-pdb context to calculate offset Frame for GE Simulation

# PDB-MODELS-related variables (no chains-related variables)
pdbID = 0
pdbIDmodelsDictionary = {}	# Key: pdb_ID;  value: a dictionary containing all the models of the current (ID) PDB

# CHAINS-related variables
chainCount = 0			# PDB import preview: chains number in PDB
importChainID = []		# PDB import preview: chains names in PDB
importChainOrderList = []	# PDB import preview: chains to be imported
mainChainCacheDict = {}        # a cache to that contains only mainchain atoms for the various PDBid (key)
mainChainCache_NucleicDict = {}
mainChainCache_Nucleic_FilteredDict = {}
chainCacheDict = {}            # a cache to that contains all non-H atoms for the various PDBid (key)
chainCache_NucleicDict = {}
ChainModels = {}            # cache to contain model of chains and atoms belonging to chains

# EP-related variables
epOBJ = []                # holds a list of object generated by the EP visualization
curveCount = 0            # a counter for EP curves
dxData = []                # list[n] of Potential data
dimension = []            # list[3] of dx grid dimension
origin = []                # list[3] of dx grid origin
dxCache = {}                # cache to speed up vertexColor mapping
maxCurveSet = 4

# ==================================================================================================================

#Define common atom name as variables to avoid RSI from typing quotes
C = "C"
N = "N"
O = "O"
S = "S"
H = "H"
CA = "CA"
P = "P"
FE = "FE"
MG = "MG"
ZN = "ZN"
CU = "CU"
NA = "NA"
K = "K"
CL = "CL"
MN = "MN"
F = "F"
NucleicAtoms=["P","O2P","OP2","O1P","OP1","O5'","C5'","C4'","C3'","O4'","C1'","C2'","O3'","O2'"]
NucleicAtoms_Filtered=["P","O5'","C5'","C4'","C3'","O3'"]


# Define atom color [R,G,B]
color={C:[0.1,0.1,0.1], CA:[0.4,1.0,0.14], N:[0.24,0.41,0.7], O:[0.46,0.1,0.1], S:[1.0,0.75,0.17], P:[1.0,0.37,0.05], FE:[1.0,0.5,0.0], MG:[0.64,1.0,0.05], ZN:[0.32,0.42,1], CU:[1.0,0.67,0.0], NA:[0.8,0.48,1.0], K:[0.72,0.29,1.0], CL:[0.1,1.0,0.6], MN:[0.67,0.6,1.0], H:[0.9,0.9,0.9], F:[0.27, 0.8, 0.21]}


dic_lipo_materials={}


# Define atom scales [visual Van der Waals scale, collision radius scale]
scale_vdw={C:[1.35,0.6], CA:[1.59,0.6], N:[1.23,0.6], O:[1.2,0.6], S:[1.43,0.6], P:[1.43,0.6], FE:[1.59,0.6], MG:[1.37,0.6], ZN:[1.1,0.6], CU:[1.1,0.6], NA:[1.8,0.6], K:[2.18,0.6], CL:[1.37,0.6], MN:[1.59,0.6], H:[0.95,0.3], F:[1.16, 0.6]}


# Define atom scales [visual covalent scale, collision radius scale]
scale_cov={C:[1.1,0.6], CA:[0.99,0.6], N:[1.07,0.6], O:[1.04,0.6], S:[1.46,0.6], P:[1.51,0.6], FE:[0.64,0.6], MG:[0.65,0.6], ZN:[0.74,0.6], CU:[0.72,0.6], NA:[0.95,0.6], K:[1.33,0.6], CL:[1.81,0.6], MN:[0.46,0.6], H:[0.53,0.3], F:[1.36, 0.6]}


# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


def bootstrapping():
	print("Bootstrapping")
	# Gravity, rendering engine
	bpy.context.scene.render.engine='BLENDER_GAME'
	bpy.context.scene.game_settings.physics_gravity = 0.0
	bpy.context.scene.render.engine = 'BLENDER_RENDER'
	# Materials
	elencoMateriali = [CA, H, N, O, S, ZN, P, FE, MG, MN, CU, NA, K, CL, F]
	if not("C" in bpy.data.materials):
		bpy.ops.material.new()
		bpy.data.materials[-1].name = "C"
		bpy.data.materials["C"].diffuse_color =  color[C]
	for m in elencoMateriali:
		if not(m in bpy.data.materials):
			bpy.data.materials['C'].copy()
			bpy.data.materials['C.001'].name = m
			bpy.data.materials[m].diffuse_color =  color[m]
	create_fi_materials()
	# get next PDB ID
	global pdbID
	pdbID = getNewPDBid()
	# EmptySet (Hemi, BBCamera)
	bpy.context.scene.layers[19] = True
	for i in range(0,19):
		bpy.context.scene.layers[i] = False
	bpy.context.scene.layers[19] = True
	elementiDaImportare = ['Empty', 'Hemi']
	try:
		for objName in elementiDaImportare:
			Directory = homePath + "data" + os.sep + "EmptySet.blend" + "/" + "Object" + "/"
			Path = os.sep + os.sep + "data" + os.sep + "EmptySet.blend" + "/" + "Object" + "/" + objName
			append_file_to_current_blend(Path, objName, Directory)
	except Exception as E:
		raise Exception ("Problem in import EmptySet.blend: ", E)
	global bootstrap
	bootstrap = 2



def getNewPDBid():
	print("get_new_PDB_id")
	tmp = 0
	for o in bpy.data.objects:
		if(o.bb2_pdbID != ""):
			tmp = o.bb2_pdbID
	tmp = tmp+1
	return tmp



def create_fi_materials():
	print("create_fi_materials")
	global dic_lipo_materials
	try:
		for item in molecules_structure:
			for item_at in molecules_structure[item]:
				value_fi_returned = parse_fi_values(item, item_at)
				if not value_fi_returned in dic_lipo_materials:
					bpy.data.materials['C'].copy()
					valuecolor = value_fi_returned
					bpy.data.materials['C.001'].name = "matlipo_"+ str(valuecolor)
					bpy.data.materials["matlipo_"+ str(valuecolor)].diffuse_color =  [float(valuecolor), float(valuecolor), float(valuecolor)]
					dic_lipo_materials[str(valuecolor)] = "matlipo_"+ str(valuecolor)
	except Exception as E:
		raise Exception ("Unable to create lipo materials", E)



def parse_fi_values(am_name, at_name):
	try:
		value_of_atom = values_fi[am_name][at_name]
		if float(value_of_atom) <= 0:
			value_final = (float(value_of_atom)+2)/4
		else:
			value_final = (float(value_of_atom)+1)/2
		value_final = "%5.3f" % float(value_final)
		return value_final
	except Exception as E:
		raise Exception ("Unable to parse fi values", E)


def retrieve_fi_materials(am_name,at_name):
	material_value=parse_fi_values(am_name,at_name)
	material_name=dic_lipo_materials[material_value]
	return material_name
# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


importReady = False



class BB2_GUI_PDB_IMPORT(bpy.types.Panel):	
	bl_idname = "BB2_GUI_PDB_IMPORT"
	bl_label = "BioBlender 2 PDB import"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBDeltaFrame = bpy.props.IntProperty(attr="BBDeltaFrame", name="Keyframe Interval", description="The number of in-between frames between each model for animation", default=100, min=1, max=200, soft_min=5, soft_max=50)
	bpy.types.Scene.BBLayerImport = bpy.props.BoolVectorProperty(attr="BBLayerImport", size=20, subtype='LAYER', name="Import on Layer", description="Import on Layer")
	bpy.types.Scene.BBImportPath = bpy.props.StringProperty(attr="BBImportPath", description="", default="", subtype="FILE_PATH")
	bpy.types.Scene.BBModelRemark = bpy.props.StringProperty(attr="BBModelRemark", description="Model name tag for multiple imports", default="protein0")
	bpy.types.Scene.BBImportFeedback = bpy.props.StringProperty(attr="BBImportFeedback", description="Import Feedback", default="")
	bpy.types.Scene.BBImportChain = bpy.props.StringProperty(attr="BBImportChain", description="Import Chain", default="")
	bpy.types.Scene.BBImportChainOrder = bpy.props.StringProperty(attr="BBImportChainOrder", description="List of chains to be imported", default="")
	bpy.types.Scene.BBImportOrder = bpy.props.StringProperty(attr="BBImportOrder", description="List of models to be imported", default="")
	bpy.types.Scene.BBImportHydrogen = bpy.props.BoolProperty(attr="BBImportHydrogen", name="Import Hydrogen", description="Import hydrogen atoms (Slower)", default=False)
	# ================
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		split = layout.split(percentage=0.7)
		split.prop(scene, "BBImportPath", text="")
		split.operator("ops.bb2_operator_make_preview")
		row = layout.row()
		row.prop(scene, "BBModelRemark", text="")
		row = layout.row()
		row.prop(scene, "BBImportFeedback", text="", emboss=False)
		row = layout.row()
		# left column
		split = layout.split(percentage=0.7)
		col = split.column()
		col.prop(scene, "BBImportOrder", text="")
		# right column
		col = split.column()
		col.prop(scene, "BBDeltaFrame")
		# next row
		row = layout.row()
		row.prop(scene, "BBImportChain", text="", emboss=False)
		row = layout.row()
		row.prop(scene, "BBImportChainOrder", text="")
		row = layout.row()
		row.prop(scene, "BBLayerImport")
		row = layout.row()
		row.prop(scene, "BBImportHydrogen")
		row = layout.row()
		row.scale_y = 2
		if importReady:
			row.operator("ops.bb2_operator_import")
		else:
			row.active = False  
			row.operator("ops.bb2_operator_import", text="Error: Not Ready to Import", icon="X")



class bb2_operator_make_preview(types.Operator):
	bl_idname = "ops.bb2_operator_make_preview"
	bl_label = "Make Preview"
	bl_description = "Make Preview"
	def invoke(self, context, event):
		try:
			if bootstrap == -1:
				bootstrapping()
			global importReady
			importReady = False
			bpy.context.scene.BBImportFeedback = ""
			bpy.context.scene.BBImportChain = ""
			bpy.context.scene.BBImportOrder = ""
			bpy.context.scene.BBImportChainOrder = ""
			importReady = importPreview(retrieved=False)
			print("Import Ready: " + str(importReady))
		except Exception as E:
			s = "Import Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_make_preview)



class bb2_operator_import(types.Operator):
	bl_idname = "ops.bb2_operator_import"
	bl_label = "Import PDB"
	bl_description = "generate 3D Model"
	def invoke(self, context, event):
		try:			
			if bootstrap == 0:
				bootstrap()
			bpy.context.user_preferences.edit.use_global_undo = False
			core_importFile()
			bpy.context.user_preferences.edit.use_global_undo = True
		except Exception as E:
			s = "Import Failed: " + str(E)
			print (s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_import)



# validate and get the number of models in the BBImportOrder string
def getNumModel():
	try:
		tmpPDBmodelsList = [int(tmpPDBmodelsBBio) for tmpPDBmodelsBBio in bpy.context.scene.BBImportOrder.split(',')]
		print("getNumModel() => " + str(tmpPDBmodelsList))
		return len(tmpPDBmodelsList)
	except:
		return -1


def index_element(this_list, elemen_list):
	print("index_element")
	for ik in range(len(this_list)):
		if elemen_list==this_list[ik]:
			return ik


def importPreview(verbose =  False, retrieved = False):
	global chainCount
	global importChainID
	print("Import Preview")
	tmpPreviewFilePath = abspath(str(bpy.context.scene.BBImportPath))
	# get PDB straight from PDB.org
	if (len(tmpPreviewFilePath)==4) and not(retrieved):
		retrievedFile = pdbdotorg(tmpPreviewFilePath)
		if retrievedFile:
			bpy.context.scene.BBImportFeedback = "Found matching Protein on PDB.org"
		else:
			bpy.context.scene.BBImportFeedback = "Nothing matching this ID found on PDB.org"
			return False
	extension = str(bpy.context.scene.BBImportPath).lower().endswith
	try:
		#file = open(tmpPreviewFilePath,"r")
		file = open(str(bpy.context.scene.BBImportPath),"r")
	except:
		bpy.context.scene.BBImportFeedback = "File not found"
		return False
	else:
		if extension(".pdb") or extension(".pqr") or extension(".txt"):
			bpy.context.scene.BBModelRemark = bpy.context.scene.BBImportPath[-8:-4]
		else:
			bpy.context.scene.BBModelRemark = bpy.context.scene.BBImportPath[-4:]
		# open is successful, check file extension
		if extension(".pdb") or extension(".pqr"):
			modelCount = 0
			importFileModel = []
			# read the chain id
			chainCount = 0
			importChainID = []
			# read file
			for line in file:
				line = PDBString(line)
				# count number of models in file using the start tag MODEL
				if line.get("tag") == "MODEL":
					tmpPreviewModelID = line.get("modelID")
					importFileModel.append(tmpPreviewModelID)
				# count number of models in file using the end tag MODEL
				elif line.get("tag") == "ENDMDL":
					modelCount += 1
				# count number of chains in file using the start tag ATOM    1
				if line.get("tag") == "ATOM":
					currentChainID = line.get("chainID")
					if currentChainID not in importChainID:
						chainCount += 1
						importChainID.append(currentChainID)
			# Special case for files containing 1 model with no opening model tag
			if len(importFileModel) == 0: importFileModel.append(0)
			# show list of models for importer to load
			bpy.context.scene.BBImportOrder = str(importFileModel)[1:-1]
			# if all okay, display feedback message
			bpy.context.scene.BBImportFeedback = "File contains " + str(len(importFileModel)) + " PDB Models"
			# if all okay, display feedback message
			bpy.context.scene.BBImportChain = "File contains chains " + str(importChainID)
			tmpChainOrderString = ",".join(importChainID)
			bpy.context.scene.BBImportChainOrder = str(tmpChainOrderString)
			file.close()
			return True
		if extension(".txt") or extension(".csv"):
			# simply get list of all files from a th specified directory
			fileList = os.listdir(os.path.dirname(tmpPreviewFilePath))
			fileListClean = []
			for f in fileList:
				# find only matching extensions
				ext = f[-4:].lower()
				if  ext == '.txt' or ext == '.csv':
					fileListClean.append (f)
			bpy.context.scene.BBImportOrder = ", ".join(fileListClean)
			# if all okay, display feedback message
			bpy.context.scene.BBImportFeedback = "Folder contains " + str(len(fileListClean)) + " text Files"
			file.close()
			return True
		# otherwise...
		bpy.context.scene.BBImportFeedback = "Error: Unrecognized File Extension"
		file.close()
		return False



# retrieve PDB from pdb.org
def pdbdotorg(id):
	print("pdbdotorg")
	url1 = str("http://www.pdb.org/pdb/files/"+id+".pdb")
	save1 = str(homePath+"fetched" + os.sep + id +".pdb")
	if opSystem == "linux":
		if not os.path.isdir(quotedPath(homePath+"fetched")):
			os.mkdir(quotedPath(homePath + "fetched"))
	elif opSystem == "darwin":
		if not os.path.isdir(quotedPath(homePath+"fetched")):
			os.mkdir(quotedPath(homePath + "fetched"))
	else:
		if not os.path.isdir(r"\\?\\" + homePath+"fetched"):
			os.mkdir(r"\\?\\" + homePath+"fetched")
	# get file from the web
	try:
		filename, header = urlretrieve(url1, save1)
		bpy.context.scene.BBImportPath = save1
		importPreview(False, True)
		return filename
	except:
		return False



class PDBString(str):
	print("PDB String")

	# Parses PDB line using column attribute
	# file definition is taken from www.wwpdb.org/documentation/format32/sect9.html
	# The function tries to be smart by striping out whitespaces
	# and converts certain properties to list
	def get(self, property):
		if property == "tag": return self[0:6].strip()
		if property == "serial": return self[6:11].strip()
		if property == "name": return self[12:16].strip()
		if property == "altLoc": return self[16:17].strip()
		if property == "aminoName": return self[17:20].strip()
		if property == "chainID": return self[21:22].strip()
		if property == "chainSeq": return self[22:26].strip()
		if property == "iCode": return self[26:27].strip()
		if property == "loc": 
			x = float(self[29:38])
			y = float(self[38:46])
			z = float(self[46:54])
			return [x,y,z]

		# if property == "occupancy": return self[54:60].strip()
		if property == "tempFactor": return self[60:66].strip()
		if property == "element": return self[76:78].strip()
		if property == "charge": return self[78:80].strip()
		if property == "modelID": return int(self[6:20].strip())
		# if no match found:
		return None

	# insert data into a 80 column pdb string
	def set(self,loc,prop):
		# insert prop into self[loc], but not changing the length of the string
		newStr = self[0:loc] + str(prop) + self[loc + len(str(prop)):]
		return PDBString(newStr)



def core_importFile():
	print("core_import_File")
	bpy.ops.object.select_all(action="DESELECT")
	for o in bpy.data.objects:
		o.select = False
	bpy.context.scene.objects.active = None
	tmpFilePath = abspath(bpy.context.scene.BBImportPath)
	extension = tmpFilePath.lower().endswith
	# user input sanity check
	if getNumModel() == -1:
		raise Exception("Error: Invalid user ordering of model sequence.  Use comma to separate values")
	if extension(".pdb") or extension(".pqr"):
		core_parsePDB(tmpFilePath)
	elif extension(".txt") or extension(".csv"):
		core_parseTXT(tmpFilePath)



def core_parsePDB(filePath):
	print("core_parse_pdb")
	tmpPDBmodelDictionary = {}		# key: atom name; value: String, the Atom BBInfo; for the CURRENT model
	tmpPDBmodelID = 0 
	tmpPDBmodelImportOrder = [int(tmpM) for tmpM in bpy.context.scene.BBImportOrder.split(',')]
	global mainChainCacheDict
	global mainChainCache_NucleicDict
	global mainChainCache_Nucleic_FilteredDict
	global chainCacheDict
	global chainCache_NucleicDict
	global pdbIDmodelsDictionary
	
	# New, due to multi-pdb version wrapped on a single-pdb one
	mainChainCache = []        # a cache to that contains only mainchain atoms
	mainChainCache_Nucleic = []
	mainChainCache_Nucleic_Filtered=[]
	chainCache = {}            # a cache to that contains all non-H atoms
	chainCache_Nucleic = {}
	
	pdbIDmodelsDictionary[pdbID] = {}
	
	
	global importChainOrderList
	importChainOrderList = []
	importChainOrderList = [tmpCOLI for tmpCOLI in bpy.context.scene.BBImportChainOrder.split(',')]
	print('importChainOrderList', importChainOrderList)
	
	# 2013-06-28 ---  Removes "1+" and "1-"... hoping it will not affect "standard" files...
	try:
		f = open(filePath, "r")
		lines = f.readlines()
		lineCounter = 0
		for line in lines:
			if(line.startswith("ATOM")):
				line = line.replace("1+", "  ")
				line = line.replace("1-", "  ")
			lines[lineCounter] = line
			lineCounter = lineCounter + 1
		f.close()
		f = open(filePath, "w")
		f.writelines(lines)
		f.close()
	except Exception as E:
		s = "Unable to fix tmp.pdb: " + str(E)
		print(s)

	print("A")

	# open file (assuming input is valid)
	with open(filePath,"r") as file:
		for line in file:
			line = line.replace("\n", "")
			line = line.replace("\r", "")
			line = PDBString(line)
			tag = line.get("tag")

			# if tag is tmpPDBmodelDictionary, load tmpPDBmodelDictionary id
			if tag == "MODEL":
				tmpPDBmodelID = line.get("modelID")

			# if tag is ATOM, load column data (skip this if tmpPDBmodelID is not in list of models)
			elif (tmpPDBmodelID in tmpPDBmodelImportOrder) and (tag == "ATOM" or tag == "HETATM"):
				# check for element type
				atomName = line.get("name")
				elementName = line.get("element")
				elementTypeResidue = line.get("aminoName")
				atomtype = line.get("tag")

				# skip water
				if elementTypeResidue == "HOH":
					continue

				# decide if hydrogen should be skipped
				if not bpy.context.scene.BBImportHydrogen and elementName == H:
					continue

				# decide if current Chain should be skipped
				if (line.get("chainID") not in importChainOrderList):
					continue

				tmpPDBobjectName = bpy.context.scene.BBModelRemark
				key = str(tmpPDBobjectName) + "#" + line.get("serial").rjust(5, "0")
				tmpPDBmodelDictionary[key] = line

				# add mchain atom data to dictionary for building bonds
				if atomName==N or atomName==C or (atomName==CA and elementName!=CA):
					if key not in mainChainCache: mainChainCache.append(key)
				if atomName in NucleicAtoms:
					if atomName in NucleicAtoms_Filtered:
						if key not in mainChainCache_Nucleic_Filtered:
							mainChainCache_Nucleic_Filtered.append(key)
					else:
						if key not in mainChainCache_Nucleic:
							mainChainCache_Nucleic.append(key)
					if atomName =="C3'":
						mainChainCache_Nucleic.append(key)

				# add all atom data to dictionary for building bonds
				elementTypeNucleic=["D","A","U","G","C","DC","DG","DA","DT"]
				if elementName != H and (not elementTypeResidue in elementTypeNucleic ) and atomtype=="ATOM":
					chainCache[key] = line.get("aminoName") + "#" + line.get("chainSeq") + "#" + line.get("name") + "#" + line.get("chainID") + "#" + line.get("element")
				if elementName != H and (elementTypeResidue in elementTypeNucleic) and atomtype=="ATOM":
					chainCache_Nucleic[key] = line.get("aminoName") + "#" + line.get("chainSeq") + "#" + line.get("name") + "#" + line.get("chainID") + "#" + line.get("element")
				# To multi-pdb: insert caches above in global chain caches dictionaries, using pdbID as key:

			# when the end of a tmpPDBmodelDictionary is reached, add the tmpPDBmodelDictionary dictionary to the list
			if tag == "ENDMDL" or tag=="END" or tag == "MODEL" and (tmpPDBmodelID in tmpPDBmodelImportOrder):
				# We add a new MODEL entry to the global pdbIDmodelsDictionary[pdbID],
				# based on the current MODEL ID, and we assign the tmpPDBmodelDictionary to this entry.

				if not (tag == 'END'):
					(pdbIDmodelsDictionary[pdbID])[tmpPDBmodelID] = tmpPDBmodelDictionary
				else:
					# ugly test: run through the file again and 
					# look at the last 2 lines.
					# if the current tag is END and the last 2 lines are
					# TER, END. or 'MASTER and END' then the format is all ATOMs and no MODEL.
					with open(filePath,"r") as sfile:
						lines = [l[:3] for l in sfile if l.strip()][-2:]
						lines = '|'.join(lines)
						if lines in {'TER|END', 'MAS|END'}:
							(pdbIDmodelsDictionary[pdbID])[tmpPDBmodelID] = tmpPDBmodelDictionary

				''' f test '''
				f = (pdbIDmodelsDictionary[pdbID])[tmpPDBmodelID]
				print('tmpPDBmodelID', tmpPDBmodelID, ':', len(f))

				# So now pdbIDmodelsDictionary[pdbID] is a Dictionary: model-dict; the second dict is [atomName]-BBInfo
				tmpPDBmodelDictionary = {}



	mainChainCacheDict[pdbID] = mainChainCache
	mainChainCache_NucleicDict[pdbID] = mainChainCache_Nucleic
	mainChainCache_Nucleic_FilteredDict[pdbID] = mainChainCache_Nucleic_Filtered
	chainCacheDict[pdbID] = chainCache
	chainCache_NucleicDict[pdbID] = chainCache_Nucleic
	core_sort_hr()



def core_parseTXT(filePath):
	tmpPDBmodelDictionary = {}
	global pdbIDmodelsDictionary
	# Parse text files sequence
	tmpPDBmodelImportOrder = bpy.context.scene.BBImportOrder.split(',')
	for fileName in tmpPDBmodelImportOrder:
		# open each file from the list
		with open(os.path.dirname(filePath)+"/"+fileName.strip(),"r") as f:
			atomCounter = 0
			# force the atom type
			char = C
			# for each line of the file
			for line in f:
				tmpPDBobjectName = bpy.context.scene.BBModelRemark
				key = str(tmpPDBobjectName) + "#" + str(atomCounter).rjust(5, "0")
				line = line.replace('"', "")	# cleanup some unconforming data
				split_line = line.split()
				x = "%8.3f" % float(split_line[0])
				y = "%8.3f" % float(split_line[1])
				z = "%8.3f" % float(split_line[2])
				# a somewhat hackish way to generate a PDB-conformant string for the unified reader to use
				line = PDBString("ATOM                                                                         " + char)
				# insert location in-situ
				line = line.set(30,x)
				line = line.set(38,y)
				line = line.set(46,z)
				tmpPDBmodelDictionary[key] = line
				atomCounter += 1
			(pdbIDmodelsDictionary[pdbID])[0] = tmpPDBmodelDictionary
			tmpPDBmodelDictionary = {}
	core_sort_hr()



def core_sort_hr():	
	print("core_sort_hr")
	# ======= IMPORT ON SELECTED LAYER = START =======================
	selectedLayer = 0
	tmp = 0
	for x in bpy.context.scene.BBLayerImport:
		if ((x) and (tmp!=19)):
			selectedLayer = tmp
		tmp += 1
	bpy.context.scene.layers[selectedLayer] = True
	for i in range(0,20):
		if (i!=selectedLayer):
			bpy.context.scene.layers[i] = False
	bpy.context.scene.layers[19] = True
	# ======= IMPORT ON SELECTED LAYER = END =========================
	# loading the Atom from library.blend
	try:
		objName = "atom"
		Directory = homePath + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep
		Path = os.sep + os.sep + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep + objName
		append_file_to_current_blend(Path, objName, Directory)

		bpy.data.objects[objName].name = objName
		bpy.data.objects[objName].select = True
		bpy.context.scene.objects.active = bpy.data.objects[objName]

	except Exception as E:
		raise Exception ("Template atom object cannot be loaded from library: ", E)
	# Make high res atom model
	bpy.ops.object.modifier_add(type = 'SUBSURF')
	modificatore = bpy.context.scene.objects.active.modifiers[0]
	modificatore.levels = 1
	modificatore.render_levels = 1
	modificatore.name = "SubSurf1"
	bpy.ops.object.modifier_apply(modifier="SubSurf1")
	# Models (3D) creation
	core_createModels()



def core_createModels():
	print("core_create_Models")
	# Empty creation
	bpy.ops.object.empty_add(type='PLAIN_AXES')
	bpy.context.scene.objects.active.name = copy.copy(str(bpy.context.scene.BBModelRemark))
	parentEmpty = bpy.data.objects[str(bpy.context.scene.BBModelRemark)]
	bpy.context.scene.objects.active.bb2_pdbID = copy.copy(str(pdbID))
	bpy.context.scene.objects.active.bb2_objectType = "PDBEMPTY"
	bpy.context.scene.objects.active.bb2_outputOptions = "1"
	bpy.context.scene.objects.active.bb2_pdbPath = copy.copy(str(bpy.context.scene.BBImportPath))
	bpy.data.objects[str(bpy.context.scene.BBModelRemark)].location = ((0.0, 0.0, 0.0))

	global chainCache
	global curFrame
	id = bpy.context.scene.BBModelRemark
	curFrame = 1
	# Build 3D scene from pdbIDmodelsDictionary

	DEBUG = False

	# write the dict to disc for debug
	if DEBUG:
		import json
		this_root = os.path.dirname(__file__)
		destination_path = os.path.join(this_root, 'tmp', 'PDB_tree.json')
		m = json.dumps(pdbIDmodelsDictionary, sort_keys=True, indent=2)
		with open(destination_path, 'w') as PDB_tree:
			PDB_tree.writelines(m)

	# pdbID references a specific model.
	# that model's dict it returned by pdbIDmodelsDictionary[pdbID]
	# m is the key, into that model's dictionary it will return a conformation of that model
	# the keys are unsorted.
	for m in pdbIDmodelsDictionary[pdbID]:
		print(m)
		model = (pdbIDmodelsDictionary[pdbID])[m]

		# Prova: se il dizionario-model in esame e' vuoto, saltalo (non e' stato selezionato il relativo model nella lista)
		if not (model):
			print('key:', m, ' - doesn\'t appear to have stored a conformation')
			continue
		
		# =======
		# reset
		bpy.ops.object.select_all(action="DESELECT")
		for o in bpy.data.objects:
			o.select = False
		bpy.context.scene.objects.active = None
		bpy.context.scene.frame_set(curFrame)

		# on first model, Place atoms in scene
		if curFrame == 1:
			modelCopy = model.copy()
			# select and temporary rename template atom
			bpy.data.objects["atom"].hide = False
			bpy.data.objects["atom"].select = True
			bpy.data.objects["atom"].name = str(id)
			# (count - 1) because there is the original template object.
			for i in range(len(model)-1):
				bpy.ops.object.duplicate(linked = True, mode='DUMMY')
			try:
				# walk through list of objects and set name, location and material for each atom
				for i, obj in enumerate(bpy.data.objects):
					# if the object is the one of those we just created (i.e. if name matches xx.0000)
					if (obj.name.split(".")[0] == id) and (obj.type=="MESH"):
						# descructively walk through the modelCopy varible
						entry = modelCopy.popitem()
						# assign obj name, material, etc.  object Locations are assigned later
						obj.name = entry[0]
						index = str(entry[1])[76:78].strip()
						obj.material_slots[0].material = bpy.data.materials[index]
						# adjust radius
						obj.scale = [scale_cov[index][0], scale_cov[index][0], scale_cov[index][0]]
						obj.game.radius = scale_cov[index][1]    					
						# add atom info as RNA string to each object
						obj.BBInfo = str(entry[1])
						obj.bb2_pdbID = copy.copy(str(pdbID))
						obj.bb2_objectType = "ATOM"
						# Setting EMPTY as parent for this object
						obj.select = True
						obj.parent = bpy.data.objects[str(parentEmpty.name)]
			except Exception as E:
				raise Exception ("Unable to generate 3D model from PDB File", E)
	
			# MAKE BONDS
			try:
				mainChainCache = mainChainCacheDict[pdbID]
				mainChainCache_Nucleic = mainChainCache_NucleicDict[pdbID]
				mainChainCache_Nucleic_Filtered = mainChainCache_Nucleic_FilteredDict[pdbID]
				chainCache = chainCacheDict[pdbID]
				chainCache_Nucleic = chainCache_NucleicDict[pdbID]
				tmpModel = (pdbIDmodelsDictionary[pdbID])[m]
				# =====
				cacheSize = len(mainChainCache) - 1
				for i, entry in enumerate(mainChainCache):
					# Skipping Last Atom to avoid cyclic dependency
					if i < cacheSize:
						# Adding constraints, using atom position to correctly orient hinge x axis
						obj = bpy.data.objects[entry]
						nextEntry = bpy.data.objects[mainChainCache[i+1]]
						#line=tmpModel[0][entry]
						line=tmpModel[entry]
						obj.location=line.get("loc")
						#line=tmpModel[0][mainChainCache[i+1]]
						line=tmpModel[mainChainCache[i+1]]
						nextEntry.location=line.get("loc")
						addRigidBodyRotamer(obj,nextEntry)
				#bonds for Nucleic Acids
				cacheSize = len(mainChainCache_Nucleic_Filtered) - 1
				for i, entry in enumerate(mainChainCache_Nucleic_Filtered):
					# Skipping Last Atom to avoid cyclic dependency
					if i < cacheSize:
						# Adding constraints, using atom position to correctly orient hinge x axis
						obj = bpy.data.objects[entry]
						nextEntry = bpy.data.objects[mainChainCache_Nucleic_Filtered[i+1]]
						#line=tmpModel[0][entry]
						line=tmpModel[entry]
						obj.location=line.get("loc")
						#line=tmpModel[0][mainChainCache_Nucleic_Filtered[i+1]]
						line=tmpModel[mainChainCache_Nucleic_Filtered[i+1]]
						nextEntry.location=line.get("loc")
						addRigidBodyRotamer(obj,nextEntry)	
				chainCache = sorted(chainCache.items())
				for entry in chainCache:
					line = entry[1].split("#")
					amac = line[0]
					chainSeq = line[1]
					atom = line[2]
					chainID = line[3]
					# skip mainchain atoms
					if (atom != C and atom != CA and atom != N and atom != H):
						# for side chain, look up parents based on rules
						parent = bondLookUp(atom=atom, amac=amac)
						# generate name of parents
						target = amac+ "#" + chainSeq + "#" + parent[0] + "#" + chainID + "#" + parent[1]
						# lookup name of blenderobject based on parent name
						targetKey = "atom"
						for item in chainCache:
							if item[1] == target:
								targetKey = item[0]
								break
						# set up the constraint
						# 2013-06-27 --- if targetKey == CA, skip...
						if targetKey == "atom":
							print("TargetKey not set, will skip Rigid Body Joint")
						else:
							obj = bpy.data.objects[entry[0]]
							#line=tmpModel[0][entry[0]]
							line=tmpModel[entry[0]]
							obj.location=line.get("loc")
							#line=tmpModel[0][targetKey]
							line=tmpModel[targetKey]
							nextEntry.location=line.get("loc")
							addRigidBodyRotamer(obj,bpy.data.objects[targetKey])
				chainCache = sorted(chainCache_Nucleic.items())
				for entry in chainCache:
					line = entry[1].split("#")
					amac = line[0]
					chainSeq = line[1]
					atom = line[2]
					chainID = line[3]
					# skip mainchain atoms
					#if atom=="O2P" or atom=="O1P" or atom=="C3'" or atom=="C2'"or atom=="C1'" or atom=="O4'":
					if not atom in NucleicAtoms:
						# for side chain, look up parents based on rules
						parent = bondLookUp_NucleicMain(atom=atom, amac=amac)
						# generate name of parents
						target = amac+ "#" + chainSeq + "#" + parent[0] + "#" + chainID + "#" + parent[1]
						# lookup name of blenderobject based on parent name
						targetKey = "atom"
						for item in chainCache:
							if item[1] == target:
								targetKey = item[0]
								break
						# set up the constraint
						if targetKey == "atom":
							print("TargetKey not set, will skip Rigid Body Joint")
						else:
							obj = bpy.data.objects[entry[0]]
							line = tmpModel[entry[0]]
							obj.location=line.get("loc")
							line = tmpModel[targetKey]
							nextEntry.location=line.get("loc")
							addRigidBodyRotamer(obj,bpy.data.objects[targetKey])	
			except Exception as E:
				raise Exception ("Unable to generate all bonds and constraints:", E)
		# for all models, insert key frame
		try:
			for key, line in ((pdbIDmodelsDictionary[pdbID])[m]).items():
				OBJ = bpy.data.objects[key]
				OBJ.select = True
				OBJ.location = line.get("loc")
		except Exception as E:
				raise Exception ("Unable to place 3D atoms:", E)
		
		if len(pdbIDmodelsDictionary[pdbID]) != 1:
			# insert keyframe for animations
			try:
				bpy.ops.anim.keyframe_insert_menu(type='LocRotScale')
			except Exception as E:
				print("Exception: " + str(E))
			# advance frame
			bpy.context.scene.frame_end = curFrame
			curFrame += bpy.context.scene.BBDeltaFrame
	core_EmptyChainsCreation()



# lookup sidechain parents
def bondLookUp(atom, amac):
	if(atom=="O" or atom=="OXT"):    parent = ["C",C]
	elif(atom=="CB" or atom=="HA" or atom=="HA2" or atom=="HA3"):    parent = ["CA",C]
	elif(atom=="SG" or "HB" in atom or "OG" in atom or "CG" in atom):    parent = ["CB",C]
	elif(atom=="H" or atom=="H1" or atom=="H2" or atom=="H3"):    parent = ["N",N]
	elif(atom=="HG1"):    parent = ["OG1",O]
	elif(atom=="HG23" or atom=="HG22" or atom=="HG21"):    parent = ["CG2",C]
	elif(atom=="SD" or "CD" in atom or "ND" in atom or atom=="HG2" or atom=="HG3" or atom=="OD1" or atom=="OD2" or atom=="HG12" or atom=="HG13" or atom=="HG13"):
		if(amac=="ILE" or amac=="VAL"):    parent = ["CG1",C]
		else:    parent = ["CG",C]
	elif(atom=="CE2" or atom=="CE3" or atom=="NE2" or atom=="HD2"):
		if(amac=="GLN"):    parent = ["CD",C]
		elif(amac=="ARG" or amac=="LYS" or amac=="PRO"):    parent = ["CD",C]
		elif(amac=="ASP"):    parent = ["OD2",O]
		else:    parent = ["CD2",C]
	elif(atom=="CE1" or atom=="HD11" or atom=="HD12" or atom=="HD13" or atom=="HD1" or atom=="NE1"):
		if(amac=="HIS"):    parent = ["ND1",N]
		else:    parent = ["CD1",C]
	elif(atom=="NE" or atom=="HD3" or atom=="CE" or atom=="OE1" or atom=="OE2"):
		if(amac=="MET"):    parent = ["SD",S]
		else:    parent = ["CD",C]
	elif(atom=="CZ" or atom=="HE" or atom=="HE1"):
		if(amac=="ARG"):    parent = ["NE",N]
		elif(amac=="TRP"):    parent = ["NE1",N]
		elif(amac=="MET"):    parent = ["CE",C]
		elif(amac=="PHE" or amac=="HIS" or amac=="TYR"):        parent = ["CE1",C]
	elif(atom=="NH1" or atom=="NH2" or atom=="HZ" or atom=="OH"):        parent = ["CZ",C]
	elif(atom=="HH11" or atom=="HH12" or atom=="1HH1" or atom=="1HH2"):    parent = ["NH1",N]
	elif(atom=="HH21" or atom=="HH22" or atom=="2HH2" or atom=="1HH2"):    parent = ["NH2",N]
	elif(atom=="HD21" or atom=="HD22" or atom=="HD23"):
		if(amac=="LEU"):    parent = ["CD2",C]
		else:    parent = ["ND2",N]
	elif(atom=="HE3"  or atom=="NZ"):
		if(amac=="TRP"):    parent = ["CE3",C]
		else:    parent = ["CE",C]
	elif(atom=="HZ1" or atom=="HZ2" or atom=="HZ3"):
		if(amac=="TRP" and atom=="HZ2"):    parent = ["CZ2",S]
		elif(amac=="TRP" and atom=="HZ3"):    parent = ["CZ3",S]
		else:    parent = ["NZ",N]
	elif(atom=="HG"):
		if(amac=="LEU"):    parent = ["CG",C]
		if(amac=="CYS"):    parent = ["SG",S]
		else:    parent = ["OG",O]
	elif(atom=="HE2" or atom=="CZ2" or atom=="HE21" or atom=="HE22"):
		if(amac=="HIS" or amac=="GLN"):    parent = ["NE2",N]
		elif(amac=="PHE" or amac=="TYR" or amac=="TRP"):    parent = ["CE2",C]
		elif(amac=="GLU"):    parent = ["OE2",O]
		elif(amac=="MET" or amac=="LYS"):    parent = ["CE",C]
	elif(atom=="HH"):    parent = ["OH",O]
	elif(atom=="CZ3"):    parent = ["CE3",C]
	elif(atom=="CH2"):    parent = ["CZ2",C]
	elif(atom=="HH2"):    parent = ["CH2",C]
	return parent


def bondLookUp_NucleicMain(atom, amac): # define skeleton atoms
	print("entrati nel bondlookupnucleicmain")
	print("atom")
	print(str(atom))
	print("amac")
	print(str(amac))
	print("---calculating----")
	if(atom=="O4\'"): parent = ["C4\'", C]
	elif(atom=="C2\'"): parent = ["C3\'", C]
	elif(atom=="O2\'"): parent = ["C2\'", C]
	elif(atom=="C1\'"): parent = ["C2\'", C]
	# define base atoms
	elif(atom=="N9"): parent = ["C1\'", C]
	elif(atom=="C8"): parent = ["N9", N]
	elif(atom=="N7"): parent = ["C8", C]
	elif(atom=="C4"):
		if(amac=="A" or amac=="DA" or  amac=="G" or  amac=="DG"): parent = ["N9", N]
		elif(amac=="C" or amac=="DC") or(amac=="U" or amac=="DT"): parent = ["N3", N]
	elif(atom=="C5"): parent = ["C4", C]
	elif(atom=="N3"):
		if(amac=="A" or amac=="DA" or amac=="G" or amac=="DG"): parent = ["C4", C]
		elif(amac=="C" or amac=="DC" or amac=="U" or amac=="DT"): parent = ["C2", C]
	elif(atom=="C2"):
		if(amac=="A" or amac=="DA" or amac=="G" or amac=="DG"): parent = ["N3", N]
		elif(amac=="C" or amac=="DC" or amac=="U" or   amac=="DT"): parent = ["N1", N]
	elif(atom=="N1"):
		if(amac=="A" or amac=="DA" or amac=="G" or amac=="DG"): parent = ["C2", C]
		elif(amac=="C" or  amac=="DC" or amac=="U" or amac=="DT"): parent = ["C1\'", C]
	elif(atom=="C6"):
		if(amac=="A" or  amac=="DA" or  amac=="G" or amac=="DG"): parent = ["N1", N]
		elif(amac=="C" or   amac=="DC" or amac=="U" or   amac=="DT"): parent = ["C5", C]
	elif(atom=="N6" or atom=="O6"): parent = ["C6", C]
	elif(atom=="N2" or atom=="O2"): parent = ["C2", C]
	elif(atom=="N4" or atom=="O4"): parent = ["C4", C]
	elif(atom=="C7"): parent = ["C5", C]
	print("parent")
	print(str(parent))
	print("returned")
	return parent


#I suppose that the object's referential was not change (the same as the scene, with x (red axis) to the right, z (blue axis) up and y (green axis) behing)
def addRigidBodyRotamer(objectparent,objecttarget) : 
	#Add the rigid body joint for rotamer
	#to define a rotamer, an hinge is use, with the axis vector which come from the atom parent to the target and with a position at the center of the parent atom
	#This rotation transform the Ox axis of the parent, to the euler angle to orient the x axes (the hinge axis) of the pivot referential from this parent atom to the target  
	parentxaxis = Vector((1.0,0.0,0.0))
	hingevector=Vector((objecttarget.location[0]-objectparent.location[0], objecttarget.location[1]-objectparent.location[1], objecttarget.location[2]-objectparent.location[2]))
	rotvec2mapx2hingevector=parentxaxis.cross(hingevector)	
	rotvec2mapx2hingevector.normalize()
	angle2mapx2hingevector=parentxaxis.angle(hingevector)
	matrot=Matrix.Rotation(angle2mapx2hingevector, 3, rotvec2mapx2hingevector)
	euler=matrot.to_euler()
	#Add the rigid body join for rotamer	
	objectparent.constraints["RigidBody Joint"].target = objecttarget
	#objectparent.constraints["RigidBody Joint"].show_pivot = True
	objectparent.constraints["RigidBody Joint"].pivot_x = 0.0
	objectparent.constraints["RigidBody Joint"].pivot_y = 0.0
	objectparent.constraints["RigidBody Joint"].pivot_z = 0.0			
	objectparent.constraints["RigidBody Joint"].axis_x = euler[0]
	objectparent.constraints["RigidBody Joint"].axis_y = euler[1]
	objectparent.constraints["RigidBody Joint"].axis_z = euler[2]		
	#objectparent.rotation_mode='XYZ'


def core_EmptyChainsCreation():
	print("Empty Chains creation")
	chainsList = []
	for o in bpy.data.objects:
		if(o.bb2_pdbID == pdbID):
			if(o.bb2_objectType == "ATOM"):
				tmpChain = str(((o.BBInfo)[21:22]).strip())
				if tmpChain not in chainsList:
					# Creo la Empty, con le opportune proprieta'
					bpy.ops.object.empty_add(type='PLAIN_AXES')
					bpy.context.scene.objects.active.name = copy.copy(str(bpy.context.scene.BBModelRemark))
					bpy.context.scene.objects.active.bb2_pdbID = copy.copy(str(pdbID))
					bpy.context.scene.objects.active.bb2_objectType = "CHAINEMPTY"
					bpy.context.scene.objects.active.bb2_subID = copy.copy(str(tmpChain))
					bpy.context.scene.objects.active.location = ((0.0, 0.0, 0.0))
					tmpName = copy.copy(str(bpy.context.scene.objects.active.name))
					cE = bpy.data.objects[tmpName]
					# imposto la Empty come figlia della Parent Empty
					for d in bpy.data.objects:
						if(d.bb2_pdbID == pdbID):
							if(d.bb2_objectType == "PDBEMPTY"):
								cE.parent = bpy.data.objects[str(d.name)]
					# imposto l'oggetto come figlio di questa Empty, non piu' della Parent Empty
					o.parent = cE
					# inserisco questa sigla nella lista di ID
					chainsList.append(tmpChain)
				else:
					for c in bpy.data.objects:
						if(c.bb2_pdbID == pdbID):
							if(c.bb2_objectType == "CHAINEMPTY"):
								if(c.bb2_subID == tmpChain):
									o.parent = bpy.data.objects[str(c.name)]
	core_cleaningUp()


def core_cleaningUp():
	print("cleaning up")
	bpy.context.scene.frame_set(1)
	bpy.ops.object.select_all(action="DESELECT")
	for o in bpy.data.objects:
		o.select = False

	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			area.spaces[0].show_relationship_lines = False
	
	try:
		atomAction()
	except Exception as E:
		print("No models, no action")
		
	bpy.ops.object.select_all(action="DESELECT")
	for o in bpy.data.objects:
		o.select = False
	bpy.data.objects['BioBlender_Camera'].select = True
	bpy.context.scene.objects.active = bpy.data.objects['BioBlender_Camera']
	bpy.context.scene.camera = bpy.data.objects["BioBlender_Camera"]
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			area.spaces[0].region_3d.view_perspective="CAMERA"
	
	global pdbID
	pdbID = pdbID + 1 # VERY IMPORTANT!!!
	print("pdbID: " + str(pdbID))
	
	sessionSave()
	
	bpy.context.scene.BBImportPath = ""
	bpy.context.scene.BBImportHydrogen = False
	
	global chainCount
	global importChainID
	global importChainOrderList
	chainCount = 0
	importChainID = []
	importChainOrderList = []
	
	
	print ("Finished Importing!")



def atomAction():
	print("atom_action")
	for obj in bpy.data.objects:
		if obj.BBInfo:
			obj.select = True
			bpy.context.scene.objects.active = obj
			actionName = str(obj.name + "Action")
			if actionName in bpy.data.actions.keys():
				obj.game.actuators['F-Curve'].action = bpy.data.actions[actionName]
				obj.game.actuators['F-Curve'].frame_end = bpy.data.actions[actionName].frame_range[1]
			obj.select = False



# Save the session variables to disk
def sessionSave():
	print("session_save")
	try:
		# if the blender file is not saved yet, do nothing
		if not bpy.data.is_dirty:
			# Serialize the the data and save to disk
			with open(bpy.data.filepath + ".cache","wb") as filedump:
				pickle.dump(pdbIDmodelsDictionary, filedump)
			print("Persistent Session Saved")
		else:
			print("Warning: Blender file needs to be saved first to create persistent session data")
	except Exception as E:
		print("An error occured in sessionSave()")



# Load the saved variables from disk
def sessionLoad(verbose =  False):
	print("session_load")
	global pdbIDmodelsDictionary
	# if the blender file is not saved yet, do nothing
	# if there is already a 'large' number of object in the scene:
	if not bpy.data.is_dirty and len(bpy.data.objects) > 500:
		# try to load serialized data from disk or fail silently
		try:
			with open(bpy.data.filepath + ".cache","rb") as filedump:
				pdbIDmodelsDictionary = pickle.load(filedump)
			select(bpy.data.objects[90].name)    # to select 'something' in the scene
			print("Persistent session loaded")
		except Exception as E:
			print("Warning: Error when loading session cache:", E)



# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



currentActiveObj = ""
oldActiveObj = ""
activeModelRemark = ""
viewFilterOld = ""



class BB2_PANEL_VIEW(types.Panel):	
	bl_label = "BioBlender2 View"
	bl_idname = "BB2_PANEL_VIEW"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBMLPSolventRadius = bpy.props.FloatProperty(attr="BBMLPSolventRadius", name="Solvent Radius", description="Solvent Radius used for Surface Generation", default=1.4, min=0.2, max=5, soft_min=0.4, soft_max=4)
	bpy.types.Scene.BBViewFilter = bpy.props.EnumProperty(attr="BBViewFilter", name="View Filter", description="Select a view mode",
		items=(("1", "Main Chain", ""),
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
	
	@classmethod
	def poll(cls, context):
		global tag
		global currentActiveObj
		global oldActiveObj
		try:
			if bpy.context.scene.objects.active.name != None:
				# do a view update when the selected/active obj changes
				if bpy.context.scene.objects.active.name != oldActiveObj:
					# get the ModelRemark of the active model
					if bpy.context.scene.objects.active.name:
						activeModelRemark = bpy.context.scene.objects.active.name.split("#")[0]
						# load previous sessions from cache
						#if not modelContainer:
							#sessionLoad()
							#print("Sessionload")
						currentActiveObj = activeModelRemark
					oldActiveObj = bpy.context.scene.objects.active.name
		except Exception as E:
			s = "Context Poll Failed: " + str(E)    # VEEEEEERY ANNOYING...
		return (context)



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
bpy.utils.register_class(bb2_view_panel_update)



# depending on view mode, selectively hide certain object based on atom definition
def updateView(residue = None, verbose = False):
	selectedPDBidS = []
	for b in bpy.context.scene.objects:
		if (b.select == True):
			try:
				if(b.bb2_pdbID not in selectedPDBidS):
					t = copy.copy(b.bb2_pdbID)
					selectedPDBidS.append(t)
			except Exception as E:
				str1 = str(E)	# Do not print...
	viewMode = bpy.context.scene.BBViewFilter
	# select amino acid by group
	if residue:
		# skip none atomic object
		if residue.BBInfo:
			seq = PDBString(residue.BBInfo).get("chainSeq")
			id = PDBString(residue.BBInfo).get("chainID")
			for o in bpy.data.objects:
				if(o.BBInfo):
					if((PDBString(o.BBInfo).get("chainSeq") == seq) and (PDBString(o.BBInfo).get("chainID")==id)):
						bpy.data.objects[o.name].select=True
					else:
						bpy.data.objects[o.name].select=False
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
						str2 = str(E)	# Do not print...
				tID = copy.copy(id)
				setup(setupPDBid = tID)
				print("first setup made")
				surface(sPid = tID)
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
				if re.search("#",obj.name):
					line=obj.BBInfo
					line = PDBString(line)
					elementName = line.get("element")
					atomName = line.get("name")
					# hide all
					if viewMode == "0":
						obj.hide = True
						obj.hide_render = True
					# Main Chain Only
					elif viewMode == "1":
						if not (atomName == N or atomName == C or (atomName == CA and elementName != CA) or (atomName in NucleicAtoms) or (atomName in NucleicAtoms_Filtered)):
							obj.hide = True
							obj.hide_render = True
					# Main Chain and Side Chain Only
					elif viewMode == '2' and elementName ==  H:
						obj.hide = True
						obj.hide_render = True
					# Main Chain and Side Chain Only and H, everything.
					elif viewMode == '4':
						obj.hide = True
						obj.hide_render = True
		except Exception as E:
			str5 = str(E)	# Do nothing


def setup(verbose = False, clear = True, setupPDBid = 0):
	# PDB Path is retrieved from parent EMPTY
	pE = None
	for o1 in bpy.context.scene.objects:
		try:
			if(o1.bb2_pdbID == setupPDBid):
				if(o1.bb2_objectType == "PDBEMPTY"):
					pE = copy.copy(o1.name)
		except Exception as E:
			str3 = str(E)	# Do not print...
	print("pE: " + str(pE))
	PDBPath = abspath(bpy.data.objects[pE].bb2_pdbPath)
	print("pdppath: " + str(PDBPath))
	
	if clear:
		if opSystem=="linux":
			if os.path.isdir(quotedPath(homePath+"tmp"+ os.sep)):
				shutil.rmtree(quotedPath(homePath+"tmp" + os.sep))
				os.mkdir(quotedPath(homePath+"tmp" + os.sep))
			else:
				os.mkdir(quotedPath(homePath+"tmp" + os.sep))
		elif opSystem=="darwin":
			if os.path.isdir(quotedPath(homePath+"tmp"+ os.sep)):
				shutil.rmtree(quotedPath(homePath+"tmp" + os.sep))
				os.mkdir(quotedPath(homePath+"tmp" + os.sep))
			else:
				os.mkdir(quotedPath(homePath+"tmp" + os.sep))
		else:
			if os.path.isdir(r"\\?\\" + homePath+"tmp"+ os.sep):
				#shutil.rmtree(r"\\?\\" + homePath+"tmp" + os.sep, ignore_errors=True)
				#os.mkdir(r"\\?\\" + homePath+"tmp")
				print("There is a TMP folder!")
			else:
				#os.mkdir(r"\\?\\" + homePath+"tmp" + os.sep)
				print("Trying to making dir on Win (no TMP folder)...")
				os.mkdir(r"\\?\\" + homePath+"tmp")
	
	if opSystem=="linux":
		shutil.copy(PDBPath, quotedPath(homePath+"tmp" + os.sep + "original.pdb"))
	elif opSystem=="darwin":
		shutil.copy(PDBPath, quotedPath(homePath+"tmp" + os.sep + "original.pdb"))
	else:
		print("Precopy")
		shutil.copy(r"\\?\\" + PDBPath, r"\\?\\" + homePath+"tmp" + os.sep + "original.pdb")
	
	print("Exporting PDB...")
	exportPDB(tag=bpy.data.objects[pE].name.split("#")[0], sPid = setupPDBid)
		
	# clear zero-user datablocks
	#try:
	#	if True:
	#		for datablock in bpy.data.meshes:
	#			if datablock.users == 0:
	#				bpy.data.meshes.remove(datablock)
	#		for datablock in bpy.data.curves:
	#				if datablock.users == 0:
	#					bpy.data.curves.remove(datablock)
	#		for datablock in bpy.data.objects:
	#			if datablock.users == 0:
	#				bpy.data.objects.remove(datablock)
	#except Exception as E:
	#	print("Warning: an error occured in setup while clearing zero-user datablocks")
	print("Setup is complete!")




# export scene to PDB file; if no path is specified, it writes to tmp.pdb
def exportPDB(path = homePath+"tmp" + os.sep + "tmp.pdb", tag = None, verbose = False, sPid = None):
	print("=============== exporting PDB")
	print("Exporting model '%s' to %s" %(tag, path))
		
	outPath = abspath(path)
	# Questo e' un singolo PDB, di un singolo MODEL (quello corrente), quindi penso si possa procedere in maniera molto semplice...
	#if not tag:	
	#	for model in modelContainer:
	#		tag = model
	#model = modelContainer[tag]
	#ordered = sorted(model.keys())
	print("=======outPath = " + str(outPath))
	with open(outPath, "w") as outFile:
		for o in bpy.data.objects:
			try:
				if((o.bb2_pdbID == sPid) and (o.bb2_objectType=="ATOM")):
					loc = o.location
					info = o.BBInfo
					x = "%8.3f" % loc[0]
					y = "%8.3f" % loc[1]
					z = "%8.3f" % loc[2]
					# convert line to pdbstring class
					line = PDBString(info)
					# clear location column
					line = line.set(30,"                         ")
					# insert new location
					line = line.set(30,x)
					line = line.set(38,y)
					line = line.set(46,z)
					outFile.write (line+"\n")
			except Exception as E:
				str4 = str(E)	# Do nothing...
		outFile.write("ENDMDL"+"\n")



# Import the surface generated from PyMol
def surface(sPid = 0, optName=""):
	res = bpy.context.scene.BBMLPSolventRadius
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
	
	tmpPathO = homePath+"tmp" + os.sep + "surface.pml"
	tmpPathL = "load "+  homePath+"tmp" + os.sep + "tmp.pdb" + "\n"
	tmpPathS = "save " + homePath+"tmp"+os.sep+"tmp.wrl" + "\n"
	
	# 2013-06-28
		#f.write("cmd.move('z',-cmd.get_view()[11])\n")
	
	
	with open(tmpPathO, mode="w") as f:
		f.write("# This file is automatically generated by BioBlender at runtime.\n")
		f.write("# Modifying it manually might not have an effect.\n")
		f.write(tmpPathL)
		f.write('cmd.hide("lines"  ,"tmp")\n')
		f.write('cmd.set("surface_quality"  ,"%s")\n' % quality)
		f.write('cmd.show("surface","tmp")\n')
		f.write('set solvent_radius,'+ str(res) +'\n')
		f.write('cmd.reset()\n')
		f.write('cmd.origin(position=[0,0,0])\n')
		f.write('cmd.center("origin")\n')
		f.write(tmpPathS)
		f.write("quit")
	print("Making Surface using PyMOL")
	
	command = "%s -c -u %s" % (quotedPath(pyMolPath), quotedPath(homePath+"tmp" + os.sep + "surface.pml"))
	
	command = quotedPath(command)
	launch(exeName=command)
	
	bpy.ops.import_scene.x3d(filepath=homePath+"tmp"+os.sep+"tmp.wrl", axis_forward="Y", axis_up="Z")

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



def quotedPath(stringaInput):
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


# launch app in separate process, for better performance on multithreaded computers
def launch(exeName, async = False):
	# try to hide window (does not work recursively)
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
		

def select(obj):
	try:
		ob=bpy.data.objects[obj]
		bpy.ops.object.select_all(action="DESELECT")
		for o in bpy.data.objects:
			o.select = False
		ob.select = True
		bpy.context.scene.objects.active=ob
	except:
		return None
	else:
		return ob


def todoAndviewpointsOLD():
	try:
		if "TODO" in bpy.data.objects.keys():
			bpy.ops.object.select_all(action="DESELECT")
			for o in bpy.data.objects:
				o.select = False
			bpy.context.scene.objects.active = None
			bpy.data.objects['TODO'].select = True
			bpy.context.scene.objects.active = bpy.data.objects['TODO']
			bpy.ops.object.delete(use_global=False)
	except:
		print("Warning: TODOs removing not performed properly...")
	try:
		if "Viewpoint" in bpy.data.objects.keys():
			bpy.ops.object.select_all(action="DESELECT")
			for o in bpy.data.objects:
				o.select = False
			bpy.context.scene.objects.active = None
			bpy.data.objects['Viewpoint'].select = True
			bpy.context.scene.objects.active = bpy.data.objects['Viewpoint']
			bpy.ops.object.delete(use_global=False)
	except:
		print("Warning: VIEWPOINTs removing not performed properly...")

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
# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



geList = []



class BB2_PHYSICS_SIM_PANEL(types.Panel):	
	bl_label = "BioBlender2 Game Engine Sim"
	bl_idname = "BB2_PHYSICS_SIM_PANEL"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBDeltaPhysicRadius = bpy.props.FloatProperty(attr="BBDeltaPhysicRadius", name="Radius", description="Value of radius for collisions in physics engine", default=0.7, min=0.1, max=2, soft_min=.1, soft_max=2)
	bpy.types.Scene.BBRecordAnimation = bpy.props.BoolProperty(attr="BBRecordAnimation", name="RecordAnimation", description="Use the physics engine to calculate protein motion and record the IPO")

	def draw(self, context):
		global activeObj
		global activeobjOld
		scene = context.scene
		layout = self.layout
		r = layout.row()
		r.operator("ops.bb2_operator_ge_refresh")
		r = layout.row()
		split = r.split(percentage=0.50)
		try:
			for m in geList:
				split.label(str(m))
				split.prop(bpy.context.scene.objects[str(m)].game, "physics_type") 
				r = layout.row()
				split = r.split(percentage=0.50)
		except Exception as E:
			print("An error occured in SIM_PANEL.draw while drawing geList")
		r = layout.row()
		split = r.split(percentage=0.50)
		split.prop(scene, "BBRecordAnimation")
		split.prop(scene, "BBDeltaPhysicRadius")
		r = layout.row()
		r.operator("ops.bb2_operator_interactive")


class bb2_operator_interactive(types.Operator):
	bl_idname = "ops.bb2_operator_interactive"
	bl_label = "Run in Game Engine"
	bl_description = "Enter Interactive View Mode"
	def invoke(self, context, event):
		for o in bpy.data.objects:
			try:
				if o.bb2_objectType == "SURFACE":
					o.select = True
					bpy.context.scene.objects.active = o
					bpy.ops.object.delete(use_global=False)
			except Exception as E:
				print("No ShapeIndexedFaceSet in scene (or renamed...)")
		try:
			if(bpy.context.scene.BBViewFilter=="4"):
				bpy.context.scene.BBViewFilter="3"
				updateView()
			geStart()
		except Exception as E:
			s = "Start Game Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_interactive)



class bb2_operator_ge_refresh(types.Operator):
	bl_idname = "ops.bb2_operator_ge_refresh"
	bl_label = "Refresh GE List"
	bl_description = "Refresh GE List"
	def invoke(self, context, event):
		global geList
		geList = []
		for o in bpy.data.objects:
			try:
				bpy.context.scene.render.engine='BLENDER_GAME'
				if(o.bb2_objectType == "PDBEMPTY"):
					pe = copy.copy(o.name)
					geList.append(pe)
			except Exception as E:
				str7 = str(E)	# Do nothing...
		return{'FINISHED'}
bpy.utils.register_class(bb2_operator_ge_refresh)



def geStart():
	tmpFPS = bpy.context.scene.render.fps
	bpy.context.scene.render.fps = 1
	bpy.context.scene.game_settings.fps = bpy.context.scene.render.fps
	bpy.context.scene.game_settings.physics_engine = "BULLET"
	bpy.context.scene.game_settings.logic_step_max = 1
	if bpy.context.vertex_paint_object:
		bpy.ops.paint.vertex_paint_toggle()
	#for i, obj in enumerate(bpy.data.objects):
		#obj.game.radius=bpy.context.scene.BBDeltaPhysicRadius		# Done in createModels! Do not overwrite (Hydrogens problem!)
	#setViewShading("TEXTURED")
	bpy.context.scene.render.engine='BLENDER_GAME'
	bpy.context.scene.game_settings.physics_gravity = 0.0
	# Setting dynamic-static type...
	for m in geList:
		tmpEmpty = bpy.data.objects[str(m)]
		tmpID = copy.copy(tmpEmpty.bb2_pdbID)
		for o in bpy.data.objects:
			try:
				if((o.bb2_pdbID == tmpID) and (o.bb2_objectType == 'ATOM')):
					tmpType = copy.copy(tmpEmpty.game.physics_type)
					o.game.physics_type = str(tmpType)
			except Exception as E:
				str8 = str(E)	# Do nothing...
		tmpEmpty.game.physics_type = "NO_COLLISION"

	# START!
	bpy.ops.view3d.game_start()
	#setViewShading("SOLID")
	bpy.context.scene.render.fps = tmpFPS



# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


class BB2_MLP_PANEL(types.Panel):
	bl_label = "BioBlender2 MLP Visualization"
	bl_idname = "BB2_MLP_PANEL"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBAtomic = bpy.props.EnumProperty(attr="BBAtomic", name="BBAtomic", description="Atomic or Surface MLP", items=(("0", "Atomic", ""), ("1", "Surface", "")), default="0")
	bpy.types.Scene.BBMLPFormula = bpy.props.EnumProperty(attr="BBMLPFormula", name="Formula", description="Select a formula for MLP calculation", items=(("0", "Dubost", ""), ("1", "Testa", ""), ("2", "Fauchere", ""), ("3", "Brasseur", ""), ("4", "Buckingham", "")), default="1")
	bpy.types.Scene.BBMLPGridSpacing = bpy.props.FloatProperty(attr="BBMLPGridSpacing", name="Grid Spacing", description="MLP Calculation step size (Smaller is better, but slower)", default=1, min=0.01, max=20, soft_min=1.4, soft_max=10)
	bpy.types.Scene.BBAtomicMLP = bpy.props.BoolProperty(attr="BBAtomicMLP", name="Atomic MLP", description = "Atomic MLP", default=False)
	def draw(self, context):
		scene = context.scene
		layout = self.layout
		r = layout.row()
		r.prop(scene, "BBAtomic", expand=True)
		r = layout.row()
		if(bpy.context.scene.BBAtomic == "0"):
			r.prop(scene, "BBAtomicMLP")
			r = layout.row()
			r.operator("ops.bb2_operator_atomic_mlp")
		else:
			split = layout.split()
			c = split.column()
			c.prop(scene, "BBMLPFormula")
			c.prop(scene, "BBMLPGridSpacing")
			r = split.row()
			r.scale_y = 2
			r.operator("ops.bb2_operator_mlp")
			split = layout.split()
			r = split.column(align=True)
			r = split.column()
			r.scale_y = 2
			r.operator("ops.bb2_operator_mlp_render")


class bb2_operator_atomic_mlp(types.Operator):
	bl_idname = "ops.bb2_operator_atomic_mlp"
	bl_label = "Atomic MLP"
	bl_description = "Atomic MLP"
	def invoke(self, context, event):
		try:
			selectedPDBidS = []
			for b in bpy.context.scene.objects:
				if (b.select == True):
					try:
						if(b.bb2_pdbID not in selectedPDBidS):
							t = copy.copy(b.bb2_pdbID)
							selectedPDBidS.append(t)
					except Exception as E:
						str1 = str(E)	# Do not print...
			context.user_preferences.edit.use_global_undo = False
			for id in selectedPDBidS:
				bpy.ops.object.select_all(action="DESELECT")
				for o in bpy.data.objects:
					o.select = False
				for obj in bpy.context.scene.objects:
					try:
						if obj.bb2_pdbID == id:
							obj.select = True
					except Exception as E:
						str2 = str(E)	# Do not print...
				tID = copy.copy(id)
				atomicMLP(bpy.context.scene.BBAtomicMLP, tID)
			context.user_preferences.edit.use_global_undo = True
		except Exception as E:
			s = "Generate MLP visualization Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_atomic_mlp)



def atomicMLP(MLPcolor, tID):
	if MLPcolor:	
		for obj in bpy.data.objects:
			try:
				if ((obj.bb2_pdbID==tID) and (obj.bb2_objectType == "ATOM")):
					aminoName = PDBString(obj.BBInfo).get("aminoName")
					name = PDBString(obj.BBInfo).get("name")
					material_this=retrieve_fi_materials(am_name=aminoName,at_name=name)
					obj.material_slots[0].material = bpy.data.materials[material_this]
			except Exception as E:
				str9 = print(str(E))
		print("Atomic MLP Color set")
	else:
		# Original color	
		for obj in bpy.data.objects:
			try:
				if ((obj.bb2_pdbID==tID) and (obj.bb2_objectType == "ATOM")):
					# In BBInfo, the Atom name is the last string
					index = obj.BBInfo.split()[-1]
					obj.material_slots[0].material = bpy.data.materials[index]
			except Exception as E:
				str10 = print(str(E))
		print("Original Atomic Color set")




class bb2_operator_mlp(types.Operator):
	bl_idname = "ops.bb2_operator_mlp"
	bl_label = "Show MLP on Surface"
	bl_description = "Calculate Molecular Lipophilicity Potential on surface"
	def invoke(self, context, event):
		try:
			bpy.context.user_preferences.edit.use_global_undo = False
			selectedPDBidS = []
			for b in bpy.context.scene.objects:
				if (b.select == True):
					try:
						if(b.bb2_pdbID not in selectedPDBidS):
							t = copy.copy(b.bb2_pdbID)
							selectedPDBidS.append(t)
					except Exception as E:
						str1 = str(E)	# Do not print...
			context.user_preferences.edit.use_global_undo = False
			for id in selectedPDBidS:
				bpy.ops.object.select_all(action="DESELECT")
				for o in bpy.data.objects:
					o.select = False
				for obj in bpy.context.scene.objects:
					try:
						if obj.bb2_pdbID == id:
							obj.select = True
					except Exception as E:
						str2 = str(E)	# Do not print...
				tID = copy.copy(id)
				mlp(tID, force = True)
				todoAndviewpoints()
			bpy.context.scene.BBViewFilter = "4"
			bpy.context.user_preferences.edit.use_global_undo = True
		except Exception as E:
			s = "Generate MLP visualization Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_mlp)



class bb2_operator_mlp_render(types.Operator):
	bl_idname = "ops.bb2_operator_mlp_render"
	bl_label = "Render MLP to Surface"
	bl_description = "Visualize Molecular Lipophilicity Potential on surface"
	def invoke(self, context, event):
		try:
			context.user_preferences.edit.use_global_undo = False
			selectedPDBidS = []
			for b in bpy.context.scene.objects:
				if (b.select == True):
					try:
						if((b.bb2_pdbID not in selectedPDBidS) and (b.bb2_objectType=="SURFACE")):
							t = copy.copy(b.bb2_pdbID)
							selectedPDBidS.append(t)
					except Exception as E:
						str1 = str(E)	# Do not print...
			context.user_preferences.edit.use_global_undo = False
			for id in selectedPDBidS:
				tID = copy.copy(id)
				mlpRender(tID)
				todoAndviewpoints()
			context.scene.BBViewFilter = "4"
			context.user_preferences.edit.use_global_undo = True
		except Exception as E:
			s = "Generate MLP visualization Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_mlp_render)



# do MLP visualization
def mlp(tID, force):
	global dxCache
	global dxData
	global dimension
	global origin
	global delta
	scene = bpy.context.scene
	formula = bpy.context.scene.BBMLPFormula
	spacing = bpy.context.scene.BBMLPGridSpacing


	scene.render.engine = 'BLENDER_RENDER'

	def getVar(rawID):
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
			mmm = dxData[cellz + ((celly)*dimz) + ((cellx)*dimz*dimy)]
			pmm = dxData[cellz + ((celly)*dimz) + ((cellx+1)*dimz*dimy)]
			mpm = dxData[cellz + ((celly+1)*dimz) + ((cellx)*dimz*dimy)]
			mmp = dxData[cellz+1 + ((celly)*dimz) + ((cellx)*dimz*dimy)]
			ppm = dxData[cellz + ((celly+1)*dimz) + ((cellx+1)*dimz*dimy)]
			mpp = dxData[cellz+1 + ((celly+1)*dimz) + ((cellx)*dimz*dimy)]
			pmp = dxData[cellz+1 + ((celly)*dimz) + ((cellx+1)*dimz*dimy)]
			ppp = dxData[cellz+1 + ((celly+1)*dimz) + ((cellx+1)*dimz*dimy)]
			wxp = 1.0-(fabs(v[0] - (origin[0] + (deltax*(cellx+1)))))/deltax
			wxm = 1.0-(fabs(v[0] - (origin[0] + (deltax*(cellx)))))/deltax
			wyp = 1.0-((v[1] - (origin[1] + (deltay*(celly+1)))))/deltay
			wym = 1.0-(fabs(v[1] - (origin[1] + (deltay*(celly)))))/deltay
			wzp = 1.0-(fabs(v[2] - (origin[2] + (deltaz*(cellz+1)))))/deltaz
			wzm = 1.0-(fabs(v[2] - (origin[2] + (deltaz*(cellz)))))/deltaz
			onz_xmym = (wzp*mmp)+(wzm*mmm)
			onz_xpym = (wzp*pmp)+(wzm*pmm)
			onz_xmyp = (wzp*mpp)+(wzm*mpm)
			onz_xpyp = (wzp*ppp)+(wzm*ppm)
			onx_yp = (wxp*onz_xpyp)+(wxm*onz_xmyp)
			onx_ym = (wxp*onz_xpym)+(wxm*onz_xmym)
			val = (wyp*onx_yp)+(wym*onx_ym)
			dxCache[rawID] = val

		# map values
		if(val >= 0.0):
			val=(val+1.0)/2.0
		else:
			val=(val+3.0)/6.0
		return [val,val,val]

	if force:
		setup(setupPDBid = tID)
		# select formula for PyMLP script
		if formula == "0": method = "dubost"
		elif formula == "1": method = "testa"
		elif formula == "2": method = "fauchere"
		elif formula == "3": method = "brasseur"
		elif formula == "4": method = "buckingham"

		# Launch this in a separate process
		if opSystem == "linux":
			command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "pyMLP-1.0" + os.sep + "pyMLP.py"))
			command = quotedPath(command)
			launch(exeName = command)
		elif opSystem == "darwin":
			command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "pyMLP-1.0" + os.sep + "pyMLP.py"))
			command = quotedPath(command)
			launch(exeName = command)
		print("Running PyMLP")
		global pyPath
		if not pyPath:
			pyPath = "python"
		command = "%s %s -i %s -m %s -s %f -o %s -v" % (quotedPath(pyPath), quotedPath(homePath + "bin" + os.sep + "pyMLP-1.0" + os.sep + "pyMLP.py"), quotedPath(homePath + "tmp" + os.sep + "tmp.pdb"), method, spacing, quotedPath(homePath + "tmp" + os.sep + "tmp.dx"))
		
		p = launch(exeName=command, async = True)
		
		
		print("PyMLP command succeded")
		surface(sPid = tID, optName="mlpSurface")

		wait(p)

		# purge the all old data
		dxCache = {}
		dxData = []			# list[n] of Potential data
		dimension = []		# list[3] of dx grid store.dimension
		origin = []			# list[3] of dx grid store.origin
		delta = []			# list[3] of dx grid store.increment

		print("Loading MLP values into Blender")
		
		try:
			tmpPathO = homePath + "tmp"+os.sep+"tmp.dx"
			with open(tmpPathO) as dx:
				for line in dx:
					# skip comments starting with #
					if line[0] == "#": continue
					if not dimension:
						#get the store.dimension and convert to integer
						dim = line.split()[-3:]
						dimension = [int(d) for d in dim]
						size = dimension[0]*dimension[1]*dimension[2]
						continue

					if not origin:
						# get the store.origin
						org = line.split()[-3:]
						origin = [float(o) for o in org]
						continue
						
					if not delta:
						# get the increment delta
						x = float(line.split()[-3:][0])
						line = dx.readline()
						y = float(line.split()[-3:][1])
						line = dx.readline()
						z = float(line.split()[-3:][2])
						delta = [x,y,z]

						# ignore more garbage lines
						dx.readline()
						dx.readline()
						continue

					# load as much data as we should, ignoring the rest of the file
					if (len(dxData) >= size):
						break

					# Load the data
					# Convert dx data from str to float, then save to list
					[dxData.append(float(coord)) for coord in line.split()]
		except Exception as E:
			print("An error occured in MLP while loading values into Blender; be careful; " + str(E))

	# quick and dirty update starts here
	if dxData:
		ob = bpy.data.objects['mlpSurface']
		ob.name = "SURFACE"
		ob.bb2_pdbID = copy.copy(tID)
		ob.bb2_objectType = "SURFACE"
		ob.select = True
		bpy.context.scene.objects.active = ob
		
		if not bpy.context.vertex_paint_object:
			bpy.ops.paint.vertex_paint_toggle()
		try:
			bpy.ops.object.editmode_toggle()
			bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
			bpy.ops.object.editmode_toggle()
			bpy.ops.object.shade_smooth()
		except Exception as E:
			print("Error in MLP: remove doubles and shade smooth failed; " + str(E))
			
		
		
		try:
			color_map_collection = ob.data.vertex_colors
			if len(color_map_collection) == 0:
				color_map_collection.new()
			color_map = color_map_collection['Col']
			i = 0
			for poly in ob.data.polygons:
				for idx in poly.loop_indices:
					#tmp = ((0.21 * color_map.data[i].color[0]) + (0.71 * color_map.data[i].color[1]) + (0.07 * color_map.data[i].color[2]))
					tmp = (color_map.data[i].color[0] + color_map.data[i].color[1] + color_map.data[i].color[2]) / 3
					color_map.data[i].color = [tmp, tmp, tmp]
					i += 1
			#color_map_collection['Col'] = color_map
			#ob.data.vertex_colors = color_map_collection['Col']
		except Exception as E:
			print("Error new color map collection; " + str(E))
		
		#try:
		#	ob.data.update(calc_tessface=True)
		#except Exception as E:
		#	print("Error in MLP: ob.data.update tessface failed; " + str(E))
		#try:
		#	vColor0 = []
		#	vColor1 = []
		#	vColor2 = []
		#	for f in ob.data.tessfaces:
		#		vColor0.extend(getVar(f.vertices_raw[0]))
		#		vColor1.extend(getVar(f.vertices_raw[1]))
		#		vColor2.extend(getVar(f.vertices_raw[2]))
		#	for i in range(len(ob.data.vertex_colors[0].data)):
		#		#tmp = ((0.21 * vColor0[i]) + (0.71 * vColor1[i]) + (0.07 * vColor2[i]))
		#		tmp = (vColor0[i] + vColor1[i] + vColor2[i]) / 3
		#		ob.data.vertex_colors[0].data[i].color = (tmp, tmp, tmp)	
		#except Exception as E:
		#	print("Error in MLP: tessfaces vColor extend failed; " + str(E))
		
		


		try:
			me = ob.data
		except Exception as E:
			print("Error in MLP: me = ob.data failed; " + str(E))
		
		try:
			bpy.ops.paint.vertex_paint_toggle()
			me.use_paint_mask = False 
			bpy.ops.paint.vertex_color_smooth()
			bpy.ops.paint.vertex_paint_toggle()
		except Exception as E:
			print("Error in MLP: vertex color smooth failed; " + str(E))
			
		try:
			# needed to make sure VBO is up to date
			ob.data.update()
		except Exception as E:
			print("Error in MLP: VBO ob.data.update failed; " + str(E))
			
		try:
			for area in bpy.context.screen.areas:
				if area.type == 'VIEW_3D':
					area.spaces[0].viewport_shade = "TEXTURED"
		except Exception as E:
			print("Error in MLP: view3D viewport shade textured failed; " + str(E))
			
	try:
		for obj in bpy.context.scene.objects:
			if obj.BBInfo:
				obj.hide = True
				obj.hide_render = True
	except Exception as E:
		print("Error in MLP: obj.BBInfo")
	print("MLP function completed")
	
	
def mlpRender(tID):
	print("MLP RENDER Start")
	scene = bpy.context.scene
	# Stop if no surface is found
	
	scene.render.engine = 'BLENDER_RENDER'
	
	for obj in bpy.data.objects:
		try:
			if((obj.bb2_pdbID == tID) and (obj.bb2_objectType=="SURFACE")):
				surfaceName = str(copy.copy(obj.name))
		except Exception as E:
			print(str(E))
	ob = bpy.data.objects[surfaceName]

	bpy.ops.object.select_all(action="DESELECT")
	for o in bpy.data.objects:
		o.select = False
	bpy.context.scene.objects.active = None
	bpy.data.objects[surfaceName].select = True
	bpy.context.scene.objects.active = bpy.data.objects[surfaceName]
	
	if not ob:
		raise Exception("No MLP Surface Found, select surface view first")

	# Stop if no dx data is loaded
	if not dxData:
		raise Exception("No MLP data is loaded.  Run MLP calculation first")

	# create image data block
	try:
		print("MLP Render first time: False")
		firstTime = False
		image = bpy.data.images["MLPBaked"]
	except:
		print("MLP Render first time: True")
		firstTime = True
		image = bpy.data.images.new(name="MLPBaked", width=2048, height=2048)

	# set material
	if firstTime:
		mat = bpy.data.materials.new("matMLP")
		mat.use_shadeless=True
		mat.use_vertex_color_paint=True
		ob.data.materials.append(mat)
	else:
		mat = bpy.data.materials["matMLP"]
		mat.use_shadeless=True
		mat.use_vertex_color_paint=True
		if not ob.data.materials:
			ob.data.materials.append(mat)
			
	print("Baking MLP textures")

	# save and bake
	image.source = "GENERATED"
	image.generated_height = 2048
	image.generated_width = 2048
	
	if not ob.data.uv_textures:	bpy.context.active_object.data.uv_textures.new()
	if bpy.context.mode != "EDIT":
		bpy.ops.object.editmode_toggle()
	# ====
	for uv in ob.data.uv_textures[0].data:
		uv.image=image

	bpy.data.screens['UV Editing'].areas[1].spaces[0].image = bpy.data.images['MLPBaked']

	bpy.ops.uv.smart_project(angle_limit=66, island_margin=0, user_area_weight=0)
	bpy.context.scene.render.bake_type = 'TEXTURE'	
	
	bpy.context.scene.render.use_raytrace = False
	print("===== BAKING... =====")
	bpy.ops.object.bake_image()
	print("=====          ... BAKED! =====")
	bpy.context.scene.render.use_raytrace = True
	
	if opSystem == "linux":
		os.chdir(quotedPath(homePath + "tmp" + os.sep))
	elif opSystem == "darwin":
		os.chdir(quotedPath(homePath + "tmp" + os.sep))
	else:
		os.chdir(r"\\?\\" + homePath + "tmp" + os.sep)

	print("Image Save Render")
	image.save_render(homePath + "tmp" + os.sep + "MLPBaked.png")
	# copy the needed files
	print("Copy the needed files")
	uriSource = homePath +"data" + os.sep + "noise.png"
	uriDest = homePath + "tmp" + os.sep + "noise.png"
	
	if opSystem=="linux":
		shutil.copy(uriSource, uriDest)
	elif opSystem=="darwin":
		shutil.copy(uriSource, uriDest)
	else:
		shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)
		
	
	uriSource = homePath + "data" + os.sep + "composite.blend"
	uriDest = homePath + "tmp" + os.sep + "composite.blend"
	
	if opSystem=="linux":
		shutil.copy(uriSource, uriDest)
	elif opSystem=="darwin":
		shutil.copy(uriSource, uriDest)
	else:
		shutil.copy(r"\\?\\" + uriSource, r"\\?\\" + uriDest)
			
	
	# render out composite texture
	if blenderPath == "":
		bP = quotedPath(str(os.environ['PWD']) + os.sep + "blender")
		command = "%s -b %s -f 1" % (quotedPath(bP), quotedPath(homePath +"tmp" + os.sep + "composite.blend"))
	else:
		command = "%s -b %s -f 1" % (quotedPath(blenderPath), quotedPath(homePath +"tmp" + os.sep + "composite.blend"))
	
	launch(exeName=command)
	
	# set materials
	mat.specular_shader=("TOON")
	mat.specular_toon_size=0.2
	mat.specular_toon_smooth=0.0
	mat.specular_intensity=0.0
	mat.use_shadeless=False
	mat.use_vertex_color_paint=False
	mat.use_shadows=False

	# setup textures
	if firstTime:
		img_bump = bpy.data.images.load(homePath +"tmp" + os.sep + "0001.png")
		tex_bump = bpy.data.textures.new('bump', type="IMAGE")
		tex_bump.image = img_bump
		mtex = mat.texture_slots.add()
		mtex.texture = tex_bump
		mtex.texture_coords = 'UV'
		mtex.use_map_normal = True
		mtex.use_map_color_diffuse = False
		bpy.data.textures["bump"]
		mat.texture_slots[0].normal_factor=1
		img_baked = bpy.data.images.load(homePath +"tmp" + os.sep + "MLPBaked.png")
		tex_spec = bpy.data.textures.new('specular', type="IMAGE")
		tex_spec.image = img_baked
		tex_spec.contrast = 4.0
		mtex = mat.texture_slots.add()
		mtex.texture = tex_spec
		mtex.texture_coords = 'UV'
		mtex.use_map_color_diffuse = False
		mtex.use_map_specular = True
		mat.texture_slots[1].use_rgb_to_intensity=True
		mat.texture_slots[1].default_value=1
		
	# refresh all images
	for img in bpy.data.images:
		img.reload()

	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			area.spaces[0].viewport_shade = "SOLID"
	bpy.ops.object.editmode_toggle()
	
	ob.data.materials[0] = mat
	
	ob.data.materials[0].specular_toon_smooth = 0.3
	ob.data.materials[0].texture_slots[0].normal_factor=1
	ob.data.materials[0].texture_slots[1].default_value=1
	ob.data.materials[0].texture_slots[1].specular_factor=0.1
	
	bpy.ops.paint.vertex_paint_toggle()
	meshData = ob.data
	vColLayer0 = meshData.vertex_colors[0]
	for vCol in vColLayer0.data:
		vCol.color = Color((((vCol.color[0]-0.5)*0.6)+0.5, ((vCol.color[1]-0.5)*0.6)+0.5, ((vCol.color[2]-0.5)*0.6)+0.5))
	meshData.update()
	bpy.ops.paint.vertex_paint_toggle()

	ob.data.materials[0].use_vertex_color_paint = True
	
	for obj in bpy.context.scene.objects:
		if obj.BBInfo:
			obj.hide = True
			obj.hide_render = True


# Wait until process finishes
def wait(process):
	while process.poll() == None:
		time.sleep(0.1)
		# needed if io mode is set to subprocess.PIPE to avoid deadlock
		# process.communicate()
# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



class BB2_EP_PANEL(types.Panel):
	bl_label = "BioBlender2 EP Visualization"
	bl_idname = "BB2_EP_PANEL"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBForceField = bpy.props.EnumProperty(attr="BBForceField", name="ForceField", description="Select a forcefield type for EP calculation",
	items=(("0", "amber", ""),
	("1", "charmm", ""),
	("2", "parse", ""),
	("3", "tyl06", ""),
	("4", "peoepb", ""),
	("5", "swanson", "")),
	default="0")
	bpy.types.Scene.BBEPIonConc = bpy.props.FloatProperty(attr="BBEPIonConc", name="Ion concentration", description="Ion concentration of the solvent", default=0.15, min=0.01, max=1, soft_min=0.01, soft_max=1)
	bpy.types.Scene.BBEPGridStep = bpy.props.FloatProperty(attr="BBEPGridStep", name="Grid Spacing", description="EP Calculation step size (Smaller is better, but slower)", default=1, min=0.01, max=10, soft_min=0.5, soft_max=5)
	bpy.types.Scene.BBEPMinPot = bpy.props.FloatProperty(attr="BBEPMinPot", name="Minimum Potential", description="Minimum Potential on the surface from which start the calculation of the field lines", default=0.0, min=0.0, max=10000, soft_min=0, soft_max=1000)
	bpy.types.Scene.BBEPNumOfLine = bpy.props.FloatProperty(attr="BBEPNumOfLine", name="n EP Lines*eV/Å² ", description="Concentration of lines", default=0.05, min=0.01, max=0.5, soft_min=0.01, soft_max=0.1, precision=3, step=0.01)
	bpy.types.Scene.BBEPParticleDensity = bpy.props.FloatProperty(attr="BBEPParticleDensity", name="Particle Density", description="Particle Density", default=1, min=0.1, max=10.0, soft_min=0.1, soft_max=5.0)

	def draw(self, context):
		scene = bpy.context.scene
		layout = self.layout
		split = layout.split()
		c = split.column()
		c.prop(scene, "BBForceField")
		c = c.column(align=True)
		c.label("Options:")
		c.prop(scene, "BBEPIonConc")
		c.prop(scene, "BBEPGridStep")
		c.prop(scene, "BBEPMinPot")
		c.prop(scene, "BBEPNumOfLine")
		c.prop(scene, "BBEPParticleDensity")
		c = split.column()
		c.scale_y = 2
		c.operator("ops.bb2_operator_ep")
		c.operator("ops.bb2_operator_ep_clear")



class bb2_operator_ep(types.Operator):
	bl_idname = "ops.bb2_operator_ep"
	bl_label = "Show EP"
	bl_description = "Calculate and Visualize Electric Potential"
	def invoke(self, context, event):
		try:
			bpy.context.user_preferences.edit.use_global_undo = False
			cleanEPObjs()
			scenewideEP(animation = False)
			bpy.context.scene.BBViewFilter = "4"
			bpy.context.user_preferences.edit.use_global_undo = True
			todoAndviewpoints()
		except Exception as E:
			s = "Generate EP Visualization Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_ep)



class bb2_operator_ep_clear(types.Operator):
	bl_idname = "ops.bb2_operator_ep_clear"
	bl_label = "Clear EP"
	bl_description = "Clear the EP Visualization"
	def invoke(self, context, event):
		try:
			bpy.context.user_preferences.edit.use_global_undo = False
			cleanEPObjs()
			bpy.context.user_preferences.edit.use_global_undo = True
			todoAndviewpoints()
		except Exception as E:
			s = "Clear EP Visualization Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_ep_clear)



# delete EP related objects
def cleanEPObjs(deletionList = None):
	global epOBJ
	bpy.ops.object.select_all(action="DESELECT")
	for o in bpy.data.objects:
		o.select = False
	# use deletionList if supplied
	if deletionList:
		for obj in deletionList:
			obj.select = True
	# otherwise delete everything in EPOBJ list
	else:
		for list in epOBJ:
			for obj in list:
				obj.select = True
		epOBJ = []
	# call delete operator
	bpy.ops.object.delete()



def scenewideEP(animation):
	global epOBJ
	scene = bpy.context.scene
	
	scenewideSetup()	# In BB1, it was a call to "Setup"; now, Setup is 'per id', so we need a scenewide setup function...
	
	if (not animation):
		print("Generating scenewide surface")
		scenewideSurface()
	
	if (not animation) or (bpy.context.scene.frame_current % 5 == 1):
		print("Generating EP Curves")
		tmpPathOpen = homePath + "tmp" + os.sep + "scenewide.pdb" # former tmp.pdb
		
		with open(tmpPathOpen, "r") as file:
			for line in file:
				line = line.replace("\n", "")
				line = line.replace("\r", "")
				line = PDBString(line)
				tag = line.get("tag")
				
				# if tag is ATOM, load column data
				if(tag == "ATOM" or tag == "HETATM"):
					# check for element type
					if line.get("element") == H:
						extraCommand = "--assign-only"
						break
		
		# select the forcefield
		forcefield = bpy.context.scene.BBForceField
		if forcefield == "0": method = "amber"
		elif forcefield == "1": method = "charmm"
		elif forcefield == "2": method = "parse"
		elif forcefield == "3": method = "tyl06"
		elif forcefield == "4": method = "peoepb"
		elif forcefield == "5": method = "swanson"
		
		
		print("Running PDB2PQR")
		if opSystem == "linux":
			os.chdir(quotedPath(homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep))
		elif opSystem == "darwin":
			os.chdir(quotedPath(homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep))
		else:
			os.chdir(r"\\?\\" + homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep)
		tmpPathPar1 = "python"
		tmpPathPar2 = homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep + "pdb2pqr.py"
		tmpPathPar3 = homePath + "tmp" + os.sep + "scenewide.pqr"
		tmpPathPar4 = homePath + "tmp" + os.sep + "scenewide.pdb"
		if opSystem == "linux":
			command = "%s %s --apbs-input --ff=%s %s %s" % (tmpPathPar1, tmpPathPar2, method, tmpPathPar4, tmpPathPar3)
		elif opSystem == "darwin":
			command = "%s %s --apbs-input --ff=%s %s %s" % (tmpPathPar1, tmpPathPar2, method, tmpPathPar4, tmpPathPar3)
		else:
			command = "%s %s --apbs-input --ff=%s %s %s" % (quotedPath(tmpPathPar1), quotedPath(tmpPathPar2), method, quotedPath(tmpPathPar4), quotedPath(tmpPathPar3))
		launch(exeName=command)
		
		
		print("Running inputgen.py")
		tmp1PathPar1 = "python"
		tmp1PathPar2 = homePath + "bin" + os.sep + "pdb2pqr-1.6" + os.sep + "src" + os.sep + "inputgen.py"
		tmp1PathPar3 = homePath + "tmp" + os.sep + "scenewide.pqr"
		if opSystem == "linux":
			command = "%s %s --istrng=%f --method=auto --space=%f %s" % (tmp1PathPar1, tmp1PathPar2, bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, tmp1PathPar3)
		elif opSystem == "darwin":
			command = "%s %s --istrng=%f --method=auto --space=%f %s" % (tmp1PathPar1, tmp1PathPar2, bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, tmp1PathPar3)
		else:
			command = "%s %s --istrng=%f --method=auto --space=%f %s" % (quotedPath(tmp1PathPar1), quotedPath(tmp1PathPar2), bpy.context.scene.BBEPIonConc, bpy.context.scene.BBEPGridStep, quotedPath(tmp1PathPar3))
		launch(exeName=command)
		
		
		print("Running APBS")
		try:
			if opSystem == "linux":
				shutil.copy(quotedPath(homePath + "bin" + os.sep + "apbs-1.2.1" + os.sep + "apbs.exe"), quotedPath(homePath + "tmp" + os.sep + "apbs.exe"))
			elif opSystem == "darwin":
				shutil.copy(quotedPath(homePath + "bin" + os.sep + "apbs-1.2.1" + os.sep + "darwin_apbs"), quotedPath(homePath + "tmp" + os.sep + "darwin_apbs"))
			else:
				shutil.copy(r"\\?\\" + homePath + "bin" + os.sep + "apbs-1.2.1" + os.sep + "apbs.exe", r"\\?\\" + homePath + "tmp" + os.sep + "apbs.exe")
		except Exception as E:
			s = "APBS COPY failed: " + str(E)
			print(s)
		if opSystem == "linux":
			oPath = homePath + "tmp" + os.sep + "scenewide.in"
			f = open(oPath, "r")
			lines = f.readlines()
			f.close()
			lines[1] = "    mol pqr " + quotedPath(homePath + "tmp" + os.sep + "scenewide.pqr") + "\n"
			f = open(oPath, "w")
			f.writelines(lines)
			f.close()
			command = "chmod 755 %s" % (quotedPath(homePath + "tmp" + os.sep + "apbs.exe"))
			command = quotedPath(command)
			launch(exeName = command)
			command = homePath + "tmp" + os.sep + "apbs.exe" + " " + homePath + "tmp" + os.sep + "scenewide.in"
		elif opSystem == "darwin":
			oPath = homePath + "tmp" + os.sep + "scenewide.in"
			f = open(oPath, "r")
			lines = f.readlines()
			f.close()
			lines[1] = "    mol pqr " + quotedPath(homePath + "tmp" + os.sep + "scenewide.pqr") + "\n"
			f = open(oPath, "w")
			f.writelines(lines)
			f.close()
			command = "chmod 755 %s" % (quotedPath(homePath + "tmp" + os.sep + "darwin_apbs"))
			command = quotedPath(command)
			launch(exeName = command)
			command = homePath + "tmp" + os.sep + "darwin_apbs" + " " + homePath + "tmp" + os.sep + "scenewide.in"
		else:
			oPath = homePath + "tmp" + os.sep + "scenewide.in"
			f = open(oPath, "r")
			lines = f.readlines()
			f.close()
			lines[1] = "    mol pqr " + quotedPath(homePath + "tmp" + os.sep + "scenewide.pqr") + "\n"
			f = open(oPath, "w")
			f.writelines(lines)
			f.close()
			command = quotedPath(homePath + "tmp" + os.sep + "apbs.exe") + " " + quotedPath(homePath + "tmp" + os.sep + "scenewide.in")
		p = launch(exeName=command, async = True)
		print("APBS Ok")
		
		# sync
		wait(p)

		# write pot dx pot problems: writes the .dx file in user home path...
		print("============ POT DX POT COPY ================")
		envBoolean = False
		try:
			if opSystem == "linux":
				tmpP = quotedPath(homePath + "tmp" + os.sep + "pot.dx")
				if os.path.isfile(tmpP):
					envBoolean = True
					print("pot.dx in current directory; won't search in HOME or VIRTUALSTORE folders...")
			elif opSystem == "darwin":
				tmpP = quotedPath(homePath + "tmp" + os.sep + "pot.dx")
				if os.path.isfile(tmpP):
					envBoolean = True
					print("pot.dx in current directory; won't search in HOME or VIRTUALSTORE folders...")
		except Exception as E:
			s = "pot.dx output rewrite failed in tmp.in, will search in some folders...: " + str(E)
			print(s)
		if envBoolean == False:
			if opSystem == "linux":
				print("user home: ", os.path.expanduser("~"))
				try:
					print("BB stays here: ")
					homeutente = os.path.expanduser("~")
					shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/pot.dx"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/pot.dx"))
					shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/io.mc"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/io.mc"))
				except Exception as E:
					s = "pot.dx not found in HOME: " + str(E)
					print(s)
			elif opSystem == "darwin":
				print("user home: ", os.path.expanduser("~"))
				try:
					print("BB stays here: ")
					homeutente = os.path.expanduser("~")
					shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/pot.dx"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/pot.dx"))
					shutil.move(quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/bin/pdb2pqr-1.6/io.mc"), quotedPath(homeutente + "/.config/blender/2.67/scripts/addons/BioBlender1/tmp/io.mc"))
				except Exception as E:
					s = "pot.dx not found in HOME: " + str(E)
					print(s)
			else:
				try:
					envHome = str(os.environ['USERPROFILE'])
					print("envHome: " + envHome)
					shutil.move(r"\\?\\" + envHome + os.sep + "pot.dx", r"\\?\\" + homePath + "tmp" + os.sep + "pot.dx")
					shutil.move(r"\\?\\" + envHome + os.sep + "io.mc", r"\\?\\" + homePath + "tmp" + os.sep + "io.mc")
					envBoolean = True
				except Exception as E:
					s = "No pot.dx in HOME: " + str(E)
					print(s)
				if not envBoolean:
					print("Win problem; will search in Windows...")
					try:
						envHome = "C:" + os.sep + "Windows"
						print("envHome: " + envHome)
						shutil.move(envHome + os.sep + "pot.dx", homePath + "tmp" + os.sep + "pot.dx")
						shutil.move(envHome + os.sep + "io.mc", homePath + "tmp" + os.sep + "io.mc")
						envBoolean = True
					except Exception as E:
						s = "Windows home failed too; no pot.dx, sorry: " + str(E)
						print(s)
				if not envBoolean:
					print("Win problem; will search in AppData - Local - VirtualStore...")
					try:
						envHome = str(os.environ['USERPROFILE']) + os.sep + "AppData" + os.sep + "Local" + os.sep + "VirtualStore"
						print("envHome: " + envHome)
						shutil.move(envHome + os.sep + "pot.dx", homePath + "tmp" + os.sep + "pot.dx")
						shutil.move(envHome + os.sep + "io.mc", homePath + "tmp" + os.sep + "io.mc")
						envBoolean = True
					except Exception as E:
						s = "VirtualStore failed too; no pot.dx, sorry: " + str(E)
						print(s)
				if not envBoolean:
					print("Win problem; will search in AppData - Local - VirtualStore - Windows...")
					try:
						envHome = str(os.environ['USERPROFILE']) + os.sep + "AppData" + os.sep + "Local" + os.sep + "VirtualStore" + os.sep + "Windows"
						print("envHome: " + envHome)
						shutil.move(envHome + os.sep + "pot.dx", homePath + "tmp" + os.sep + "pot.dx")
						shutil.move(envHome + os.sep + "io.mc", homePath + "tmp" + os.sep + "io.mc")
						envBoolean = True
					except Exception as E:
						s = "VirtualStore - Windows failed too; no pot.dx, sorry: " + str(E)
						print(s)
						print("=========== SORRY: CANNOT FIND POT.DX ============")
		print ("Saving obj")
		exportOBJ(homePath +"tmp" + os.sep + "scenewide")

		if len(epOBJ) >= maxCurveSet:
			# delete the oldest curve-sets out of the list.
			epOBJ.reverse()
			deletionList = epOBJ.pop()			
			cleanEPObjs(deletionList)
			epOBJ.reverse()

		print("Running Scivis")
		if opSystem == "linux":
			command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "scivis" + os.sep + "SCIVIS.exe"))
			command = quotedPath(command)
			launch(exeName = command)
			command = "%s %s %s %s %f %f %f %f %f" % (homePath + "bin" + os.sep + "scivis" + os.sep + "SCIVIS.exe", homePath + "tmp" + os.sep + "scenewide.obj", homePath + "tmp" + os.sep + "pot.dx", homePath + "tmp" + os.sep + "tmp.txt", bpy.context.scene.BBEPNumOfLine/10, bpy.context.scene.BBEPMinPot, 45, 1, 3)
		elif opSystem == "darwin":
			command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "scivis" + os.sep + "darwin_SCIVIS"))
			command = quotedPath(command)
			launch(exeName = command)
			command = "%s %s %s %s %f %f %f %f %f" % (homePath + "bin" + os.sep + "scivis" + os.sep + "darwin_SCIVIS", homePath + "tmp" + os.sep + "scenewide.obj", homePath + "tmp" + os.sep + "pot.dx", homePath + "tmp" + os.sep + "tmp.txt", bpy.context.scene.BBEPNumOfLine/10, bpy.context.scene.BBEPMinPot, 45, 1, 3)
		else:
			command = "%s %s %s %s %f %f %f %f %f" % (quotedPath(homePath + "bin" + os.sep + "scivis" + os.sep + "SCIVIS.exe"), quotedPath(homePath + "tmp" + os.sep + "scenewide.obj"), quotedPath(homePath + "tmp" + os.sep + "pot.dx"), quotedPath(homePath + "tmp" + os.sep + "tmp.txt"), bpy.context.scene.BBEPNumOfLine/10, bpy.context.scene.BBEPMinPot, 45, 1, 3)
		launch(exeName=command)
		
		print("Importing data into Blender")
		
		list = importEP(homePath + "tmp" + os.sep + "tmp.txt")
		
		epOBJ.append(list)

		ob = select("Emitter")
		
		# Positioning and rotating the Emitter
		try:
			if(False):
				bpy.ops.object.select_all(action="DESELECT")
				for o in bpy.data.objects:
					o.select = False
				bpy.context.scene.objects.active = None
				bpy.data.objects['SCENEWIDESURFACE'].select = True
				bpy.context.scene.objects.active = bpy.data.objects['SCENEWIDESURFACE']
				tmpRot = copy.copy(oE.rotation_euler)
				tmpLoc = copy.copy(oE.location)
				ob = select("Emitter")
				ob.rotation_euler = tmpRot
				ob.location = tmpLoc
			else:
				ob.location = [0,0,0]
		except Exception as E:
			print("An error occured while positioning and rotating the Emitter: " + str(E))

		print("Current frame before if animation: " + str(bpy.context.scene.frame_current))
		if animation:
			ob.particle_systems[0].settings.frame_start = bpy.context.scene.frame_current
			ob.particle_systems[0].settings.frame_end = bpy.context.scene.frame_current
			ob.particle_systems[0].settings.frame_end = 20
			ob.particle_systems[0].settings.count = len(ob.data.vertices)
			print("Animation")
		else:
			if not bpy.context.screen.is_animation_playing:
				bpy.ops.screen.animation_play()


		#Destroy the surface
		try:
			if "SCENEWIDESURFACE" in bpy.data.objects.keys():
				bpy.ops.object.select_all(action="DESELECT")
				for o in bpy.data.objects:
					o.select = False
				bpy.context.scene.objects.active = None
				bpy.data.objects['SCENEWIDESURFACE'].select = True
				bpy.context.scene.objects.active = bpy.data.objects['SCENEWIDESURFACE']
				bpy.ops.object.delete(use_global=False)
		except Exception as E:
			print("Warning: SCENEWIDESURFACE removing not performed properly: " + str(E))


# import curve description text into Blender
def importEP(path):
	global curveCount
	global objList
	
	curveCount = 0
	scene = bpy.context.scene
	pts = []
	objList = []

	# DEBUG
	print('DEBUG:', path)

	# read the file once to generate curves
	with open(path,"r") as file:
		for file_line in file:
			line=file_line.split()
			if line[0]=="n":
				if curveCount !=0:

					# for every n encountered creates a new curve
					cu = bpy.data.curves.new("Curve%3d"%curveCount, "CURVE")
					ob = bpy.data.objects.new("CurveObj%3d"%curveCount, cu)
					scene.objects.link(ob)
					scene.objects.active = ob

					# set all the properties of the curve
					spline = cu.splines.new("NURBS")
					cu.dimensions = "3D"
					cu.use_path = True
					cu.resolution_u = 1
					spline.points.add(len(pts)//4-1)   # minus 1 because of the 1 default .co
					spline.points.foreach_set('co', pts)
					spline.use_endpoint_u = True
					ob.field.type="GUIDE"
					ob.field.use_max_distance=True

					# each emitter vertex is dedicated a curve object,
					# however some emitter vertices exist very close to eachother, 
					# these adjusted settings are intended to constrain the search field significantly,
					# the hope is that this will prevent most mixed up trajectories. as evidenced
					# https://github.com/MonZop/BioBlender/issues/20
					ob.field.guide_minimum = 0.0008   # originally 0.8
					ob.field.distance_max = 0.0008   # originally 0.05

					# objList keeps a list of all EP related objects for easy deletion
					objList.append(ob)
					pts = []

				curveCount += 1
			elif line[0]=="v":
				pts.append(float(line[1]))
				pts.append(float(line[2]))
				pts.append(float(line[3]))
				pts.append(1)

	# rename current emitter
	if select("Emitter"):
		for list in epOBJ:
			for obj in list:
				if obj.name == "Emitter":
					obj.name = "Emitter%d"%curveCount

	# read the file again to generate the particle emitter object
	with open(path,"r") as file:
		verts=[]
		for line in file:
			# read the first line after each 'n' identifier
			if "n" in line:
				next = file.readline()
				coord = next.split()
				verts.append([float(i) for i in coord[1:]])

		# make mesh
		mesh = bpy.data.meshes.new("Emitter")
		mesh.from_pydata(verts[:-1], [], [])		# [:-1] to fix the off by one error somewhere...

		# append emitter object with particle sytem into scene, and assign mesh to the object
		# this is a workaround to avoid having to add a particle system from the scene context (impossible)
		Directory = homePath + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep
		Path = os.sep + os.sep + "data" + os.sep + "library.blend" + os.sep + "Object" + os.sep + "Emitter"
		objName = "Emitter"

		append_file_to_current_blend(Path, objName, Directory)
		
		ob = bpy.data.objects["Emitter"]
		print("EMITTER in ob: " + ob.name)
		ob.data = mesh
		
		# 2013-06-27 - Particle Settings End Frame
		#try:
		#	bpy.data.particles['ParticleSettings'].frame_end = bpy.context.scene.frame_end
			#bpy.data.particles['ParticleSettings'].frame_end = bpy.context.scene.frame_end
			#lifetime
		#except Exception as E:
		#	s = "Emitter Particle System frame_end NOT SET: " + str(E)
		#	print(s)

		# add material if does not exist
		if not ob.data.materials:
			mat = bpy.data.materials["Particles"]
			ob.data.materials.append(mat)

		# change particle density according to curve count
		ob.particle_systems[0].settings.count = int(bpy.context.scene.BBEPNumOfLine * 50000 * bpy.context.scene.BBEPParticleDensity)
		# reset location
		#ob.location = [0,0,0]
		# add object to deletion list
		objList.append(ob)
	return objList



# Convert WRL to OBJ for scivis.exe
def exportOBJ(path):
	vertexData = []		# list of list[3] (wrl vertices data)
	# read wrl file
	with open(path+".wrl") as wrl:
		found = False
		for line in wrl:
			# skip to coord section of the file
			if not found:
				if "coord" in line:
					wrl.readline()
					found = True
			# when in the coord section of the file
			else:
				if "]" not in line:
					# convert vertexData from string to a list of float
					entry = line[:-2].split()
					entryFloat = [float(coord) for coord in entry]
					vertexData.append(entryFloat)
				else:
					# end document processing
					break

	# write obj file: vertex data
	with open(path+".obj", mode="w") as obj:
		for entry in vertexData:
			out = "v %f %f %f\n" % (entry[0], entry[1], entry[2])
			obj.write(out)

		# face data
		i = 0
		while (i < len(vertexData)):
			out = "f %d/%d %d/%d %d/%d\n" % (i+1,i+1,i+2,i+2,i+3,i+3)
			obj.write(out)
			i = i + 3


def scenewideSetup():
	path = homePath+"tmp" + os.sep + "scenewide.pdb"
	# Actually, this is a custom "exportPDB" function, without instructions which were present in original "setup" function...
	print("=============== exporting PDB")
	print("Exporting scene to: " + str(path))
		
	outPath = abspath(path)
	print("=======outPath = " + str(outPath))
	i = 1
	with open(outPath, "w") as outFile:
		for o in bpy.data.objects:
			try:
				if(o.bb2_objectType=="ATOM"):
					loc = trueSphereOrigin(o)
					info = o.BBInfo
					x = "%8.3f" % loc[0]
					y = "%8.3f" % loc[1]
					z = "%8.3f" % loc[2]
					# convert line to pdbstring class
					line = PDBString(info)
					# Recalculate ATOM id number...
					line = line.set(1,"           ")
					if (i<10):
						tmpString = "ATOM      " + str(i)
					elif(i>9 and i<100):
						tmpString = "ATOM     " + str(i)
					elif(i>99 and i<1000):
						tmpString = "ATOM    " + str(i)
					else:
						tmpString = "ATOM   " + str(i)
					line = line.set(0,tmpString)
					# clear location column
					line = line.set(30,"                         ")
					# insert new location
					line = line.set(30,x)
					line = line.set(38,y)
					line = line.set(46,z)
					outFile.write (line+"\n")
					i = i+1
			except Exception as E:
				str4 = str(E)	
				print("An error occured in sceneWideSetup: " + str4)
		outFile.write("ENDMDL"+"\n")
	print("scenewideSetup is complete!")


# Import the surface generated from PyMol
def scenewideSurface():
	res = bpy.context.scene.BBMLPSolventRadius
	quality = "1"
		
	# 2013-06-28 -Trying to fix pdb ending with 1- or 1+...
	try:
		oPath = homePath + "tmp" + os.sep + "scenewide.pdb"
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
		s = "Unable to fix scenewide.pdb: " + str(E)
		print(s)
	
	tmpPathO = homePath+"tmp" + os.sep + "surface.pml"
	tmpPathL = "load "+  homePath+"tmp" + os.sep + "scenewide.pdb" + "\n"
	tmpPathS = "save " + homePath+"tmp"+os.sep+"scenewide.wrl" + "\n"
	
	# 2013-06-28
		#f.write("cmd.move('z',-cmd.get_view()[11])\n")
	
	
	with open(tmpPathO, mode="w") as f:
		f.write("# This file is automatically generated by BioBlender at runtime.\n")
		f.write("# Modifying it manually might not have an effect.\n")
		f.write(tmpPathL)
		f.write('cmd.hide("lines"  ,"scenewide")\n')
		f.write('cmd.set("surface_quality"  ,"%s")\n' % quality)
		f.write('cmd.show("surface","scenewide")\n')
		f.write('set solvent_radius,'+ str(res) +'\n')
		f.write('cmd.reset()\n')
		f.write('cmd.origin(position=[0,0,0])\n')
		f.write('cmd.center("origin")\n')
		f.write(tmpPathS)
		f.write("quit")
	print("Making Surface using PyMOL")
	
	command = "%s -c -u %s" % (quotedPath(pyMolPath), quotedPath(homePath+"tmp" + os.sep + "surface.pml"))
	
	command = quotedPath(command)
	launch(exeName=command)
	
	bpy.ops.import_scene.x3d(filepath=homePath+"tmp"+os.sep+"scenewide.wrl", axis_forward="Y", axis_up="Z")

	try:
		ob = bpy.data.objects['ShapeIndexedFaceSet']
		ob.name = "SCENEWIDESURFACE"
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
# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



class BB2_PDB_OUTPUT_PANEL(types.Panel):
	bl_label = "BioBlender2 PDB Output"
	bl_idname = "BB2_PDB_OUTPUT_PANEL"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBPDBExportStep = bpy.props.IntProperty(attr="BBPDBExportStep", name="PDB Export Step", description="PDB Export step", default=1, min=1, max=100, soft_min=1, soft_max=50)
	def draw(self, context):
		scene = bpy.context.scene
		layout = self.layout
		r = layout.row()
		r.prop(bpy.context.scene.render,"filepath", text="")
		r = layout.row()
		r.prop(bpy.context.scene, "frame_start")
		r = layout.row()
		r.prop(bpy.context.scene, "frame_end")
		r = layout.row()
		r.prop(bpy.context.scene, "BBPDBExportStep")
		r = layout.row()
		r.operator("ops.bb2_operator_export_pdb")
		r = layout.row()
		num = ((bpy.context.scene.frame_end - bpy.context.scene.frame_start)/bpy.context.scene.BBPDBExportStep)+1
		r.label("A total of %d frames will be exported." % num)



class bb2_operator_export_pdb(types.Operator):
	bl_idname = "ops.bb2_operator_export_pdb"
	bl_label = "Export PDB"
	bl_description = "Export current view to PDB"
	def invoke(self, context, event):
		try:
			if((bpy.context.scene.objects.active.bb2_objectType=="ATOM") or (bpy.context.scene.objects.active.bb2_objectType=="PDBEMPTY")):
				bpy.context.user_preferences.edit.use_global_undo = False
				selectedPDBidS = []
				for b in bpy.context.scene.objects:
					if (b.select == True):
						try:
							if((b.bb2_pdbID not in selectedPDBidS) and ((b.bb2_objectType=="ATOM") or (b.bb2_objectType=="PDBEMPTY"))):
								t = copy.copy(b.bb2_pdbID)
								selectedPDBidS.append(t)
						except Exception as E:
							str1 = str(E)	# Do not print...
				context.user_preferences.edit.use_global_undo = False
				for id in selectedPDBidS:
					tID = copy.copy(id)
					for o in bpy.data.objects:
						try:
							if((o.bb2_pdbID == tID) and (o.bb2_objectType=="PDBEMPTY")):
								tmpName = copy.copy(str(o.name))
								exportPDBSequence(tmpName, tID)
						except Exception as E:
							print("PDB seq error: " + str(E))
				bpy.context.user_preferences.edit.use_global_undo = True
			else:
				print("No PDB Empty or Atom selected")
		except Exception as E:
			s = "Export PDB Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_export_pdb)


def trueSphereOrigin(object):
	tmpSphere = bpy.data.objects[object.name]
	coord = [(object.matrix_world[0])[3], (object.matrix_world[1])[3],(object.matrix_world[2])[3]]
	return coord


def exportPDBSequence(curPDBpath="", tID = 0):
	step = bpy.context.scene.BBPDBExportStep
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	bpy.context.scene.render.engine = 'BLENDER_RENDER'
	
	a = time.time()

	cu = bpy.context.scene.render.filepath+"_"+((curPDBpath.split("."))[0]) + ".pdb"
	pdbPath = abspath(cu)
	
	print("=======outPath = " + str(pdbPath))
	with open(pdbPath, "w") as outFile:
		#outFile.write("NUMMDL    " + str(int(((bpy.context.scene.frame_end - bpy.context.scene.frame_start)/bpy.context.scene.BBPDBExportStep)+1)) + "\n")
		i = start
		while i <= end:
			bpy.context.scene.frame_set(i)
			# PRINT MODEL n
			if(i<10):
				currentModelString = "MODEL " + "       " + str(i)
			elif(i>9 and i<100):
				currentModelString = "MODEL " + "      " + str(i)
			elif(i>99 and i<1000):
				currentModelString = "MODEL " + "     " + str(i)
			else:
				currentModelString = "MODEL " + "    " + str(i)
			outFile.write(currentModelString + "\n")
			for o in bpy.data.objects:
				try:
					if((o.bb2_pdbID == tID) and (o.bb2_objectType=="ATOM")):
						loc = trueSphereOrigin(o)
						info = o.BBInfo
						x = "%8.3f" % loc[0]
						y = "%8.3f" % loc[1]
						z = "%8.3f" % loc[2]
						# convert line to pdbstring class
						line = PDBString(info)
						# clear location column
						line = line.set(30,"                         ")
						# insert new location
						line = line.set(30,x)
						line = line.set(38,y)
						line = line.set(46,z)
						outFile.write (line+"\n")
				except Exception as E:
					print("An error occured while exporting PDB sequence: " + str(E))
			outFile.write("ENDMDL" + "\n")
			i += step
		outFile.write("ENDMDL" + "\n")
	# clean up
	bpy.context.scene.frame_set(start)
	bpy.context.scene.frame_start = start
	bpy.context.scene.frame_end = end
	print(time.time()-a)
# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



class BB2_OUTPUT_PANEL(types.Panel):
	bl_label = "BioBlender2 Movie Output"
	bl_idname = "BB2_OUTPUT_PANEL"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBExportStep = bpy.props.IntProperty(attr="BBExportStep", name="Export Step", description="Export step", default=1, min=1, max=100, soft_min=1, soft_max=50)
	bpy.types.Scene.BBRecordEP = bpy.props.BoolProperty(attr="BBRecordEP", name="EP Curves (global)", description="Do and render EP Visualization")
	def draw(self, context):
		scene = bpy.context.scene
		layout = self.layout
		r = layout.row()
		r.prop(scene, "BBRecordEP")
		r = layout.row()
		r.operator("ops.bb2_operator_movie_refresh")
		r = layout.row()
		for ob in bpy.context.scene.objects:
			try:
				if (ob.bb2_objectType == "PDBEMPTY"):
					r.label(str(ob.name))
					r = layout.row()
					r.prop(ob, "bb2_outputOptions") 
					r = layout.row()
			except Exception as E:
				print("An error occured in BB2_OUTPUT_PANEL: " + str(E))	# Do nothing...
		r.prop(bpy.context.scene.render,"stamp_note_text", text="Notes")
		r = layout.row()
		r.prop(bpy.context.scene.render,"use_stamp", text ="Information Overlay")
		r = layout.row()
		r.prop(bpy.context.scene.world.light_settings, "use_environment_light", text="Ambient Light")
		r = layout.row()
		r.prop(bpy.context.scene.render,"filepath", text="")
		r = layout.row()
		r.prop(bpy.context.scene, "frame_start")
		r = layout.row()
		r.prop(bpy.context.scene, "frame_end")
		r = layout.row()
		r.prop(bpy.context.scene, "BBExportStep")
		r = layout.row()
		num = ((bpy.context.scene.frame_end - bpy.context.scene.frame_start)/bpy.context.scene.BBPDBExportStep)+1
		r.label("A total of %d frames will be exported." % num)
		r = layout.row()
		r.operator("ops.bb2_operator_anim")


class bb2_operator_movie_refresh(types.Operator):
	bl_idname = "ops.bb2_operator_movie_refresh"
	bl_label = "Refresh MOVIE List"
	bl_description = "Refresh MOVIE List"
	def invoke(self, context, event):
		global outputOptions
		for o in bpy.data.objects:
			try:
				if(o.bb2_objectType == "PDBEMPTY"):
					pe = copy.copy(o.name)
					print("pe: " + str(pe))
					print("outputOption: " + str(o.bb2_outputOptions))
			except Exception as E:
				print("An error occured in bb2_operator_movie_refresh:" + str(E))
		return{'FINISHED'}
bpy.utils.register_class(bb2_operator_movie_refresh)



class bb2_operator_anim(types.Operator):
	bl_idname = "ops.bb2_operator_anim"
	bl_label = "Export Movie"
	bl_description = "Make a movie"
	def invoke(self, context, event):
		try:
			bpy.context.user_preferences.edit.use_global_undo = False
			exportMovie()
			bpy.context.user_preferences.edit.use_global_undo = True
		except Exception as E:
			s = "Export Movie Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_anim)



def exportMovie():
	step = bpy.context.scene.BBExportStep
	start = bpy.context.scene.frame_start
	end = bpy.context.scene.frame_end
	bpy.context.scene.render.engine = 'BLENDER_RENDER'
	
	a = time.time()

	pdbPath = os.path.normpath(abspath(bpy.context.scene.render.filepath))

	if opSystem == "linux":
		if not os.path.isdir(pdbPath):
			os.mkdir(abspath(pdbPath))
	elif opSystem == "darwin":
		if not os.path.isdir(pdbPath):
			os.mkdir(abspath(pdbPath))
	else:
		if not os.path.isdir(r"\\?\\" + pdbPath):
			os.mkdir(r"\\?\\" + pdbPath)

	i = start
	
	# Set-up PDBs...
	PDBdict = {}	# Key: PDBid; Value: PDBEMPTY name
	for p in bpy.data.objects:
		try:
			if p.bb2_objectType == "PDBEMPTY":
				PDBdict[p.bb2_pdbID] = copy.copy(p.name)
		except Exception as E:
			print("Error m01: " + str(E))
	
	while i <= end:
		bpy.context.scene.frame_start = start
		bpy.context.scene.frame_end = end
		bpy.context.scene.frame_set(i)
		current_frame = bpy.context.scene.frame_current
		# Destroy SURFACE objects
		surfacesDestroyer()
		todoAndviewpoints()
		for pdb in PDBdict:
			bpy.ops.object.select_all(action="DESELECT")
			for o in bpy.data.objects:
				o.select = False
			for o in bpy.data.objects:
				try:
					if ((o.bb2_objectType == "ATOM") and (o.bb2_pdbID == PDBdict[pdb])):
						o.select = True
					else:
						o.select = False
				except Exception as E:
					print("Error m02: " + str(E))
			# For every PDB ID [ = pdb in PDBdict], calls the right visualization function...
			tmpPDBName = str(PDBdict[pdb])
			tmpPDBobject = bpy.data.objects[tmpPDBName]
			tmpPDBobject.select = True
			bpy.context.scene.objects.active = tmpPDBobject
			try:
				print("tmpPDBobject: " + str(tmpPDBobject.name))
				tmpMode = tmpPDBobject.bb2_outputOptions
				if tmpMode == "0":
					# Rendering MAIN Atoms
					bpy.context.scene.BBViewFilter="1"
					bpy.context.scene.BBAtomic="0"
					bpy.context.scene.BBAtomicMLP=False
					updateView(residue=bpy.context.scene.objects.active)
				elif tmpMode == "1":
					# Rendering +SIDE
					bpy.context.scene.BBViewFilter="2"
					bpy.context.scene.BBAtomic="0"
					bpy.context.scene.BBAtomicMLP=False
					updateView(residue=bpy.context.scene.objects.active)
				elif tmpMode == "2":
					# Rendering +HYD
					bpy.context.scene.BBViewFilter="3"
					bpy.context.scene.BBAtomic="0"
					bpy.context.scene.BBAtomicMLP=False
					updateView(residue=bpy.context.scene.objects.active)
				elif tmpMode == "3":
					# Rendering Surface
					bpy.context.scene.BBViewFilter="4"
					bpy.context.scene.BBAtomic="0"
					bpy.context.scene.BBAtomicMLP=False
					updateView(residue=bpy.context.scene.objects.active)
				elif tmpMode == "4":
					# Rendering MLP MAIN
					bpy.context.scene.BBViewFilter="1"
					bpy.context.scene.BBAtomic="0"
					bpy.context.scene.BBAtomicMLP=True
					updateView(residue=bpy.context.scene.objects.active)
					atomicMLP(True, pdb)
				elif tmpMode == "5":
					# Rendering MLP +SIDE
					bpy.context.scene.BBViewFilter="2"
					bpy.context.scene.BBAtomic="0"
					bpy.context.scene.BBAtomicMLP=True
					updateView(residue=bpy.context.scene.objects.active)
					atomicMLP(True, pdb)
				elif tmpMode == "6":
					# Rendering MLP +HYD
					bpy.context.scene.BBViewFilter="3"
					bpy.context.scene.BBAtomic="0"
					bpy.context.scene.BBAtomicMLP=True
					updateView(residue=bpy.context.scene.objects.active)
					atomicMLP(True, pdb)
				elif tmpMode == "7":
					# Rendering MLP SURFACE
					bpy.context.scene.BBViewFilter="4"
					bpy.context.scene.BBAtomic="1"
					mlp(pdb, True)
					mlpRender(pdb)
					#updateView(residue=bpy.context.scene.objects.active)
			except Exception as E:
				print("Error m03: " + str(E))
		# ... then, if EP is checked, performs a global EP visualization
		try:
			if bpy.context.scene.BBRecordEP:
				scenewideEP(animation=True)
				step = 1  # EP animation should not skip steps, due to particles behavior
		except Exception as E:
			print("Error m04: " + str(E))
		# render frame
		current_frame = i
		bpy.context.scene.frame_current = 1
		bpy.context.scene.frame_start = i
		bpy.context.scene.frame_end = i
		bpy.context.scene.frame_current = i
		bpy.ops.render.render(animation=True)
		# Destroy SURFACE objects
		surfacesDestroyer()
		todoAndviewpoints()
		# Next frame
		i += step
	# clean up
	bpy.context.scene.frame_set(start)
	bpy.context.scene.frame_start = start
	bpy.context.scene.frame_end = end
	print(time.time()-a)
	

def surfacesDestroyer():
	for s in bpy.data.objects:
		s.select = False
		try:
			if(s.bb2_objectType == "SURFACE"):
				s.select = True
				bpy.context.scene.objects.active = s
				bpy.ops.object.delete(use_global=False)
		except Exception as E:
			print("Error m05: " + str(E))
# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


class BB2_NMA_PANEL(types.Panel):
	bl_label = "BioBlender2 NMA Visualization"
	bl_idname = "BB2_NMA_PANEL"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "scene"
	bl_options = {'DEFAULT_CLOSED'}
	bpy.types.Scene.BBNormalModeAnalysis = bpy.props.EnumProperty(attr="BBNormalModeAnalysis", name="Mode", description="Select a normal mode analysis to show", items=(("0", "1", ""), ("1", "2", ""), ("2", "3", ""), ("3", "4", ""), ("4", "5", ""), ("5", "6", ""), ("6", "7", ""), ("7", "8", ""), ("8", "9", ""), ("9", "10", ""), ("10", "11", ""), ("11", "12", ""), ("12", "13", ""), ("13", "14", ""), ("14", "15", ""), ("15", "16", ""), ("16", "17", ""), ("17", "18", ""), ("18", "19", ""), ("19", "20", "")), default="0")
	bpy.types.Scene.BBNMANbModel = bpy.props.IntProperty(attr="BBNMANbModel", name="NMA steps", description="Number of conformations to be calculated in each direction", default=6, min=1, max=100, soft_min=1, soft_max=50)
	bpy.types.Scene.BBNMARMSD = bpy.props.FloatProperty(attr="BBNMARMSD", name="RMSD sampling", description="RMSD between the given and the farthest conformation", default=0.8, min=0.1, max=5.0, soft_min=0.1, soft_max=5.0, precision=2, step=1.0)
	bpy.types.Scene.BBNMACutoff = bpy.props.FloatProperty(attr="BBNMACutoff", name="NMA cutoff", description="NMA cutoff distance (Å) for pairwise interactions", default=15.0, min=0.0, max=25.0, soft_min=1.0, soft_max=25.0)
	bpy.types.Scene.BBNMAGamma = bpy.props.FloatProperty(attr="BBNMAGamma", name="NMA Gamma", description="NMA spring constant", default=1.0, min=0.0, max=10.0, soft_min=0.1, soft_max=5.0, precision=2, step=1.0)

	def draw(self, context):
		scene = context.scene
		layout = self.layout
		split = layout.split()
		c = split.column()
		c.prop(scene, "BBNormalModeAnalysis")
		c.label("Options:")
		c.prop(scene, "BBNMANbModel")
		c.prop(scene, "BBNMARMSD")
		c.prop(scene, "BBNMACutoff")
		c.prop(scene, "BBNMAGamma")
		c = c.column(align=True)
		c = split.column()
		c.scale_y = 2
		c.operator("ops.bb2_operator_nma")


class bb2_operator_nma(types.Operator):
	bl_idname = "ops.bb2_operator_nma"
	bl_label = "Calculate NMA trajectories (pdb)"
	bl_description = "Calculate Normal Mode Analysis Trajectories"
	def invoke(self, context, event):
		global importReady
		try:
			bpy.context.user_preferences.edit.use_global_undo = False
			computeNormalModeTrajectories()
			bpy.context.user_preferences.edit.use_global_undo = True
		except Exception as E:
			s = "Normal Mode Analysis Calculate Failed: " + str(E)
			print(s)
			return {'CANCELLED'}
		else:
			return{'FINISHED'}
bpy.utils.register_class(bb2_operator_nma)


def computeNormalModeTrajectories() : 
	name = bpy.context.scene.BBModelRemark
	inputpath = abspath(bpy.context.scene.BBImportPath)
	if os.path.isfile(inputpath) : 
		modestr = bpy.context.scene.BBNormalModeAnalysis
		mode = int(modestr)+1
		struct = "--all"
		name = bpy.context.scene.BBModelRemark
		rmsd = bpy.context.scene.BBNMARMSD
		gamma = bpy.context.scene.BBNMAGamma
		cutoff = bpy.context.scene.BBNMACutoff		 
		nbconfiguration = bpy.context.scene.BBNMANbModel
		
		outputpath = homePath + "fetched" + os.sep +name+"_"+"Mode"+str(mode)+"_"+struct+"_"+str(rmsd)+"_"+str(nbconfiguration)+".pdb"
		
		file = open(outputpath, 'w+')
		file.close()
		
		if opSystem == "linux":
			command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "nma" + os.sep + "nma.py"))
			command = quotedPath(command)
			p = launch(exeName=command, async = False)
		elif opSystem == "darwin":
			command = "chmod 755 %s" % (quotedPath(homePath + "bin" + os.sep + "nma" + os.sep + "nma.py"))
			command = quotedPath(command)
			p = launch(exeName=command, async = False)
		global pyPath
		if not pyPath:
			pyPath = "python"
		command = "%s %s -i %s -o %s -m %d -r %f -n %d %s " % (quotedPath(pyPath), quotedPath(homePath + "bin" + os.sep + "nma" + os.sep + "nma.py"), quotedPath(inputpath), quotedPath(outputpath), mode, rmsd, nbconfiguration, struct)
		p = launch(exeName=command, async = False)
		bpy.context.scene.BBImportPath = outputpath
		importPreview()
	else : 
		print("File does not exist !!")


# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================


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
		bpy.context.scene.frame_current = int(time+offset)
		# insert keyframe
		bpy.ops.anim.keyframe_insert_menu(type="LocRotScale")
		# jump back to the playback position
		bpy.context.scene.frame_current = int(time)
		
		# end game if done
		if time > bpy.context.scene.frame_end:
			logic.endGame()
		else:
			print("\rRecording protein motion %.0f%%" %(time/bpy.context.scene.frame_end*100), end="")



# ==================================================================================================================
# ==================================================================================================================
# ==================================================================================================================



if __name__ == "__main__":
	print("BioBlender2 module created")