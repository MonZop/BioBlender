//----------------- PUNTI -----------------------

#include <math.h>
#include <stdio.h>

#pragma once

class Point3f
{
protected:
	float	_v[3];

public:
	
	// Costruttori & assegnatori
	inline Point3f() 
	{
		_v[0] = 0;
		_v[1] = 0;
		_v[2] = 0;
	}

	inline Point3f( const float nx, const float ny, const float nz )
	{
		_v[0] = nx;
		_v[1] = ny;
		_v[2] = nz;
	}

	inline Point3f( Point3f const & p )
	{   
		_v[0]= p._v[0];
		_v[1]= p._v[1];
		_v[2]= p._v[2];
	}

	inline Point3f( const float nv[3] )
	{
		_v[0] = nv[0];
		_v[1] = nv[1];
		_v[2] = nv[2];
	}

	inline Point3f & operator =( Point3f const & p )
	{
		_v[0]= p._v[0]; 
		_v[1]= p._v[1]; 
		_v[2]= p._v[2]; 
		return *this;
	}

		// Accesso alle componenti
	inline const float &x() const { return _v[0]; } 
	inline const float &y() const { return _v[1]; }
	inline const float &z() const { return _v[2]; }
	inline float &x() { return _v[0]; }
	inline float &y() { return _v[1]; }
	inline float &z() { return _v[2]; }

	inline float & operator [] ( const int i )
	{
		return _v[i];
	}

	inline const float & operator [] ( const int i ) const
	{
		return _v[i];
	}

	// Operatori matematici di base
	inline Point3f operator + ( Point3f const & p) const
	{ 
		return Point3f( _v[0]+p._v[0], _v[1]+p._v[1], _v[2]+p._v[2] );
	}

	inline Point3f operator - ( Point3f const & p) const
	{
		return Point3f( _v[0]-p._v[0], _v[1]-p._v[1], _v[2]-p._v[2] );
	}

	inline Point3f operator * ( const float s ) const
	{
		return Point3f( _v[0]*s, _v[1]*s, _v[2]*s );
	}

	inline Point3f operator / ( const float s ) const
	{
		return Point3f( _v[0]/s, _v[1]/s, _v[2]/s );
	}

		// dot product
	inline float operator * ( Point3f const & p ) const
	{
		return ( _v[0]*p._v[0] + _v[1]*p._v[1] + _v[2]*p._v[2] );
	}  

		// Cross product
	inline Point3f operator ^ ( Point3f const & p ) const
	{
		return Point3f
		(
			_v[1]*p._v[2] - _v[2]*p._v[1],
			_v[2]*p._v[0] - _v[0]*p._v[2],
			_v[0]*p._v[1] - _v[1]*p._v[0]
		);
	}

	inline Point3f & operator += ( Point3f const & p)
	{
		_v[0] += p._v[0];
		_v[1] += p._v[1];
		_v[2] += p._v[2];
		return *this;
	}

	inline Point3f & operator -= ( Point3f const & p)
	{
		_v[0] -= p._v[0];
		_v[1] -= p._v[1];
		_v[2] -= p._v[2];
		return *this;
	}

	inline Point3f & operator *= ( const float s )
	{
		_v[0] *= s;
		_v[1] *= s;
		_v[2] *= s;
		return *this;
	}

	inline Point3f & operator /= ( const float s )
	{
		_v[0] /= s;
		_v[1] /= s;
		_v[2] /= s;
		return *this;
	}
    
	// Norme
	inline float Norm() const
	{
		return sqrt( _v[0]*_v[0] + _v[1]*_v[1] + _v[2]*_v[2] );
	}
    
	inline float SquaredNorm() const
	{
		return ( _v[0]*_v[0] + _v[1]*_v[1] + _v[2]*_v[2] );
	}

    // normalization
    inline Point3f Normalize() const
	{
        float norm = sqrt( _v[0]*_v[0] + _v[1]*_v[1] + _v[2]*_v[2]);
        return Point3f( _v[0]/norm, _v[1]/norm, _v[2]/norm );
	}


};
