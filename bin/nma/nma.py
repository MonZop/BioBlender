from prody import *
import sys
import getopt

def computeNormalMode(userfilenamein="",userfilenameout="NMA.pdb", usermode=0,userrmsd=0.8, usernbconf=5, conf="allatom", usercutoff=15.0, usergamma=1.0) : 
	fileOutput = open(userfilenameout, 'w+')
	
	mystruct = parsePDB(userfilenamein, model=1)	
	# Return an AtomGroup and/or dictionary containing header data parsed from a PDB file.
	
	mystruct_ca = mystruct.select('protein and name CA')
	# Return atoms matching selstr criteria. See select module documentation for details and usage examples.
	
	anm = ANM(userfilenamein+str(usermode))
	#Perform ANM calculations for given PDB structure and output results in NMD format.
	anm.buildHessian(mystruct_ca, gamma=usergamma, cutoff=usercutoff)
	anm.calcModes()
	
	# bb_anm, bb_atoms = extrapolateModel(anm, mystruct_ca, mystruct.select(conf))
	# extendModel(model, nodes, atoms, norm=False)[source]
	# Extend a coarse grained model built for nodes to atoms. 
	# Model may be ANM, GNM, PCA, or NMA instance. 
	# This function will take part of the normal modes for each node (i.e. CA atoms) 
	# and extend it to all other atoms in the same residue. 
	# For each atom in nodes argument atoms argument must contain a corresponding residue. 
	# If norm is True, extended modes are normalized.
	# return extended, atommap
	bb_anm, bb_atoms = extendModel(anm, mystruct_ca, mystruct.select(conf))
	#print("type: " + str(type(bb_atoms)))
	#print("bb_atoms stringato: " + str(bb_atoms))


	# traverseMode(mode, atoms, n_steps=10, rmsd=1.5)[source]
	# Generates a trajectory along a given mode, which can be used to animate fluctuations in an external program.
	# Parameters:	
	# mode (Mode) - mode along which a trajectory will be generated
	# atoms (Atomic) - atoms whose active coordinate set will be used as the initial conformation
	ensemble = traverseMode(bb_anm[usermode], bb_atoms, n_steps=usernbconf, rmsd=userrmsd)

	#nmastruct = mystruct.copy(bb_atoms)
	nmastruct = mystruct.copy()
	#print("type: " + str(type(nmastruct)))
	#print("stringato: " + str(nmastruct))
	#print("dir: " + str(dir(nmastruct)))
	#print("Primo elencato: " + str(nmastruct[0]))
	
	nmastruct.delCoordset(0)
	nmastruct.addCoordset(ensemble)
	nmastruct.addCoordset(ensemble)	# Prody checks if coordsets> 1; should be >= 1...
	
	writePDBStream(fileOutput, nmastruct)
	fileOutput.close()
	print("NMA pdb exit success")


def usage() :
	print("Compute a normal mode analysis based on Anistropic Network Model (ANM) on alpha carbon, according to minimized input pdb struture (local file or pdb code) and provide an output pdb structure with trajectory the specified normal mode, using extrapolation to produce a carbon alpha trajectory, a backbone trajectory, or a all atom trajectory (default)")
	print("python nma.py --input=input.pdb -output=output.pdb -mode=mode [--rmsd=0.8][--nbconformations=5][gamma=][cutoff=][--all][--calpha][--backbone]")
		
def main():
	try : 
		opts, args = getopt.getopt(sys.argv[1:], "hi:o:m:r:n:g:c:", ["help","input=", "output=","mode=", "rmsd=","nbconformations=", "gamma=", "cutoff=", "backbone", "calpha", "all"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)	
	mode = 0
	rmsd = 0.8
	nbconformations = 5
	pdbin=""
	pdbout=""
	conf="all"
	gamma=1.0
	cutoff=15.0
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage()               
			sys.exit()                  
		elif opt in ("-i", "--input"): 
			pdbin = arg   
		elif opt in ("-o", "--output"): 
			pdbout = arg   
		elif opt in ("-r", "--rmsd"): 
			rmsd = float(arg)   
		elif opt in ("-n", "--nbconformations"):
			nbconformations = int(arg)
		elif opt in ("-c", "--cutoff"):
			cutoff = float(arg)
		elif opt in ("-g", "--gamma"):
			gamma = float(arg)
		elif opt in ("-m", "--mode"): 
			mode = int(arg)
		elif opt in ("--allatom"): 
			conf = "all"
		elif opt in ("--calpha"): 
			conf = "calpha"
		elif opt in ("--backbone"): 
			conf = "backbone"
		else : 
			usage()
			sys.exit(2)	
	if pdbin=="" or pdbout=="" or mode==0 : 
			usage()
			sys.exit(2)	
	else : 		
		computeNormalMode(pdbin,pdbout, mode, rmsd, nbconformations, conf, cutoff, gamma)

if __name__ == "__main__":
    sys.exit(main())