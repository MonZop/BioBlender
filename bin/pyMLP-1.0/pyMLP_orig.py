#
# pyMLP Molecular Lipophilic Potential evaluator
# Copyright (c) 2006-2007 Julien Lefeuvre <lefeuvrejulien@yahoo.fr>
#

"""pyMLP: Molecular Lipophilicity Potential evaluator"""

# PLEASE DO NOT CHANGE FORMAT OF __version__ LINE (setup.py reads this)

__author__ =    "Julien Lefeuvre <lefeuvrejulien@yahoo.fr>"
__version__ =   "1.0"
__date__ =      "2007-03-28"
__copyright__ = "Copyright (c) 2006-2007 %s. All rights reserved." % __author__
__licence__ =   "BSD"
__modifications__ =   "SciVis <www.scivis.ifc.cnr.it> 2010. We introduced fi values for Hydrogens and sugars and Testa formula"

import sys
import os
import shutil
import time
import numpy

from optparse import OptionParser
from pprint import pformat

try:
	import psyco
	psyco.full()
except ImportError:
	pass

class Defaults(object):
	"""Constants"""

	def __init__(self):
		self.gridmargin = 10.0
		self.fidatadefault = {                    #Default fi table
'ALA': {'CB': '0.63',    #fi : lipophilic atomic potential
		'C': '-0.54',
		'CA': '0.02',
		'O': '-0.68',
		'N': '-0.44',
		'H': '-0.5',
		'HA': '-0.25'},
'ARG': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD': '0.45',
		'CG': '0.45',
		'CZ': '-0.54',
		'N': '-0.44',
		'NE': '-0.55',
		'NH1': '-0.11',
		'NH2': '-0.83',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25',
		'HD2': '-0.25',
		'HD3': '-0.25',
		'HH11': '-0.5',
		'HH12': '-0.5',
		'HH21': '-0.5',
		'HH22': '-0.5'},
'ASN': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.02',
		'CG': '0.45',
		'N': '-0.44',
		'ND2': '-0.11',
		'O': '-0.68',
		'OD1': '-0.68',
		'H': '-0.5',
		'HA': '-0.25',
		'HD21': '-0.5',
		'HD22': '-0.5'},
'ASP': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CG': '0.54',
		'N': '-0.44',
		'O': '-0.68',
		'OD1': '-0.68',
		'OD2': '0.53',
		'H': '-0.5',
		'HA': '-0.25'},
'CYS': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'N': '-0.44',
		'O': '-0.68',
		'SG': '0.27',
		'H': '-0.5',
		'HA': '-0.25'},
'GLN': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD': '-0.54',
		'CG': '0.45',
		'N': '-0.44',
		'NE2': '-0.11',
		'O': '-0.68',
		'OE1': '-0.68',
		'H': '-0.5',
		'HA': '-0.25',
		'HE21': '-0.5',
		'HE22': '-0.5'},
'GLU': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD': '-0.54',
		'CG': '0.45',
		'N': '-0.44',
		'O': '-0.68',
		'OE1': '-0.68',
		'OE2': '0.53',
		'H': '-0.5',
		'HA': '-0.25'},
'GLY': {'C': '-0.54',
		'CA': '0.45',
		'O': '-0.68',
		'N': '-0.55',
		'H': '-0.5',
		'HA': '-0.25'},
'HIS': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD2': '0.31',
		'CE1': '0.31',
		'CG': '0.09',
		'N': '-0.44',
		'ND1': '-0.56',
		'NE2': '-0.80',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25',
		'HD2': '-0.25',
		'HE1': '-0.25',
		'HE2': '-0.5'},
'HYP': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD1': '0.45',
		'CG': '0.02',
		'N': '-0.92',
		'O': '-0.68',
		'OD2': '-0.93',
		'H': '-0.5',
		'HA': '-0.25'},
'ILE': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.02',
		'CD': '0.63',
		'CD1': '0.63',
		'CG1': '0.45',
		'CG2': '0.63',
		'N': '-0.44',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25'},
'LEU': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD1': '0.63',
		'CD2': '0.63',
		'CG': '0.02',
		'N': '-0.44',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25'},
'LYS': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD': '0.45',
		'CE': '0.45',
		'CG': '0.45',
		'N': '-0.44',
		'NZ': '-1.08',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25',
		'HE2': '-0.25',
		'HE3': '-0.25',
		'HZ1': '-0.5',
		'HZ2': '-0.5',
		'HZ3': '-0.5'},
