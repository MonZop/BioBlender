#ifndef __POTFIELD
#define __POTFIELD

#include <stdio.h>
#include <math.h>


//--------------------------------------------------------------------------
// potential field class & helper functions
//--------------------------------------------------------------------------


class PotentialGrid
{

public:

  float* potential;           // potential data

  int dimx,dimy,dimz;         // grid dimension in cell#
  Point3f potgridorigin;      // grid origin
  Point3f potgridincrement;   // grid increment [X,Y,Z]
  
  float  maxpot;              // maximum potential on the grid
  float  minpot;              // minimum potential on the grid

  bool isvalid;               // true if data is valid

// creator ---------------------------------------------------------------------------

PotentialGrid()
{
  potential = NULL;

  dimx = dimy = dimz = 0;
  potgridorigin = Point3f(0.0, 0.0, 0.0);
  potgridincrement = Point3f(0.0, 0.0, 0.0);

  maxpot = -10000;
  minpot =  10000;

  isvalid = false;
}

~PotentialGrid()
{
 if(potential != NULL)
   delete[] potential;  // delete data, if present
}


// loader  ---------------------------------------------------------------------------

bool loadDX(char* filename)
{
  int count;
  float read;
  float rxx,ryy,rzz,garbage;
  char cc;
  FILE* inpf=NULL;

  inpf = fopen(filename,"r");
  if(inpf==NULL)
    return false;

  // -- header --

  // five rows initial comment
  fscanf(inpf,"%c",&cc);
  while (cc == '#')
  {
   for(cc='x'; cc != '\n'; )
    fscanf(inpf,"%c",&cc);

   fscanf(inpf,"%c",&cc);
  }

  // warning: the next few comments are only to show an actual example of the content of a DX file, 
  // to better understand the code, it is not the value i expect to read
    
  // garbage + 3 int (potsx, potsy, potsz)
  // object 1 class gridpositions counts 65 66 74
  fscanf(inpf,"bject 1 class gridpositions counts %d %d %d\n",&dimx,&dimy,&dimz);

  //grid origin
  //origin -2.358800e+001 -2.867600e+001 -5.454100e+001
  fscanf(inpf,"origin %f %f %f\n",&rxx,&ryy,&rzz);
  potgridorigin = Point3f(rxx, ryy, rzz);

  // grid increment
  //delta 1.000000e+000 0.000000e+000 0.000000e+000
  //delta 0.000000e+000 1.000000e+000 0.000000e+000
  //delta 0.000000e+000 0.000000e+000 1.000000e+000

  fscanf(inpf,"delta %f %f %f\n",&rxx,&garbage,&garbage);
  fscanf(inpf,"delta %f %f %f\n",&garbage,&ryy,&garbage);
  fscanf(inpf,"delta %f %f %f\n",&garbage,&garbage,&rzz);

  potgridincrement = Point3f(rxx, ryy, rzz);

  // two lines garbage
  //object 2 class gridconnections counts 65 66 74
  //object 3 class array type double rank 0 items 317460 data follows
  for(cc='x'; cc != '\n'; )
   fscanf(inpf,"%c",&cc);
  for(cc='x'; cc != '\n'; )
   fscanf(inpf,"%c",&cc);   


  // -- body --

  if(potential != NULL)
        delete[] potential;  // delete old data, if present

  // allocation
  potential = new float[dimx*dimy*dimz];
  maxpot = -1000000.0;
  minpot =  1000000.0;


  for(count = 0; count < (dimx*dimy*dimz); count++)
  {
    fscanf(inpf,"%f",&read);
    potential[count] = read;
    if(read<minpot)
     minpot=read;
    if(read>maxpot)
     maxpot=read;
  }

  fclose(inpf);

  isvalid = true;

  return true;
}



// accessors ---------------------------------------------------------------------------

float getPotentialAtCell(int cellx, int celly, int cellz)
{
 return potential[cellz + ((celly)*dimz) + ((cellx)*dimz*dimy)];
}


float getPotentialAt(Point3f position)
{
 float retpotential;
 int cellx,celly,cellz;
 float mmm,pmm,mpm,mmp,ppm,mpp,pmp,ppp;
 float wxp,wxm,wyp,wym,wzp,wzm;
 float onz_xmym,onz_xpym,onz_xmyp,onz_xpyp;
 float onx_yp,onx_ym;

 cellx = floor((position.x() - potgridorigin.x()) / potgridincrement.x());
 celly = floor((position.y() - potgridorigin.y()) / potgridincrement.y());
 cellz = floor((position.z() - potgridorigin.z()) / potgridincrement.z());

 mmm = potential[cellz + ((celly)*dimz) + ((cellx)*dimz*dimy)];
 pmm = potential[cellz + ((celly)*dimz) + ((cellx+1)*dimz*dimy)];
 mpm = potential[cellz + ((celly+1)*dimz) + ((cellx)*dimz*dimy)];
 mmp = potential[cellz+1 + ((celly)*dimz) + ((cellx)*dimz*dimy)];
 ppm = potential[cellz + ((celly+1)*dimz) + ((cellx+1)*dimz*dimy)];
 mpp = potential[cellz+1 + ((celly+1)*dimz) + ((cellx)*dimz*dimy)];
 pmp = potential[cellz+1 + ((celly)*dimz) + ((cellx+1)*dimz*dimy)];
 ppp = potential[cellz+1 + ((celly+1)*dimz) + ((cellx+1)*dimz*dimy)];

 wxp = 1.0-(fabs(position.x() - (potgridorigin.x() + (potgridincrement.x()*(cellx+1)))))/potgridincrement.x();
 wxm = 1.0-(fabs(position.x() - (potgridorigin.x() + (potgridincrement.x()*(cellx)))))/potgridincrement.x();
 wyp = 1.0-(fabs(position.y() - (potgridorigin.y() + (potgridincrement.y()*(celly+1)))))/potgridincrement.y();
 wym = 1.0-(fabs(position.y() - (potgridorigin.y() + (potgridincrement.y()*(celly)))))/potgridincrement.y();
 wzp = 1.0-(fabs(position.z() - (potgridorigin.z() + (potgridincrement.z()*(cellz+1)))))/potgridincrement.z();
 wzm = 1.0-(fabs(position.z() - (potgridorigin.z() + (potgridincrement.z()*(cellz)))))/potgridincrement.z();

 // trilinear interp
 onz_xmym = (wzp*mmp)+(wzm*mmm);
 onz_xpym = (wzp*pmp)+(wzm*pmm);
 onz_xmyp = (wzp*mpp)+(wzm*mpm);
 onz_xpyp = (wzp*ppp)+(wzm*ppm);
 //------------
 onx_yp = (wxp*onz_xpyp)+(wxm*onz_xmyp);
 onx_ym = (wxp*onz_xpym)+(wxm*onz_xmym);
 //------------
 retpotential = (wyp*onx_yp)+(wym*onx_ym);

 return retpotential;
}


};




//--------------------------------------------------------------------------

#endif