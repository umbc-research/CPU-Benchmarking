#ifndef CHECK_MEMORY_H
#define CHECK_MEMORY_H

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <mpi.h>

void diag_memory();
long get_memory_usage_kb();
void get_cluster_memory_usage_kb(long* usage_vector, int root, int np);
long get_global_memory_usage_kb(int np);

#endif