'MET': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CE': '0.63',
		'CG': '0.45',
		'N': '-0.44',
		'O': '-0.68',
		'SD': '-0.30',
		'H': '-0.5',
		'HA': '-0.25'},
'PCA': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD': '-0.54',
		'CG': '0.45',
		'N': '1.52',
		'O': '-0.68',
		'OE': '-0.68',
		'H': '-0.5',
		'HA': '-0.25'},
'PHE': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD1': '0.31',
		'CD2': '0.31',
		'CE1': '0.31',
		'CE2': '0.31',
		'CG': '0.09',
		'CZ': '0.31',
		'N': '-0.44',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25'},
'PRO': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD': '0.45',
		'CG': '0.45',
		'N': '-0.92',
		'O': '-0.68',
		'HA': '-0.25',
		'HD2': '-0.25',
		'HD3': '-0.25',},
'SER': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'N': '-0.44',
		'O': '-0.68',
		'OG': '-0.99',
		'H': '-0.5',
		'HA': '-0.25'},
'THR': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.02',
		'CG2': '0.63',
		'N': '-0.44',
		'O': '-0.68',
		'OG1': '-0.93',
		'H': '-0.5',
		'HA': '-0.25'},
'TRP': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD1': '0.31',
		'CD2': '0.24',
		'CE2': '0.24',
		'CE3': '0.31',
		'CG': '0.09',
		'CH2': '0.31',
		'CZ2': '0.31',
		'CZ3': '0.31',
		'N': '-0.44',
		'NE1': '-0.55',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25',
		'HE1': '-0.5',
		'HD1': '-0.25'},
'TYR': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.45',
		'CD1': '0.31',
		'CD2': '0.31',
		'CE1': '0.31',
		'CE2': '0.31',
		'CG': '0.09',
		'CZ': '0.09',
		'N': '-0.44',
		'O': '-0.68',
		'OH': '-0.17',
		'H': '-0.5',
		'HA': '-0.25'},
'VAL': {'C': '-0.54',
		'CA': '0.02',
		'CB': '0.02',
		'CG1': '0.63',
		'CG2': '0.63',
		'N': '-0.44',
		'O': '-0.68',
		'H': '-0.5',
		'HA': '-0.25'},
'CA': { 'CA': '-1.0'},
'NAG': {'C1': '0.02',
		'C2': '0.02',
		'C3': '0.02',
		'C4': '0.02',
		'C5': '0.02',
		'C6': '0.31',
		'C7': '-0.61',
		'C8': '0.62',
		'O1': '-0.92',
		'O2': '-0.92',
		'O3': '-0.92',
		'O4': '-0.92',
		'O5': '-1.14',
		'O6': '-0.99',
		'O7': '-0.58',
		'N2': '-0.49',
		'H2': '-0.25',
		'HN2': '-0.5'},
'NDG': {'C1': '0.02',
		'C2': '0.02',
		'C3': '0.02',
		'C4': '0.02',
		'C5': '0.02',
		'C6': '0.031',
		'C7': '-0.61',
		'C8': '0.62',
		'O1L': '-0.92',
		'O3': '-0.92',
		'O4': '-0.92',
		'O': '-1.14',
		'O6': '-0.99',
		'O7': '-0.58',
		'N2': '-0.29'},
'BMA': {'C1': '0.02',
		'C2': '0.02',
		'C3': '0.02',
		'C4': '0.02',
		'C5': '0.02',
		'C6': '0.31',
		'O1': '-0.92',
		'O2': '-0.92',
		'O3': '-0.92',
		'O4': '-0.92',
		'O5': '-1.14',
		'O6': '-0.58'},
'MAN': {'C1': '0.02',
		'C2': '0.02',
		'C3': '0.02',
		'C4': '0.02',
		'C5': '0.02',
		'C6': '0.31',
		'O1': '-0.92',
		'O2': '-0.92',
		'O3': '-0.92',
		'O4': '-0.92',
		'O5': '-1.14',
		'O6': '-0.58'},
'GAL': {'C1': '0.02',
		'C2': '0.02',
		'C3': '0.02',
		'C4': '0.02',
		'C5': '0.02',
		'C6': '0.31',
		'O1': '-0.92',
		'O2': '-0.92',
		'O3': '-0.92',
		'O4': '-0.92',
		'O5': '-1.14',
		'O6': '-0.58'},
