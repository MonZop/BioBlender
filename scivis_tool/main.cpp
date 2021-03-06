
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

// custom libraries
#include "Point3f.h"          // helper for 3d points
#include "mesh.h"             // helper for 3d mesh
#include "potential.h"        // management of DX potential grid
#include "gradient.h"         // management of gradient field over DX potential grid, line extraction


//-----------------------------------------------------------------------------------------------
//------ map the potential to each mesh vertex and face --------
bool potentialMeshMapping(Mesh *molmesh, PotentialGrid *molpot)
{
  int vv,ff;
  float currentPot=0;
  float area = 0.0;

  // for each mesh vertex
  for(vv=0; vv<molmesh->vn; vv++)
  {
    currentPot = molpot->getPotentialAt(molmesh->verts[vv].P);
    molmesh->verts[vv].pot = currentPot;
  }

  // for each mesh face, compute area-weighted potential
  for(ff=0; ff<molmesh->fn; ff++)
  {
    currentPot=0;
    area = molmesh->getFaceArea(ff);

    currentPot += ( fabs(molmesh->verts[molmesh->faces[ff].v[0]].pot) * area) /3.0;
    currentPot += ( fabs(molmesh->verts[molmesh->faces[ff].v[1]].pot) * area) /3.0;
    currentPot += ( fabs(molmesh->verts[molmesh->faces[ff].v[2]].pot) * area) /3.0;

    molmesh->faces[ff].pot = currentPot;
  }

  return true;
}
//-----------------------------------------------------------------------------------------------

//-----------------------------------------------------------------------------------------------
//------ calculate the number of lines --------
int calclinesnum(Mesh *molmesh, float linesdensity)
{
  int ff;
  float totalpotential=0.0;

  // for each mesh face, compute area-weighted potential
  for(ff=0; ff<molmesh->fn; ff++)
  {
    totalpotential += molmesh->faces[ff].pot;
  }

  printf("combined power value %f\n",totalpotential);

  // you cant have more lines than number of faces :)
  return min(molmesh->fn,int(totalpotential * linesdensity));
}
//-----------------------------------------------------------------------------------------------

//-----------------------------------------------------------------------------------------------
//------ sample the faces to find suitable line seeds --------
int fillseeds(Mesh *molmesh, vector<Point3f>   *seeds, int seednum)
{
  int ff;
  int foundseeds=0;
  float maxvalue = -10000;

  srand((unsigned)time(NULL));  

  // initialize as ALL faces
  foundseeds = molmesh->fn;
  for(ff=0; ff<molmesh->fn; ff++)
  {
    molmesh->faces[ff].seed = true;

    if(molmesh->faces[ff].pot > maxvalue)
      maxvalue = molmesh->faces[ff].pot;
  }    

  // pruning until correct seed number is reached
  ff=0;
  float limit,extracted;
  while(foundseeds > seednum)
  {
    while (molmesh->faces[ff].seed == false)
    {
      ff++;
      if(ff>=molmesh->fn)
        ff = ff%molmesh->fn;
    }

   // limit = molmesh->faces[ff].pot;
   // extracted = (float(rand()) / float(RAND_MAX)) * maxvalue * 0.25;

   limit = (molmesh->faces[ff].pot / maxvalue);
   limit = pow(limit, 1.5f);
   extracted = (float(rand()) / float(RAND_MAX));

    if(extracted > limit)
    {
      // discarding face
      molmesh->faces[ff].seed = false;

      foundseeds--;
    }

    // go to another random face
    ff += 1;//int((float(rand()) / float(RAND_MAX)) * (molmesh->fn / 100.0));
    if(ff>=molmesh->fn)
    {
      ff = ff%molmesh->fn;
    }
  }
  printf("line seeds found\n");

  // fill seeds vector
  for(ff=0; ff<molmesh->fn; ff++)
  {
    if (molmesh->faces[ff].seed == true)
    {
      Point3f seedpoint(0.0, 0.0, 0.0); 

      seedpoint += molmesh->verts[molmesh->faces[ff].v[0]].P;
      seedpoint += molmesh->verts[molmesh->faces[ff].v[1]].P;
      seedpoint += molmesh->verts[molmesh->faces[ff].v[2]].P;

      seedpoint = seedpoint / 3.0;

      seedpoint += molmesh->faces[ff].N;

      seeds->push_back(seedpoint);
    }
  }    

  return foundseeds;    
}
//-----------------------------------------------------------------------------------------------

