#include "main.h"

/* 09/12/02-10/10/02, updated 02/07/08 by Matthias K. Gobbert */

void setup_example (double *l_A, long n, long l_n, int id, int np)
{
  long i, j, l_j;

  /* example in global notation: A is n-by-n matrix with components
   * A(i,j)=1/(i+j-1) for i,j=1,...,n in 1-based mathematical counting or
   * A(i,j)=1/(i+j+1) for 0<=i,j<n in 0-based computer science counting
   */
  for (l_j = 0; l_j < l_n; l_j++)
    for (i = 0; i < n; i++)
    {
      j = l_j + id*l_n;
      l_A[i+l_j*n] = 1.0 / ((double) (i+j+1));
    }
  /* Note 1: loops ordered to access memory of l_A consecutively */
  /* Note 2: systematic choice of variable names and uses:
   * 0<=l_j<l_n is the index into the local l_A,
   * j is the mathematical index into the global A (not actually set up),
   * hence, j = l_j + id*l_n transforms l_j to j such that we get
   * id*l_n<=j<(id+1)*l_n on Process id.
   */
}

int main (int argc, char *argv[])
{
  int id, np; // , processor_name_len;
  // char processor_name[MPI_MAX_PROCESSOR_NAME];
  // char message[100];
  // MPI_Status status;
  long n;
  double v;
  long l_n;
  double *l_A, *l_x, *l_y;
  double *partial_y, *y, *x;
  double tol, lambda;
  int itmax, iter;
  long l_j, j;

  MPI_Init(&argc, &argv);

  /* Check processes: */
  MPI_Comm_size(MPI_COMM_WORLD, &np);
  MPI_Comm_rank(MPI_COMM_WORLD, &id);
  /*
  MPI_Get_processor_name(processor_name, &processor_name_len);
  sprintf(message, "Hello from %3d of %3d on %s", id, np, processor_name);
  if (id == 0) {
    printf("%s\n", message);
    for (i = 1; i < np; i++) {
      MPI_Recv(message, 100, MPI_CHAR, i, 0, MPI_COMM_WORLD, &status);
      printf("%s\n", message);
    }
  } else {
    MPI_Send(message, 1+strlen(message), MPI_CHAR, 0, 0, MPI_COMM_WORLD);
  }
  fflush(stdout);
  */

  /* test output of command-line: */
  /*
  if (id == 0) {
    printf("argc = %d\n", argc);
    for (i = 0; i < argc; i++) {
      printf("argv[%d] = %s\n", i, argv[i]);
    }
    printf("\n");
  }
  */

  /* process command-line inputs: */
  if (argc != 4)
  {
    if (id == 0)
    {
      printf ("Usage: \"./power n tol itmax\" \n");
      printf ("  with integer n, real tol, and integer itmax\n");
    }
    MPI_Abort (MPI_COMM_WORLD, 1);
  }
  n     = (long)atof(argv[1]);
  tol   =      atof(argv[2]);
  itmax =      atoi(argv[3]);
  v     =      atof(argv[1]);
  if (((double)n) != v)
  {
    if (id == 0)
      printf("Error: input must be integer! n = %ld, v = %f\n", n, v);
    MPI_Abort(MPI_COMM_WORLD, 1);
  }

  /* number of processes np must divide n: */
  if ( (n % np) != 0)
  {
    if (id == 0)
    {
      printf("Error: np must divide n!\n");
      printf("  n = %ld, np = %d, n%%np = %ld\n", n, np, (n%np));
    }
    MPI_Abort(MPI_COMM_WORLD, 1);
  }

  /* compute size of local blocks: */
  l_n = n / np;
  if (id == 0)
  {
    printf("n = %ld, l_n = %ld\n", n, l_n);
    printf("\n");
    fflush(stdout);
  }

  /* allocate storage: */
  l_A       = allocate_double_vector((n*l_n)); /* l_A is n-by-l_n */
  l_x       = allocate_double_vector(l_n);
  l_y       = allocate_double_vector(l_n);
  partial_y = allocate_double_vector(  n);
  y         = allocate_double_vector(  n);
  x         = allocate_double_vector(  n);

  /* setup example: */
  setup_example(l_A, n, l_n, id, np);

  /* choose default initial guess: */
  for (l_j = 0; l_j < l_n; l_j++)
    l_x[l_j] = 1.0 / sqrt((double)n);
  for (j = 0; j < n; j++)
    x[j] = 1.0 / sqrt((double)n);

  /*
  matvec (l_y, l_A,l_x, l_n, n, id, np, partial_y, y);

  double d = parallel_dot (l_x, l_x, l_n);
  if (id==0) {
    printf("d = x' * x = %24.16e\n", d);
  }
  d = parallel_dot (l_x, l_y, l_n);
  if (id==0) {
    printf("d = x' * y = %24.16e\n", d);
  }

  if (n < 25) {
    if (id==0) printf("x = \n");
    print_vector(l_x, l_n, n, id, np);
    printf("\n");
  }
  if (n < 25) {
    if (id==0) printf("y = \n");
    print_vector(l_y, l_n, n, id, np);
    printf("\n");
  }
  if (n <= 4) {
    if (id==0) printf("A = \n");
    print_matrix(l_A, l_n, n, id, np);
    printf("\n");
  }
  */

  MPI_Barrier(MPI_COMM_WORLD);
  double starttime = MPI_Wtime();
  lambda = my_power (l_A,l_x,&iter,tol,itmax,l_n, n,id,np,l_y,partial_y,y,x);
  MPI_Barrier(MPI_COMM_WORLD);
  double endtime = MPI_Wtime();
  double tsec = endtime - starttime;

  if (n < 25) {
    if (id==0) printf("x = \n");
    print_vector(l_x, l_n, n, id, np);
    printf("\n");
  }

  double resnormabs = -69.0, resnormrel = -69.0;
  /* resnormabs = ||A*x-lambda*x|| = ||y-lambda*x|| */
  for (l_j=0; l_j<l_n; l_j++)
    l_y[l_j] -= lambda * l_x[l_j]; // residual vector
  resnormabs = sqrt(parallel_dot(l_y,l_y,l_n));
  resnormrel = resnormabs / lambda;

  if(id==0) {
    printf("n = %ld, np = %d, l_n = %ld\n", n, np, l_n);
    printf("tol = %24.16e, itmax = %d, iter = %d\n", tol, itmax, iter);
    printf("lambda          = %24.16e\n", lambda);
    printf("resnormabs      = %24.16e\n", resnormabs);
    printf("resnormrel      = %24.16e\n", resnormrel);
    printf("time in seconds = %11.2f\n", tsec);
    diag_time(tsec);
  }

  /* log nodes used and memory usage */
  nodesused();
  diag_memory();
  MPI_Barrier(MPI_COMM_WORLD);

  free_vector(x);
  free_vector(y);
  free_vector(partial_y);
  free_vector(l_A);
  free_vector(l_x);
  free_vector(l_y);

  MPI_Finalize();

  return 0;
}