'NAN': {'C1': '-0.61',
		'C2': '0.02',
		'C3': '0.62',
		'C4': '0.02',
		'C5': '0.02',
		'C6': '0.02',
		'C7': '0.02',
		'C8': '0.02',
		'C9': '0.31',
		'C10': '-0.61',
		'C11': '0.62',
		'O1A': '-0.21',
		'O1B': '-0.46',
		'O2': '-0.92',
		'O4': '-0.92',
		'O6': '-1.14',
		'O7': '-0.92',
		'O8': '-0.92',
		'O9': '-0.7',
		'O10': '-0.22',
		'N5': '-0.49',
		'NH5': '-0.5'}}


def _CLIparsing():
	"""Parsing of pyMLP command line"""
	usage='\n%%prog -i file.pdb\n\n%s' %__doc__
	version="%%prog %s %s" %(__version__, __date__)
	CLparser = OptionParser(usage=usage, version=version)
	CLparser.add_option('-i', '--inpdb', dest='pdbfile',
		help='PDB file (input)', metavar='file.pdb')
	CLparser.add_option('-f', '--fipdb', dest='fipdbfile',
		help='PDB file with added fi (partial lipophilicity) (input/output)'
		' (optional)', metavar='file_fi.pdb')
	CLparser.add_option('-t', '--fitab', dest='fitabfile',
		help='FI table used to convert file.pdb into file_fi.pdb '
		'(input/output) (optional)', metavar='fi.tab')
	CLparser.add_option('-o', '--outdx', dest='dxfile',
		help='DX file (output) (optional)', metavar='file.dx')
	CLparser.add_option('-m', '--method', dest='method',
		help='Potential calculation method :                     '
			'dubost     [1/(1+d)]                               '
			'testa      [exp(-d/2)] (default)                   '
			'fauchere   [exp(-d/2)]                             '
			'brasseur   [exp(-d/3.1)]                           '
			'buckingham [1/d**n]                                '
			'type5      [exp(-sqrt(d))]                         '
			'none       [no calculation]', metavar='fauchere')
	CLparser.add_option('-s', '--spacing', type="float", dest='spacing',
		help='Grid spacing (default = 1.0 Angstrom)', metavar='1.0')
	CLparser.add_option('-n', '--n_exp', type="float", dest='nexp',
		help='Exponent for the buckingham method (default = 3.0)',
		metavar='3.0')
	CLparser.add_option('-v', '--verbose', action='store_true', dest='verbose',
		help='make a lot of noise ...')
	CLparser.set_defaults(verbose=False, spacing=1.0, method='fauchere',
							nexp=3.0)
	(params, args) = CLparser.parse_args()

	#Checking if the input is valid
	if args or (not params.pdbfile and not params.fipdbfile):
		CLparser.error('This script require parameters ...\n'
					'see help : pyMLP.py -h')

	methods=['dubost', 'testa', 'fauchere', 'brasseur', 'buckingham', 'type5', 'none']
	if params.method not in methods:
		CLparser.error('Please use a valid method ...\n'
					'see help : pyMLP.py -h')
	return params


def writefitab(fidata,fitabfile,verbose=False):
	"""write fidata in the file fitabfile (to let the user modify it)"""
	try:
		fitabf = open(fitabfile,'w')
		fitabf.write('fidata = {\n '+pformat(fidata)[1:])
		if verbose: sys.stdout.write("%s created with default values...\n"
											% fitabfile)
	except IOError:
		sys.stderr.write("Can't write file named : %s\n" % fitabfile)


class Atom(object):
	"""Atom properties needed for the calculation"""

	def __init__(self, x, y, z, fi):
		self.x = x
		self.y = y
		self.z = z
		self.fi = fi

