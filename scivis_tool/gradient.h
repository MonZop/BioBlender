#ifndef __GRADFIELD
#define __GRADFIELD

#include <vector>

// potential field definition
#include "potential.h"

using namespace std;

//--------------------------------------------------------------------------
// gradient field class & helper functions
//--------------------------------------------------------------------------

class GradientField
{

public:

  Point3f* gradient;          // gradient data
  
  int dimx,dimy,dimz;         // grid dimension in cell#
  Point3f ggridorigin;        // grid origin
  Point3f ggridincrement;     // grid increment [X,Y,Z]
  
  float  maxgrad;             // maximum gradient intensity on the grid
  float  mingrad;             // minimum gradient intensity on the grid

  bool isvalid;               // true if data is valid  


//  creator  ---------------------------------------------------------------

GradientField()
{
  gradient = NULL;

  dimx = dimy = dimz = 0;
  ggridorigin = Point3f(0.0, 0.0, 0.0);
  ggridincrement = Point3f(0.0, 0.0, 0.0);

  maxgrad = -10000;
  mingrad =  10000;

  isvalid = false;
}

~GradientField()
{
  if(gradient != NULL)
    delete[] gradient;  // delete data, if present
}


//  initialization from a potential field ----------------------------------

bool intiFromPotential(PotentialGrid* potentialfield, int smoothsteps, float maxintensity)
{
 dimx = potentialfield->dimx;
 dimy = potentialfield->dimy;
 dimz = potentialfield->dimz;
 
 ggridorigin = potentialfield->potgridorigin;
 ggridincrement = potentialfield->potgridincrement;

 if(gradient != NULL)
    delete[] gradient;  // delete old data, if present

 // allocation
 gradient = new Point3f[dimx*dimy*dimz];

 // data filling
 int indx,indy,indz;
 float curr;
 float curr_xp, curr_yp, curr_zp;
 float deltax,deltay,deltaz;
 Point3f newgrad;
  

 // fill all points exept last slices 
 for(indx=0; indx<(dimx-1); indx++)
   for(indy=0; indy<(dimy-1); indy++)
     for(indz=0; indz<(dimz-1); indz++)
     {
      // gradient is Dx Dy Dz
      curr    = potentialfield->getPotentialAtCell(indx,   indy,   indz);
      curr_xp = potentialfield->getPotentialAtCell(indx+1, indy,   indz);
      curr_yp = potentialfield->getPotentialAtCell(indx,   indy+1, indz);
      curr_zp = potentialfield->getPotentialAtCell(indx,   indy,   indz+1);

      deltax = (curr_xp - curr) / ggridincrement.x();
      deltay = (curr_yp - curr) / ggridincrement.y();
      deltaz = (curr_zp - curr) / ggridincrement.z();

      gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)] = Point3f(deltax,deltay,deltaz);
     }

 
 // take care of the last slices
 indx = dimx-1;
 for(indy=0; indy<(dimy); indy++)
   for(indz=0; indz<(dimz); indz++)
     {
      gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)] = gradient[indz + ((indy)*dimz) + ((indx-1)*dimz*dimy)];
     }
 indy = dimy-1;
 for(indx=0; indx<(dimx); indx++)
   for(indz=0; indz<(dimz); indz++)
     {
      gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)] = gradient[indz + ((indy-1)*dimz) + ((indx)*dimz*dimy)];
     }
 indy = dimy-1;
 for(indx=0; indx<(dimx); indx++)
   for(indz=0; indz<(dimz); indz++)
     {
      gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)] = gradient[indz + ((indy-1)*dimz) + ((indx)*dimz*dimy)];
     }


 // check for off-scale values
 for(indx=1; indx<(dimx); indx++)
   for(indy=1; indy<(dimy); indy++)
     for(indz=1; indz<(dimz); indz++)
     {
       float len = gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)].Norm();
       if(len > maxintensity)
        {
          gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)].x() /= (len/maxintensity);
          gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)].y() /= (len/maxintensity);
          gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)].z() /= (len/maxintensity);
        }
     } 


 // smooth gradient
 for(int iter=0; iter<smoothsteps; iter++)
   smoothgradient();


 maxgrad = -10000;
 mingrad =  10000;
 for(indx=0; indx<(dimx); indx++)
   for(indy=0; indy<(dimy); indy++)
     for(indz=0; indz<(dimz); indz++)
     {
       float len = gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)].Norm();
       if(len > maxgrad)
         maxgrad = len;
       if(len < mingrad)
         mingrad = len;
     }


 isvalid = true;
 
 return true;
}

