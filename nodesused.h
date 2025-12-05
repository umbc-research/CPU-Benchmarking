#ifndef NODESUSED_H
#define NODESUSED_H
#define _GNU_SOURCE

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include <sched.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#ifdef PARALLEL
#include <mpi.h>
#endif

void nodesused (void);

#endif

