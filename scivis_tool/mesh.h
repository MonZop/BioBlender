#ifndef __MESH
#define __MESH

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <vector>

using namespace std;

//structures declare 
struct face 
{
	int v[3];
	Point3f N;
    float pot;
    bool seed;
};

struct vert 
{
	Point3f P;
	Point3f N;
    float pot;
};



class Mesh
{

public:

    int vn;  // number of vertices
    int fn;  // number of faces
  
    vector<vert> verts;    // vertices array
    vector<face> faces;    // faces array

    bool isvalid;   // is the mesh valid ?
        
    //----------------- constructor / destructor
    
    Mesh()
    {
        verts.clear();
        faces.clear();
        vn=0;
        fn=0;
        
        isvalid = false;
    }
    
    ~Mesh()
    {
        isvalid = false;
        verts.clear();
        faces.clear();
    }
    
    //----------------- file i/o
    
    bool loadOBJ(char* filename)
    {
        FILE* inpf=NULL;
        int bytesRead;
        char justRead;
        char buffer[1024];
        int ii;
        
        inpf = fopen(filename,"r");
        if(inpf==NULL)
            return false;
        
        //new face data
        int v1,v2,v3;
        
        //new vertex data
        float xx,yy,zz;
        
        // mesh init
        vn = 0;
        fn = 0;
        verts.clear();
        faces.clear();
        
        
        
        do 
        {
            bytesRead= fread(&justRead, 1, 1, inpf);
         
            //----------------------------------------------- // comment
            if(justRead == '#')         
            {
                while((justRead != '\n') && (bytesRead>0))
                {
                    bytesRead= fread(&justRead, 1, 1, inpf);
                }
            }
            
            //----------------------------------------------- // not a vertex, not a face, ignore
            if((justRead != 'v')&&(justRead != 'f'))  
            {
                while((justRead != '\n') && (bytesRead>0))
                {
                    bytesRead= fread(&justRead, 1, 1, inpf);
                }
            }
            
            //----------------------------------------------- // face
            if(justRead == 'f')         
            {
                bytesRead= fread(&justRead, 1, 1, inpf); // skipping the space
                
                //v1
                bytesRead= fread(&justRead, 1, 1, inpf);
                ii=0;
                while((justRead != '/')&&(justRead != ' '))
                {
                    buffer[ii] = justRead;
                    bytesRead= fread(&justRead, 1, 1, inpf);
                    ii++;
                }
                while(justRead != ' ')
                    bytesRead= fread(&justRead, 1, 1, inpf);
                
                buffer[ii] = '\0';
                v1 = atoi(buffer);
                
                //v2
                bytesRead= fread(&justRead, 1, 1, inpf);
                ii=0;
                while((justRead != '/')&&(justRead != ' '))
                {
                    buffer[ii] = justRead;
                    bytesRead= fread(&justRead, 1, 1, inpf);
                    ii++;
                }
                while(justRead != ' ')
                    bytesRead= fread(&justRead, 1, 1, inpf);
                
                buffer[ii] = '\0';
                v2 = atoi(buffer);
                
                //v3
                bytesRead= fread(&justRead, 1, 1, inpf);
                ii=0;
                while((justRead != '/')&&(justRead != '\r')&&(justRead != '\n'))
                {
                    buffer[ii] = justRead;
                    bytesRead= fread(&justRead, 1, 1, inpf);
                    ii++;
                }
                while((justRead != '\r')&&(justRead != '\n'))
                    bytesRead= fread(&justRead, 1, 1, inpf);
                
                buffer[ii] = '\0';
                v3 = atoi(buffer);
                
                face newface;
                newface.v[0] = v1-1;
                newface.v[1] = v2-1;
                newface.v[2] = v3-1;
                newface.N[0] = 0.0;
                newface.N[1] = 0.0;
                newface.N[2] = 0.0;
                newface.pot  = 0.0;
                newface.seed = false;
                
                faces.push_back(newface);
                fn++;
                
                // last \n
                if(justRead != '\n')
                    bytesRead= fread(&justRead, 1, 1, inpf);
            }
            
            //----------------------------------------------- // vertex or normal or tcoord
            if(justRead == 'v')         
            {
                bytesRead= fread(&justRead, 1, 1, inpf);
                
                if(justRead == 'n')         // normal, skip
                {
                    do
                    {
                        bytesRead= fread(&justRead, 1, 1, inpf);
                    }
                    while(justRead != '\n');
                }
                
                if(justRead == 't')         // tcoord, skip
                {
                    do
                    {
                        bytesRead= fread(&justRead, 1, 1, inpf);
                    }
                    while(justRead != '\n');
                }
                
                if(justRead == ' ')         // vertex
                {
                    bytesRead= fread(&justRead, 1, 1, inpf);
                    ii=0;
                    while(justRead != ' ')  // X
                    {
                        buffer[ii] = justRead;
                        bytesRead= fread(&justRead, 1, 1, inpf);
                        ii++;
                    }
                    buffer[ii] = '\0';
                    xx = atof(buffer);
                    
                    
                    bytesRead= fread(&justRead, 1, 1, inpf);
                    ii=0;
                    while(justRead != ' ')  // Y
                    {
                        buffer[ii] = justRead;
                        bytesRead= fread(&justRead, 1, 1, inpf);
                        ii++;
                    }
                    buffer[ii] = '\0';
                    yy = atof(buffer);
                    
                    
                    bytesRead= fread(&justRead, 1, 1, inpf);
                    ii=0;
                    while((justRead != '\r')&&(justRead != '\n'))  // Z
                    {
                        buffer[ii] = justRead;
                        bytesRead= fread(&justRead, 1, 1, inpf);
                        ii++;
                    }
                    buffer[ii] = '\0';
                    zz = atof(buffer);
                    
                    
                    // pusho vertice
                    vert newvertex;
                    
                    newvertex.P[0] = xx;
                    newvertex.P[1] = yy;
                    newvertex.P[2] = zz;
                    newvertex.N[0] = 0.0;
                    newvertex.N[1] = 0.0;
                    newvertex.N[2] = 0.0;
                    newvertex.pot  = 0.0;

                    verts.push_back(newvertex);
                    vn++;                    
                    
                    // last \n
                    if(justRead != '\n')
                        bytesRead= fread(&justRead, 1, 1, inpf);
                }
            }
            
        } 
        while (bytesRead>0);

        fclose(inpf);
        isvalid = true;
        return true;
    }
    
