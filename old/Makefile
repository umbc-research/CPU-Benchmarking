OBJS := main.o memory.o utilities.o nodesused.o check_memory.o diag_time.o

EXECUTABLE := power

# choose compiler:
CC := mpiicc
# CC := gcc

# choose flags:
# flags for Intel compiler icc on taki:
#CFLAGS := -O3 -std=c99 -Wall -qmkl
CFLAGS := -O3 -std=c99 -Wall -ipo -axCORE-AVX2,CORE-AVX512 -qmkl
# flags for GNU compiler gcc anywhere:
# CFLAGS := -O3 -std=c99 -Wall -Wno-unused-variable

DEFS := -DPARALLEL # -DBLAS
INCLUDES :=
LDFLAGS := -lm

%.o: %.c %.h
	$(CC) $(CFLAGS) $(DEFS) $(INCLUDES) -c $< -o $@

$(EXECUTABLE): $(OBJS)
	$(CC) $(CFLAGS) $(DEFS) $(INCLUDES) $(OBJS) -o $@ $(LDFLAGS)

clean:
	-rm -f *.o $(EXECUTABLE)