void smoothgradient()
{
 int indx,indy,indz;
 Point3f newgrad;
 Point3f *smgradient=NULL;

 // init smooth buffer
 smgradient = new Point3f[dimx*dimy*dimz];

   for(indx=1; indx<(dimx-1); indx++)
     for(indy=1; indy<(dimy-1); indy++)
       for(indz=1; indz<(dimz-1); indz++)
       {
        newgrad = Point3f(0.0, 0.0, 0.0);

        newgrad = newgrad + gradient[indz + ((indy)*dimz) + ((indx+1)*dimz*dimy)];   //xp
        newgrad = newgrad + gradient[indz + ((indy)*dimz) + ((indx-1)*dimz*dimy)];   //xm

        newgrad = newgrad + gradient[indz + ((indy+1)*dimz) + ((indx)*dimz*dimy)];   //yp
        newgrad = newgrad + gradient[indz + ((indy-1)*dimz) + ((indx)*dimz*dimy)];   //ym

        newgrad = newgrad + gradient[indz+1 + ((indy)*dimz) + ((indx)*dimz*dimy)];   //zp
        newgrad = newgrad + gradient[indz-1 + ((indy)*dimz) + ((indx)*dimz*dimy)];   //zm

        newgrad = newgrad / 6.0;
        smgradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)] = newgrad;
       }


   for(indx=1; indx<(dimx-1); indx++)
     for(indy=1; indy<(dimy-1); indy++)
       for(indz=1; indz<(dimz-1); indz++)
       {
         gradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)] = smgradient[indz + ((indy)*dimz) + ((indx)*dimz*dimy)];
       }

  // delete smooth buffer
  delete[] smgradient;
}

//  accessors  -------------------------------------------------------------

Point3f getGradientAtCell(int cellx, int celly, int cellz)
{
 return gradient[cellz + ((celly)*dimz) + ((cellx)*dimz*dimy)];
}

Point3f getGradientAt(Point3f position)
{
 Point3f retgradient;
 int cellx,celly,cellz;
 Point3f mmm,pmm,mpm,mmp,ppm,mpp,pmp,ppp;
 float wxp,wxm,wyp,wym,wzp,wzm;
 Point3f onz_xmym,onz_xpym,onz_xmyp,onz_xpyp;
 Point3f onx_yp,onx_ym;

 cellx = floor((position.x() - ggridorigin.x()) / ggridincrement.x());
 celly = floor((position.y() - ggridorigin.y()) / ggridincrement.y());
 cellz = floor((position.z() - ggridorigin.z()) / ggridincrement.z());

 mmm = gradient[cellz + ((celly)*dimz) + ((cellx)*dimz*dimy)];
 pmm = gradient[cellz + ((celly)*dimz) + ((cellx+1)*dimz*dimy)];
 mpm = gradient[cellz + ((celly+1)*dimz) + ((cellx)*dimz*dimy)];
 mmp = gradient[cellz+1 + ((celly)*dimz) + ((cellx)*dimz*dimy)];
 ppm = gradient[cellz + ((celly+1)*dimz) + ((cellx+1)*dimz*dimy)];
 mpp = gradient[cellz+1 + ((celly+1)*dimz) + ((cellx)*dimz*dimy)];
 pmp = gradient[cellz+1 + ((celly)*dimz) + ((cellx+1)*dimz*dimy)];
 ppp = gradient[cellz+1 + ((celly+1)*dimz) + ((cellx+1)*dimz*dimy)];

 wxp = 1.0-(fabs(position.x() - (ggridorigin.x() + (ggridincrement.x()*(cellx+1)))))/ggridincrement.x();
 wxm = 1.0-(fabs(position.x() - (ggridorigin.x() + (ggridincrement.x()*(cellx)))))/ggridincrement.x();
 wyp = 1.0-(fabs(position.y() - (ggridorigin.y() + (ggridincrement.y()*(celly+1)))))/ggridincrement.y();
 wym = 1.0-(fabs(position.y() - (ggridorigin.y() + (ggridincrement.y()*(celly)))))/ggridincrement.y();
 wzp = 1.0-(fabs(position.z() - (ggridorigin.z() + (ggridincrement.z()*(cellz+1)))))/ggridincrement.z();
 wzm = 1.0-(fabs(position.z() - (ggridorigin.z() + (ggridincrement.z()*(cellz)))))/ggridincrement.z();

 // trilinear interp
 onz_xmym = (mmp * wzp)+(mmm * wzm);
 onz_xpym = (pmp * wzp)+(pmm * wzm);
 onz_xmyp = (mpp * wzp)+(mpm * wzm);
 onz_xpyp = (ppp * wzp)+(ppm * wzm);
 //------------
 onx_yp = (onz_xpyp * wxp)+(onz_xmyp * wxm);
 onx_ym = (onz_xpym * wxp)+(onz_xmym * wxm);
 //------------
 retgradient = (onx_yp * wyp)+(onx_ym * wym);

 return retgradient;
}

