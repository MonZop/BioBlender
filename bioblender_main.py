'''
bioblender_main.py
for license see LICENSE.txt

'''

from .file_append_utils import file_append
from .tables import (
    color,
    values_fi,
    molecules_structure,
    scale_vdw, scale_cov,
    NucleicAtoms, NucleicAtoms_Filtered)

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

print(NucleicAtoms_Filtered)