class Molecule(object):
	"""Main class of pyMLP"""

	def __init__(self, verbose=False):
		self.verbose = verbose
		self.name = 'molecule'
		self.data = None
		self.pot = None
		self.griddim = None
		self.gridcoord = None
		self.spacing = None

	def parsepdb(self, pdbfile, checkforfi=False):
		"""Parsing a PDB (Protein Data Bank) formated file"""
		if pdbfile[-4:].lower()=='.pdb':
			self.name = pdbfile[0:-4]
		else:
			self.name = pdbfile
		try:
			pdbtext = open(pdbfile)
		except IOError:
			if self.verbose: sys.stderr.write("Can't open %s ...\n" % pdbfile)
			sys.exit()
		self.data=[]
		for line in pdbtext:
			recordname=line[:6].strip()
			if recordname in ['MODEL', 'ENDMDL', 'TER', 'END']:
				atmnumber, atmname, altloc, resname = None, None, None, None
				chainid, resseq, icode = None, None, None
				atmx, atmy, atmz = None, None, None
				occupancy, tempfactor = None, None
				fi = None
				comments=line[6:]
			elif recordname in ['ATOM', 'HETATM']:
				try:
					atmnumber = int(line[6:11].strip())
					atmname = line[12:16].strip()
					altloc = line[16].strip()
					resname = line[17:20].strip()
					chainid = line[21].strip()
					resseq = int(line[22:26].strip())
					icode = line[26].strip()
					atmx = float(line[30:38].strip())
					atmy = float(line[38:46].strip())
					atmz = float(line[46:54].strip())
					occupancy = float(line[54:60].strip())
					tempfactor = float(line[60:66].strip())
					if checkforfi:
						fi = float(line[66:72].strip())
						comments = line[72:]
					else:
						fi = None
						comments = line[66:]
				except ValueError:
					if self.verbose: sys.stderr.write(
							"%s might not respect PDB standards\nor the fi "
							"parameters could have been misplaced\n" % pdbfile)
					continue
			else:
				continue
			pdbline={'recordname': recordname,
					'atmnumber': atmnumber,
					'atmname': atmname,
					'altloc': altloc,
					'resname': resname,
					'chainid': chainid,
					'resseq': resseq,
					'icode': icode,
					'atmx': atmx,
					'atmy': atmy,
					'atmz': atmz,
					'occupancy': occupancy,
					'tempfactor': tempfactor,
					'fi': fi,
					'comments': comments}
			self.data.append(pdbline)
		if self.verbose: sys.stdout.write(
							"\n%s was parsed ... %i lines were taken into "
							"account\n" % (pdbfile, len(self.data)))

	def assignfi(self, fidata):
		"""assign fi parameters to each atom in the pdbfile"""
		for line in self.data:
			if line['resname'] in fidata:
				if not line['fi']:
					try:
						fi=float(fidata[line['resname']][line['atmname']])
						line['fi']=fi
					except KeyError:
						continue
						if self.verbose: sys.stderr.write(
							"Atom Number %s is not defined in \nthe fi "
							"parameters (might be an H)\n" % line['atmnumber'])
						

	def writefipdb(self,fipdbfile):
		"""write a fipdb file containing the data for the pdbfile and the fi
		parameters"""
		try:
			fipdbf = file(fipdbfile,'w')
		except IOError:
			if self.verbose: sys.stderr.write(
				"I am having difficulties writing on %s" % fipdbfile)
		for d in self.data:
			if d['fi']:
				header='%-6s%5i  %-3s%1s%3s %1s%4i%1s   ' % (
					d['recordname'], d['atmnumber'], d['atmname'], d['altloc'],
					d['resname'], d['chainid'], d['resseq'], d['icode'])
				coord='%8.3f%8.3f%8.3f' % (d['atmx'], d['atmy'], d['atmz'])
				fi='%6.2f                \n' % (d['fi'])
				fipdbf.write(header+coord+fi)
		if self.verbose: sys.stdout.write('%s was writen' % fipdbfile)

	def _griddimcalc(self, listcoord, spacing, gridmargin):
		"""Determination of the grid dimension"""
		coordmin = min(listcoord) - gridmargin
		coordmax = max(listcoord) + gridmargin
		adjustment = ((spacing - (coordmax - coordmin)) % spacing) / 2.
		coordmin = coordmin - adjustment
		coordmax = coordmax + adjustment
		ngrid = int(round((coordmax - coordmin) / spacing))
		return coordmin, coordmax, ngrid

	def _dubost(self, fi, d, n):
		return (fi / (1 + d)).sum()

	def _testa(self, fi, d, n):
		return (fi * numpy.exp(-d/2)).sum()
		
	def _fauchere(self, fi, d, n):
		return (fi * numpy.exp(-d)).sum()

	def _brasseur(self, fi, d, n):
		#3.1 division is there to remove any units in the equation
		#3.1A is the average diameter of a water molecule (2.82 -> 3.2)
		return (fi * numpy.exp(-d/3.1)).sum()

	def _buckingham(self, fi, d, n):
		return ( fi / (d**n)).sum()

	def _type5(self, fi, d, n):
		return (fi * numpy.exp(-numpy.sqrt(d))).sum()

	def calculatefimap(self, method, spacing, nexp):
		"""Calculation loop"""
		atoms=[]
		for d in self.data:
			if  d['fi']:
				atoms.append(Atom(d['atmx'], d['atmy'], d['atmz'], d['fi']))
		#grid settings in angstrom
		gridmargin = Defaults().gridmargin
		xmingrid, xmaxgrid, nxgrid = self._griddimcalc([a.x for a in atoms],
			spacing, gridmargin)
		ymingrid, ymaxgrid, nygrid = self._griddimcalc([a.y for a in atoms],
			spacing, gridmargin)
		zmingrid, zmaxgrid, nzgrid = self._griddimcalc([a.z for a in atoms],
			spacing, gridmargin)
		self.spacing = spacing
		self.griddim = (nxgrid+1, nygrid+1, nzgrid+1)
		self.gridcoord = [[xmingrid, xmaxgrid],
						[ymingrid, ymaxgrid],
						[zmingrid, zmaxgrid]]
		if self.verbose: sys.stdout.write(
					"\nGrid dimension (angstroms):\n"
					"coord : min       max       ngrid\n"
					"    x : %8.4f %8.4f %8i\n"
					"    y : %8.4f %8.4f %8i\n"
					"    z : %8.4f %8.4f %8i\n\n" %(xmingrid, xmaxgrid, nxgrid,
					ymingrid, ymaxgrid, nygrid, zmingrid, zmaxgrid, nzgrid))

		coordatms = numpy.zeros((len(atoms),3),float)
		fiatms = numpy.zeros((len(atoms)),float)
		for p in range(len(atoms)):
			coordatms[p] = [atoms[p].x, atoms[p].y, atoms[p].z]
			fiatms[p] = atoms[p].fi

		self.pot = numpy.zeros((nxgrid+1, nygrid+1, nzgrid+1), float)
		gridsize = (nxgrid+1) * (nygrid+1) * (nzgrid+1)

		coordgridpts = numpy.zeros((nxgrid+1, nygrid+1, nzgrid+1,3), float)
		for i in range(nxgrid+1):
			for j in range(nygrid+1):
				for k in range(nzgrid+1):
					xgrid = xmingrid + i * spacing
					ygrid = ymingrid + j * spacing
					zgrid = zmingrid + k * spacing
					coordgridpts[i,j,k]=[xgrid, ygrid, zgrid]

		if self.verbose:
			sys.stdout.write('\nGrid Points Coordinates evaluated\n\n')

		if method == 'dubost':
			computemethod = self._dubost
		elif method == 'fauchere':
			computemethod = self._fauchere
		elif method == 'brasseur':
			computemethod = self._brasseur
		elif method == 'buckingham':
			computemethod = self._buckingham
		elif method == 'testa':
			computemethod = self._testa
		elif method == 'type5':
			computemethod = self._type5
		else:
			sys.stderr.write('You should never come here !\n')

		counter = 0.
		for i in range(nxgrid+1):
			for j in range(nygrid+1):
				for k in range(nzgrid+1):
			#Evaluation of the distance between th grid point and each atoms
					dist = numpy.sqrt(((coordgridpts[i,j,k,]
										- coordatms[:,])**2).sum(1))

					self.pot[i,j,k] = computemethod(fiatms, dist, nexp)

				counter += 1.
				if self.verbose:
					sys.stdout.write('\rCalculation in progress :'
							' %8.2f%%' % (counter*100/((nxgrid+1)*(nygrid+1))))

		if self.verbose:
			sys.stdout.write('\n\nMLPmin = %8.3f | MLPmax = %8.3f | '
								'MLPmean = %8.3f\n\n' % (self.pot.min(),
									self.pot.max(), self.pot.mean()))

	def writedxfile(self, dxfile):
		"""Write a dx (openDX) file"""
		if not self.pot.any():
			sys.stderr.write('\nNo Data to write !\n\n')
			return
		try:
			dxf = file(dxfile,'w')
			dxf.write('#pyMLP output file\n'
					'#  \n'
					'#A computer once beat me at chess, \n'
					'#but it was no match for me at kick boxing.\n'
					'#  \n')
			dxf.write('object 1 class gridpositions counts '
					'%i %i %i\n' % self.griddim)
			gridmin = tuple([xyzmin[0] for xyzmin in self.gridcoord])
			dxf.write('origin %8.6e %8.6e %8.6e\n' % gridmin)
			dxf.write('delta %8.6e %8.6e %8.6e\n' % (self.spacing, 0., 0.))
			dxf.write('delta %8.6e %8.6e %8.6e\n' % (0., self.spacing, 0.))
			dxf.write('delta %8.6e %8.6e %8.6e\n' % (0., 0., self.spacing))
			dxf.write('object 2 class gridconnections counts '
					'%i %i %i\n' % self.griddim)
			nbtot = self.griddim[0]*self.griddim[1]*self.griddim[2]
			dxf.write('object 3 class array type double rank 0 items'
					' %i data follows\n' % nbtot)

			self.pot = self.pot.reshape(nbtot)
			for m in range(0, nbtot-nbtot%3, 3):
				val = tuple(self.pot[m:m+3])
				dxf.write('%8.6e %8.6e %8.6e\n' % val)
			if 0 < nbtot%3 < 3:
				for m in self.pot[nbtot-nbtot%3:nbtot]:
					dxf.write('%8.6e ' % m)
				dxf.write('\n')

			dxf.write('attribute "dep" string "positions"\n'
					'object "regular positions regular connections" '
						'class field\n'
					'component "positions" value 1\n'
					'component "connections" value 2\n'
					'component "data" value 3\n')
		except IOError:
			sys.stderr.write('\nI tried to prevent it ... but writing the .dx'
							'file was not possible !')
		if self.verbose:
			sys.stdout.write('\nMolecular Lipophilic Potential Map '
								'saved in %s\n\nBye ...\n\n' % dxfile)


