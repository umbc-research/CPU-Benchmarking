#include "check_memory.h"

void diag_memory() {
  int id, np;
  long *mem_usage_vector;
  long total_mem_used = 0;
  FILE *memfil;
  char filename[64];

  MPI_Comm_size (MPI_COMM_WORLD, &np);
  MPI_Comm_rank (MPI_COMM_WORLD, &id);

  mem_usage_vector = (long*)malloc(np*sizeof(long));
  get_cluster_memory_usage_kb(mem_usage_vector, 0, np);

  if (id == 0) {
    sprintf (filename, "memory.log");
    memfil = fopen (filename, "w");

    for (int p = 0; p < np; p++) {
      fprintf (memfil, "Process %04d:   %16li kB\n", p, mem_usage_vector[p]);
      total_mem_used += mem_usage_vector[p];
    }
    fprintf (memfil, "Overall usage:  %16li kB\n", total_mem_used);
    fclose (memfil);
  }
  free(mem_usage_vector);
}

// Look for a line in the procfile contents like: 
// VmRSS:		 5560 kB
//
// Grab the number between the whitespace and the "kB"
// If -1 is returned in the end, there was a serious problem 
// (we could not find the memory usage)
long get_memory_usage_kb()
{
	// Get the the current process' status file from the proc filesystem
	FILE* procfile = fopen("/proc/self/status", "r");

	long to_read = 8192;
	char buffer[to_read];
	int read = fread(buffer, sizeof(char), to_read, procfile);
	fclose(procfile);

	long local_kb = -1;
	char* search_result;

	// Look through proc status contents line by line
	char delims[] = "\n";
	char* line = strtok(buffer, delims);

	while (line != NULL && local_kb == -1)
	{
		search_result = strstr(line, "VmRSS:");
		if (search_result != NULL)
		{
			sscanf (line, "%*s %ld", &local_kb);
		}

		line = strtok(NULL, delims);
	}

	return local_kb;
}

void get_cluster_memory_usage_kb(long* usage_vector, int root, int np)
{
	long local_kb = get_memory_usage_kb();

	MPI_Gather(&local_kb, 1, MPI_UNSIGNED_LONG, 
		usage_vector, 1, MPI_UNSIGNED_LONG, 
		root, MPI_COMM_WORLD);
}

long get_global_memory_usage_kb(int np)
{
        int i;
	long memory_usage_vector[np];
	get_cluster_memory_usage_kb(memory_usage_vector, 0, np);

	long global_kb = 0;
	for (i = 0; i < np; i++)
	{
		global_kb += memory_usage_vector[i];
	}

	return global_kb;
}

