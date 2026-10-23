#include "nodesused.h"

#ifdef PARALLEL
void nodesused (void)
{
  int id, np;
  char name[MPI_MAX_PROCESSOR_NAME];
  int namelen;
  int sys_status;
  MPI_Status status;
  int i;
  int numThreads = 1, tid = 0;
  char message[128];
  FILE *fil, *fil_threads;
  char filename[128];
  char filename_threads[128];

  MPI_Comm_size (MPI_COMM_WORLD, &np);
  MPI_Comm_rank (MPI_COMM_WORLD, &id);
  MPI_Get_processor_name (name, &namelen);

  /* classical nodesused output with hostnames only: */
  sprintf(message, "MPI process %04d of %04d on node %4s", id, np, name);
  if (id == 0) {
    sprintf (filename, "nodesused.log");
    fil = fopen (filename, "w");
    if (fil == NULL)
    {
      fprintf (stderr, "nodesused: problem opening file %s\n", filename);
      MPI_Abort(MPI_COMM_WORLD, 1);
    }
    fprintf(fil, "%s\n", message);
    for (int j = 1; j < np; j++) {
        MPI_Recv(message, 128, MPI_CHAR, j, 0, MPI_COMM_WORLD, &status);
        fprintf(fil, "%s\n", message);
    }
    fflush (fil);
    fclose (fil);
  } else {
      MPI_Send(message, strlen(message)+1, MPI_CHAR, 0, 0, MPI_COMM_WORLD);
  }
  /* nodesused output with cpu ids: */
  sprintf (filename, "nodesused-%04d.log", id);
  fil = fopen (filename, "w");
  if (fil == NULL)
  {
    fprintf (stderr, "nodesused: problem opening file %s\n", filename);
    MPI_Abort(MPI_COMM_WORLD, 1);
  }
  fprintf(fil, "MPI process %04d of %04d on cpu_id %04d of node %4s\n",
  id, np, sched_getcpu(), name);
  MPI_Barrier(MPI_COMM_WORLD);
  fflush (fil);
  fclose (fil);
  /* combine all files nodesused-????.log to nodesused_cpuid.log: */
  MPI_Barrier(MPI_COMM_WORLD);
  if (id == 0) {
    sys_status = system ("sort -n nodesused-????.log > nodesused_cpuid.log");
    if (sys_status == -1)
      fprintf (stderr, "nodesused: problem with 'system' call\n");  
    fflush (stdout);
  }
  MPI_Barrier(MPI_COMM_WORLD);
  if (id == 0) {
    sys_status = system ("rm nodesused-????.log");
    if (sys_status == -1)
      fprintf (stderr, "nodesused: problem with 'system' call\n");  
    fflush (stdout);
  }
  MPI_Barrier(MPI_COMM_WORLD);
#ifdef _OPENMP
  sprintf (filename_threads, "nodesused_threads-%04d.log", id);
  fil_threads = fopen(filename_threads, "w");
  if(fil_threads == NULL)
  {
    fprintf (stderr, "nodesused: problem opening file %s\n", filename_threads);
    MPI_Abort(MPI_COMM_WORLD, 1);
  }
  #pragma omp parallel
  {
    fprintf(fil_threads,
    "MPI process %04d of %04d thread %04d of %04d on cpu_id %04d of node %4s\n",
    id, np, omp_get_thread_num(), omp_get_num_threads(),
    sched_getcpu(), name);
  }
  #pragma omp barrier
  fflush (fil_threads);
  fclose (fil_threads);
  /* combine all files nodesused_threads-????.log to nodesused_threads.log: */
  MPI_Barrier(MPI_COMM_WORLD);
  if (id == 0) {
    sys_status
      = system ("sort -n nodesused_threads-????.log > nodesused_threads.log");
    if (sys_status == -1)
      fprintf (stderr, "nodesused: problem with 'system' call\n");
    fflush (stdout);
  }
  MPI_Barrier(MPI_COMM_WORLD);
  if (id == 0) {
    sys_status = system ("rm nodesused_threads-????.log");
    if (sys_status == -1)
      fprintf (stderr, "nodesused: problem with 'system' call\n");
    fflush (stdout);
  }
  MPI_Barrier(MPI_COMM_WORLD);
#endif
}
#else
void nodesused (void)
{
  int sys_status;
  FILE *fil, *fil_threads;
  char filename[128];
  char filename_threads[128];
  int id;

  sprintf (filename, "nodesused.log");
  fil = fopen (filename, "w");
  if (fil == NULL)
  {
    fprintf (stderr, "nodesused: problem opening file %s\n", filename);  
    return;
  }

  sys_status = system ("hostname");
  if (sys_status == -1)
    fprintf (stderr, "nodesused: problem with 'system' call\n");  
  fflush (stdout);

#ifdef _OPENMP
  id = 0;
  sprintf (filename_threads, "nodesused_threads-%04d.log", id);
  fil_threads = fopen(filename_threads, "w");
  if(fil_threads == NULL)
  {
    fprintf (stderr, "nodesused: problem opening file %s\n", filename_threads);
    return;
  }
  #pragma omp parallel
  {
    fprintf(fil_threads,
    "Thread %04d of %04d on cpu_id %04d\n",
    omp_get_thread_num(), omp_get_num_threads(), sched_getcpu());
  }
  #pragma omp barrier
  fflush (fil_threads);
  fclose (fil_threads);
  /* combine all files nodesused_threads-????.log to nodesused_threads.log: */
  sys_status
    = system ("sort -n nodesused_threads-????.log > nodesused_threads.log");
  if (sys_status == -1)
    fprintf (stderr, "nodesused: problem with 'system' call\n");
  fflush (stdout);
  sys_status = system ("rm nodesused_threads-????.log");
  if (sys_status == -1)
    fprintf (stderr, "nodesused: problem with 'system' call\n");
  fflush (stdout);
#endif

  fclose (fil);
}
#endif