def main():
	"""pyMLP main function"""
	p = _CLIparsing()   #parsing the command line and getting options in p

	defaults = Defaults()
	fidata = defaults.fidatadefault
	if p.fitabfile:
		try:                  #import fidata if requested
			import imp
			fitabf = imp.load_source('fitabf', p.fitabfile)
			fidata = fitabf.fidata
			if p.verbose: sys.stdout.write("%s is compiled for internal use "
									"as %sc\n" % (p.fitabfile, p.fitabfile))
		except IOError:       #export fidata if requested
			if p.verbose: sys.stderr.write("Can't open %s ... "
			"using default values and creating a template\n" % p.fitabfile)
			writefitab(fidata, p.fitabfile, verbose=p.verbose)

	molec = Molecule(verbose=p.verbose)
	if p.pdbfile:
		if os.path.isfile(p.pdbfile):
			molec.parsepdb(p.pdbfile)
			molec.assignfi(fidata)
			if p.fipdbfile:
				if os.path.isfile(p.fipdbfile):
					if p.verbose: sys.stderr.write('%s already exists '
							'pyMLP will not overwrite it\n' % p.fipdbfile)
					pass
				else:
					molec.writefipdb(p.fipdbfile)
		else:
			if p.verbose: sys.stderr.write("Can't open %s ...\n" % p.pdbfile)
			sys.exit()
	elif p.fipdbfile:
		if os.path.isfile(p.fipdbfile):
			molec.parsepdb(p.fipdbfile, checkforfi=True)
		else:
			if p.verbose: sys.stderr.write("Can't open %s ...\n" % p.fipdbfile)
			sys.exit()
	else:
		sys.stderr.write('You should never come here !\n')

	if p.method != 'none':
		molec.calculatefimap(p.method, p.spacing, p.nexp)
		if p.dxfile:
			pass
		else:
			p.dxfile = molec.name+'.dx'
		if os.path.isfile(p.dxfile):
			timestamp = time.strftime('%Y-%m-%d_%H%M%S')
			bckpdxfile = p.dxfile+'.bckp_'+timestamp
			shutil.copy(p.dxfile, bckpdxfile)
			if p.verbose: sys.stdout.write('Old %s was backed up as %s\n' % (
											p.dxfile, bckpdxfile))
		molec.writedxfile(p.dxfile)
	else:
		if p.verbose:
			sys.stdout.write("pyMLP didn't calculate anything\n\n")


if __name__ == '__main__':
	sys.exit(main())