//-----------------------------------------------------------------------------------------------
//------ simplify the lines --------
void simplifylines(vector< vector<Point3f> >  *lines, float angle)
{
  float minangle = cos(angle * 3.14159265 / 180.0);
  float thisangle;

  Point3f coming;
  Point3f going;
  bool deleted;

  int line_ind;
  int point_ind;

  int removed=0;
  int remaining;

  //for each line
  for(line_ind=0; line_ind<lines->size(); line_ind++)
  {
    deleted=true;

    //until we find no more to be deleted
    while(deleted)
    {
      deleted=false;

      // always keep the first and last
      for(point_ind=1; point_ind<(*lines)[line_ind].size()-2; )
      {
        // calculate angle at line point
        coming = ((*lines)[line_ind])[point_ind] - ((*lines)[line_ind])[point_ind-1];
        going  = ((*lines)[line_ind])[point_ind+1] - ((*lines)[line_ind])[point_ind];
        coming = coming.Normalize();
        going = going.Normalize();
        thisangle = coming * going;

        if(thisangle>minangle) // useless, delete and go ahead 2 (skip the next in line)
        {
          ((*lines)[line_ind]).erase((((*lines)[line_ind]).begin())+point_ind); 
          deleted = true;
          removed++;
          point_ind +=2;
        }
        else // useful, go ahead
        {
          point_ind++;
        }
      }
    }
  }

  // counting remaining points
  //for each line
  remaining=0;
  for(line_ind=0; line_ind<lines->size(); line_ind++)
  {
    remaining += (*lines)[line_ind].size();
  }

  printf("Removed: %d points, remaining: %d points\n", removed, remaining);

}
//-----------------------------------------------------------------------------------------------

//-----------------------------------------------------------------------------------------------
//------ save the lines --------
void savelines(vector< vector<Point3f> >  *lines, char* filename)
{
  FILE* outpf;
  int lind, linep;
  float xx,yy,zz;

  outpf = fopen(filename, "w");

  for (lind=0; lind<lines->size(); lind++) 
  {
    fprintf(outpf,"n\n");
    for (linep=(*lines)[lind].size()-1; linep>=0 ; linep--) 
    {
      xx = ((*lines)[lind])[linep].x();
      yy = ((*lines)[lind])[linep].y(); 
      zz = ((*lines)[lind])[linep].z();
      fprintf(outpf,"v %f %f %f\n",xx,yy,zz);
    }
  }

  fclose(outpf);
}
//-----------------------------------------------------------------------------------------------


//-DEBUG FUNCTION--DEBUG FUNCTION--DEBUG FUNCTION--DEBUG FUNCTION--DEBUG FUNCTION--DEBUG FUNCTION-
//------ save the seeds --------
void saveseeds(vector<Point3f>   *seeds)
{
  FILE* outpf;
  int ii;
  float xx,yy,zz;

  outpf = fopen("seeds.obj", "w");

  for(ii=0; ii<seeds->size(); ii++) 
  {
    xx = ((*seeds)[ii]).x();
    yy = ((*seeds)[ii]).y(); 
    zz = ((*seeds)[ii]).z();
    fprintf(outpf,"v %f %f %f\n",xx,yy,zz);
  }

  fclose(outpf);
}
//-----------------------------------------------------------------------------------------------





