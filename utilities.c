#include "utilities.h"

double parallel_dot (double *l_x, double *l_y, long l_n) {

  double l_d, d;

  l_d = serial_dot (l_x, l_y, l_n);
  MPI_Allreduce (&l_d, &d, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);

  return d;
}

double serial_dot (double *l_x, double *l_y, long l_n) {

  double l_d;
  long l_i;

  l_d = 0.0;
  for (l_i=0; l_i<l_n; l_i++) 
    l_d += l_x[l_i] * l_y[l_i];

  return l_d;
}

/* y = A*x: */
void matvec (double *l_y, double *l_A, double *l_x, 
             long l_n, long n, int id, int np, double *partial_y, double *y) {

  long i, l_j;

  /* partial_y = l_A * l_x: */
#ifdef BLAS
  cblas_dgemv(CblasColMajor,CblasNoTrans,
              n,l_n, 1.0,l_A,n, l_x,1, 0.0,partial_y,1);
#else
  for (i=0; i<n; i++)
    partial_y[i] = 0.0;
  for (l_j=0; l_j<l_n; l_j++) {
    for (i=0; i<n; i++) {
      partial_y[i] += l_A[i+n*l_j] * l_x[l_j];
    }
  }
#endif

  MPI_Allreduce(partial_y,y, n,MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
  // MPI_Scatter(y,l_n,MPI_DOUBLE, l_y,l_n,MPI_DOUBLE, 0,MPI_COMM_WORLD);
  // MPI_Reduce_scatter
  for (l_j=0; l_j<l_n; l_j++)
    l_y[l_j] = y[l_j + id*l_n];
  // or: memcpy(l_y,&(y[id*l_n]),l_n*sizeof(double));
  // or: memcpy(l_y,y+id*l_n,l_n*sizeof(double));

}

void print_vector (double *l_x, long l_n, long n, int id, int np) {

  long i;
  double *x;
  if(id==0) x = malloc(n*sizeof(double));

  MPI_Gather(l_x,l_n,MPI_DOUBLE, x,l_n,MPI_DOUBLE, 0, MPI_COMM_WORLD);
  
  if (id == 0) {
    for (i=0; i<n; i++)
      printf("%26.16e\n", x[i]);
  }

  if(id==0) free(x);
}

void print_matrix (double *l_A, long l_n, long n, int id, int np) {

  long i, j;
  double *A;
  if(id==0) A = malloc(n*n*sizeof(double));

  MPI_Gather(l_A,(n*l_n),MPI_DOUBLE, A,(n*l_n),MPI_DOUBLE, 0, MPI_COMM_WORLD);

  if (id == 0) {
    for (i=0; i<n; i++) {
      for (j=0; j<n; j++)
        printf("%10.4f", A[i+n*j]);
      printf("\n");
    }
  }

  if(id==0) free(A);
}

double my_power (double *l_A, double *l_x, int *iter, double tol, int itmax,
   long l_n, long n, int id, int np, double *l_y, double *partial_y, double *y, double *x) {

  double lambda;
  int it;
  long l_i, i;
  double err, lambdaold, normy;

  matvec (l_y, l_A, l_x, l_n, n, id, np, partial_y,y);
  err = tol + 1.0;
  it = 0;
  lambda = 0.0;
  while ( (err > tol) && (it < itmax) ) {
    it = it + 1;
    lambdaold = lambda;

    normy = sqrt(serial_dot(y,y,n)); // sqrt(parallel_dot(l_y,l_y,l_n));
    for (l_i=0; l_i<l_n; l_i++)
      l_x[l_i] = l_y[l_i] / normy;
    for (i=0; i<n; i++)
      x[i] = y[i] / normy;
    matvec (l_y, l_A, l_x, l_n, n, id, np, partial_y,y);
    lambda = serial_dot(x,y,n); // parallel_dot(l_x,l_y,l_n); // x' * y;

    err = fabs( (lambda-lambdaold) / lambda );
  }

  if (it == itmax)
    fprintf(stderr, "maximum number of iterations reached\n");
  *iter = it;

  return lambda;
}

