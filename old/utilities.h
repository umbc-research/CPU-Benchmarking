#ifndef UTILITIES_H
#define UTILITIES_H

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#ifdef PARALLEL
#include <mpi.h>
#endif

#ifdef BLAS
#include <mkl.h>
#endif

double parallel_dot (double *l_x, double *l_y, long l_n);
double serial_dot (double *l_x, double *l_y, long l_n);
void matvec (double *l_y, double *l_A, double *l_x,
             long l_n, long n, int id, int np, double *partial_y, double *y);
void print_vector (double *l_x, long l_n, long n, int id, int np);
void print_matrix (double *l_A, long l_n, long n, int id, int np);
double my_power (double *l_A, double *l_x, int *iter, double tol, int itmax,
    long l_n, long n, int id, int np, double *l_y, double *partial_y, double *y, double *x);

#endif