int main (int argc, const char * argv[])
{
  char meshfilename[1024];            // mesh file name
  char potentialfilename[1024];       // dx potential file name
  char linesfilename[1024];           // output file name

  float linesdensity;                 // line density, expressed as XXX over XXXXX

  float haltgradient;                 // minimal gradient size for line propagation
  float haltangle;                    // maximum angle for line propagation (avoid running into field irregularities)

  bool reducelines;                   // if true, lines are simplified before exporting
  float reducelinesangle;             // max angle change in simplification

  //---------------------------------------

  Mesh           moleculeMesh;        // the mesh
  PotentialGrid  moleculePotential;   // potential
  GradientField  moleculeGradient;    // gradient

  //---------------------------------------

  int linesnumber = 0;
  vector<Point3f>   lines_seeds;      // seed for the potential lines
  vector< vector<Point3f> >  lines;   // potential lines

  //---------------------------------------

  bool debug_mode = true;


  printf("--- SCIVIS --- Potential Lines Tool - V 2.0\n\n");

  //---- parameters parsing ----
  if(argc < 9)
  {
    printf("\ntoo few parameters\n");
    printf("USAGE: scivis 3dmeshfilename DXfilenamne linesfilename linesdensity haltgradient haltangle reduce reduceangle\n\n");
    printf("3dmeshfilename     3d mesh to load, obj format\n");
    printf("DXfilenamne        potential grid, DX format\n");
    printf("linesfilename      output file name for lines, txt format\n");
    printf("linesdensity       lines density, as # of lines per Ev/squareAngstrom, float\n");
    printf("haltgradient       stop line if a gradient lower than this is found, float\n");
    printf("haltangle          stop line if an angle larger than this is encountered, float\n");
    printf("reduce             simplify lines before exporting, 1=yes 0=no\n");
    printf("reduceangle        maxim angular change in simplification, float\n");
    printf("\nEXAMPLE: scivis calmodulin.obj calmodulin_EP.DX output_lines.txt 0.01 0.0 45 1 3.0\n\n");
    return -1;  
  }

  strcpy(meshfilename, argv[1]);
  strcpy(potentialfilename, argv[2]);
  strcpy(linesfilename, argv[3]);

  linesdensity = atof(argv[4]);

  haltgradient = atof(argv[5]);
  haltangle = atof(argv[6]);

  if(strcmp(argv[7],"1")==0)
    reducelines = true;
  else
    reducelines = false;

  reducelinesangle = atof(argv[8]);

  if((argc == 10) && (strcmp(argv[9],"1")==0)) // secret parameter
  {
    debug_mode = true;
    printf("\n DEBUG MODE \n\n");
  }
  else
    debug_mode = false;

  //---- loading model ----
  {
    printf("loading OBJ model: %s\n", meshfilename);
    moleculeMesh.loadOBJ(meshfilename);
    printf("loaded OBJ model: %d faces, %d verts\n", moleculeMesh.fn, moleculeMesh.vn);

    moleculeMesh.calcFaceNormals();
    moleculeMesh.calcVertexNormals();

    if(debug_mode)
    {
      moleculeMesh.saveOBJ("saved.obj");
      moleculeMesh.saveOBJ_norms("saved_n.obj");
    }
  }

  //---- loading potential ----
  {
    printf("loading potential DX grid: %s\n", potentialfilename);
    moleculePotential.loadDX(potentialfilename);
    printf("loaded DX potential: %d x %d x %d\n\n", moleculePotential.dimx, moleculePotential.dimy, moleculePotential.dimz);
  }

  //---- data setup ----
  {
    // mapping potential on mesh vertices
    potentialMeshMapping(&moleculeMesh, &moleculePotential);
    printf("mapped potential on the mesh\n");        

    // generate gradient 
    moleculeGradient.intiFromPotential(&moleculePotential, 3, 6.0); 
    printf("computed gradient: %d x %d x %d, max %f min %f\n", moleculeGradient.dimx, moleculeGradient.dimy, moleculeGradient.dimz, moleculeGradient.maxgrad, moleculeGradient.mingrad);
  }

  //---- lines calculation ----
  {
    // how many lines we need ?
    linesnumber = calclinesnum(&moleculeMesh, linesdensity);
    printf("%d lines will be calculated\n", linesnumber);   

    // starting point selection 
    lines_seeds.clear();
    fillseeds(&moleculeMesh, &lines_seeds, linesnumber);
    if(debug_mode)
      saveseeds(&lines_seeds);

    // lines computation
    lines.clear();
    for (int lind=0; lind<linesnumber; lind++) 
    {
      vector<Point3f> newline;
      newline.clear();

      lines.push_back(newline);

      moleculeGradient.FollowLine(lines_seeds[lind], &(lines.back()), haltgradient, haltangle);
    }
    printf("lines calculated\n");            
  }

  //---- lines saving ----
  {
    if(reducelines)
      simplifylines(&lines, reducelinesangle);

    savelines(&lines, linesfilename);
    printf("lines saved\n");            
  }

  return 0;
}

/*



*/



