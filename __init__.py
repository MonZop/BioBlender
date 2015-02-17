import bpy
from bpy import *
from urllib.parse import urlencode
from urllib.request import *
from html.parser import *
from smtplib import *
from email.mime.text import MIMEText
import time, platform, os
import codecs
import bpy.path
from bpy.path import abspath
import base64
import mathutils
from mathutils import *
from math import *
import pickle
import shutil
import subprocess
import sys



bl_info = {
    "name" : "BioBlender 2.0",
    "author" : "SciVis, IFC-CNR",
    "version" : (2,0),
    "blender" : (2,7,3),
    "location" : "Properties Window > Scene",
    "description" : "BioBlender 2.0",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "http://bioblender.eu/?page_id=665",
    "category" : "Add Mesh"
}



# ==================================================================================================================


from .BioBlender import *


# ==================================================================================================================


def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
