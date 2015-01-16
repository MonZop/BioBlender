from prody import *
import sys
import getopt

def computeNormalModeVectors(userfilenamein="",userfilenameout="NMA.pdb", usermode=0, usercutoff=15.0, usergamma=1.0) : 
	mystruct = parsePDB(userfilenamein, model=1)
	mystruct_ca = mystruct.select('protein and name CA')	
	anm = ANM(userfilenamein+str(usermode))
	anm.buildHessian(mystruct_ca, gamma=usergamma, cutoff=usercutoff)
	anm.calcModes()
	#bb_anm, bb_atoms = extrapolateModel(anm, mystruct_ca, mystruct)
	bb_anm, bb_atoms = extendModel(anm, mystruct_ca, mystruct)
	nmastruct = mystruct.copy( bb_atoms )
	aavectors = bb_anm[usermode].getArrayNx3() 
	nmastruct = mystruct.copy()
	# nmastruct = mystruct.copy( bb_atoms )
	nmastruct.delCoordset(0)
	nmastruct.addCoordset(aavectors)	

	for aa in nmastruct : 
		name = aa.getAtomName()
		if name != "CA" : 
			aa.setCoordinates([0.0,0.0,0.0])		
	writePDB(userfilenameout, nmastruct)

def usage() :
	print "Compute a normal mode analysis based on Anistropic Network Model (ANM) on alpha carbon, according to minimized input pdb struture (local file or pdb code) and provide an output pdb structure with normal mode vectors on CA instead of atom positions for the specified normal mode"
	print "python nmavectors.py --input=input.pdb -output=output.pdb -mode=mode [cutoff=][--gamma]"
		
def main():
	try : 
		opts, args = getopt.getopt(sys.argv[1:], "hi:o:m:g:c:", ["help","input=", "output=","mode=",  "gamma=", "cutoff="])
	except getopt.GetoptError:
		usage()
		sys.exit(2)	
	mode = 0
	pdbin=""
	pdbout=""
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
		elif opt in ("-c", "--cutoff"):
			cutoff = float(arg)
		elif opt in ("-g", "--gamma"):
			gamma = float(arg)
		elif opt in ("-m", "--mode"): 
			mode = int(arg)
		else : 
			usage()
			sys.exit(2)	
	if pdbin=="" or pdbout=="" or mode==0 : 
			usage()
			sys.exit(2)	
	else : 		
		computeNormalModeVectors(pdbin,pdbout, mode, cutoff, gamma)

if __name__ == "__main__":
    sys.exit(main())