    void saveOBJ(char* filename)
    {
        FILE* outpf;
        int vv,ff;
        
        outpf = fopen(filename,"w");
        
        for(vv=0; vv<vn; vv++)
        {
            fprintf(outpf,"v %f %f %f\n",	
                    verts[vv].P.x(),
                    verts[vv].P.y(),
                    verts[vv].P.z());
        }
        
        
        for(ff=0; ff<fn; ff++)
        {
            fprintf(outpf,"f %d %d %d\n",	
                    (faces[ff].v[0])+1,
                    (faces[ff].v[1])+1,
                    (faces[ff].v[2])+1);
        }
        
        fclose(outpf);
    }    
    
    void saveOBJ_norms(char* filename)
    {
        FILE* outpf;
        int vv,ff;
        
        outpf = fopen(filename,"w");
        
        for(vv=0; vv<vn; vv++)
        {
            fprintf(outpf,"v %f %f %f\n",	
                    verts[vv].P.x(),
                    verts[vv].P.y(),
                    verts[vv].P.z());
            fprintf(outpf,"vn %f %f %f\n",	
                    verts[vv].N.x(),
                    verts[vv].N.y(),
                    verts[vv].N.z());
        }
        
        
        for(ff=0; ff<fn; ff++)
        {
            fprintf(outpf,"f %d//%d %d//%d %d//%d\n",	
                    (faces[ff].v[0])+1,(faces[ff].v[0])+1,
                    (faces[ff].v[1])+1,(faces[ff].v[1])+1,
                    (faces[ff].v[2])+1,(faces[ff].v[2])+1);
        }
        
        fclose(outpf);
    }      
    
    //----------------- setup functions
    void calcFaceNormals()
    {
        int ff;
        
        for(ff=0; ff<fn; ff++)
            faces[ff].N = Point3f(0.0, 0.0, 0.0);        
        
        for(ff=0; ff<fn; ff++)
        {
            Point3f U = (verts[faces[ff].v[1]].P - verts[faces[ff].v[0]].P);
            Point3f V = (verts[faces[ff].v[2]].P - verts[faces[ff].v[0]].P);
            Point3f N = U ^ V;
            faces[ff].N = N.Normalize(); 
        }  
    }
    
    void calcVertexNormals()
    {
        int vv,ff;
        
        for(vv=0; vv<vn; vv++)
            verts[vv].N = Point3f(0.0, 0.0, 0.0);
      
        for(ff=0; ff<fn; ff++)
        {
            verts[faces[ff].v[0]].N += faces[ff].N;
            verts[faces[ff].v[1]].N += faces[ff].N;
            verts[faces[ff].v[2]].N += faces[ff].N;
        }
        
        for(vv=0; vv<vn; vv++)
            verts[vv].N = verts[vv].N.Normalize(); 
    }    
    
    //----------------- helper functions
    float getFaceArea(int facenum)
    {
        float area;
        
        Point3f U = (verts[faces[facenum].v[1]].P - verts[faces[facenum].v[0]].P);
        Point3f V = (verts[faces[facenum].v[2]].P - verts[faces[facenum].v[0]].P);
        Point3f N = U ^ V;
        area = N.Norm();
        
        area = area / 2.0;
        
        return area;
    }
    
    
};

#endif // __MESH