//  line tools  ------------------------------------------------------------

void FollowLine(Point3f origin, vector<Point3f> *line, float limitgrad, float limitangle, int maxstep=200)
{
 int stepnum=0;
 bool valid = true;
 int cellx, celly, cellz;
 Point3f direction;
 Point3f oldpoint;
 Point3f newpoint;
 int sign=-1;
 bool anglecheck = false;
 float maxangle = 0.0;
 bool stallcheck = false;
 float mingradient = 0.0;

 // use step angle as halting condition
 if(limitangle != 90.0)
 {
  anglecheck = true;
  maxangle = cos((limitangle)*3.14159265/180.0);
 }

 // use stalling as halting condition
 if(limitgrad > 0.0)
 {
  stallcheck = true;
  mingradient = limitgrad;
 }

 // calculate integration step as half of the cell diagonal
 float inc = ggridincrement.Norm() / 2.0;
 // BUT never allow integration step to be larger than a threshold
 if (inc>0.75)
   inc = 0.75;

 //clear line structure
 line->clear();
 // origin is the starting point
 line->push_back(origin);

 for(sign=-1; sign<=1; sign=sign+2)
 {
  stepnum = 1;
  valid = true;

  while((valid)&&(stepnum<=maxstep))
  {
   if(sign == -1)
    oldpoint = line->front();
   if(sign ==  1)
    oldpoint = line->back();

   cellx = floor((oldpoint.x() - ggridorigin.x()) / ggridincrement.x());
   celly = floor((oldpoint.y() - ggridorigin.y()) / ggridincrement.y());
   cellz = floor((oldpoint.z() - ggridorigin.z()) / ggridincrement.z());

   if((cellx<(dimx-1))&&(celly<(dimy-1))&&(cellz<(dimz-1))&&(cellx>1)&&(celly>1)&&(cellz>1))
   {
    direction = getGradientAt(oldpoint);
    // check for too much acceleration
    if(direction.Norm() > inc)
     direction = direction.Normalize() * inc;
    direction = direction * sign;

    newpoint.x() = oldpoint.x() + (direction.x());
    newpoint.y() = oldpoint.y() + (direction.y());
    newpoint.z() = oldpoint.z() + (direction.z());

    if(sign ==  -1)
     line->insert(line->begin(),newpoint);
    if(sign ==  1)
     line->push_back(newpoint);

    stepnum++;
   }
   else // out of bounds
   {
    valid = false;
   }


   // angle check (if too sudden curve, halt)
   if((anglecheck)&&(line->size()>=3))
   {
    float stepangle;
    Point3f last,middle,old,olddir,newdir;

    if(sign == -1)
    {
      last   = (*line)[0];
      middle = (*line)[1];
      old    = (*line)[2];
    }
    if(sign ==  1)
    {
      last   = (*line)[line->size()-1];
      middle = (*line)[line->size()-2];
      old    = (*line)[line->size()-3];
    }

    olddir = (middle-old).Normalize();
    newdir = (last-middle).Normalize();
    stepangle = newdir * olddir;

    if(stepangle<maxangle)
    {
     valid = false;
    }
   }

   // stall check (if gradient too small, halt)
   if(stallcheck)
   {
    if(direction.Norm()<mingradient)
    {
     valid = false;
    }
   }
  }
 }

}


};  // end class
//--------------------------------------------------------------------------

#endif
