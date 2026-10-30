import os
import sys
import time
import json
import platform
from mpi4py import MPI

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    node_name = platform.node()

    if size < 2:
        if rank == 0:
            print("ERROR: This benchmark requires at least 2 MPI processes across 2 nodes.")
        sys.exit(1)

    # Gather hostnames across ranks
    hostnames = comm.allgather(node_name)
    server_node = hostnames[0]
    client_node = hostnames[1]

    # Buffer sizes: 1 Byte for Latency, 100 MB for Bandwidth
    lat_buffer = bytearray(1)
    bw_size = 100 * 1024 * 1024  # 100 MB
    bw_buffer = bytearray(bw_size)

    # 1. Latency Ping-Pong Test
    iterations_lat = 1000
    if rank == 0:
        # Warmup
        comm.send(lat_buffer, dest=1, tag=10)
        comm.recv(source=1, tag=11)

        t0 = time.perf_counter()
        for _ in range(iterations_lat):
            comm.send(lat_buffer, dest=1, tag=10)
            comm.recv(source=1, tag=11)
        t1 = time.perf_counter()

        avg_lat_us = round(((t1 - t0) / (iterations_lat * 2)) * 1e6, 2)

    elif rank == 1:
        # Warmup
        comm.recv(source=0, tag=10)
        comm.send(lat_buffer, dest=0, tag=11)

        for _ in range(iterations_lat):
            comm.recv(source=0, tag=10)
            comm.send(lat_buffer, dest=0, tag=11)

    # 2. Bandwidth Test
    iterations_bw = 20
    if rank == 0:
        t0 = time.perf_counter()
        for _ in range(iterations_bw):
            comm.send(bw_buffer, dest=1, tag=20)
            comm.recv(source=1, tag=21)
        t1 = time.perf_counter()

        total_bytes = bw_size * iterations_bw * 2  # Sent + Received
        elapsed = t1 - t0
        mbps = round((total_bytes / elapsed) / (1024 * 1024), 2)
        gbps = round((total_bytes * 8 / elapsed) / 1e9, 2)

        results = {
            "pair": f"{server_node}<->{client_node}",
            "server_node": server_node,
            "client_node": client_node,
            "avg_latency_us": avg_lat_us,
            "throughput_mbps": mbps,
            "throughput_gbps": gbps
        }

        print("\n--------------------------------------------------")
        print(f" HIGH-SPEED MPI NETWORK RESULT ({server_node} <-> {client_node})")
        print(f" Round-Trip Latency: {avg_lat_us} us")
        print(f" Throughput Speed:   {mbps} MB/s ({gbps} Gbps)")
        print("--------------------------------------------------\n")

        out_file = f"network_mpi_{server_node}_{client_node}.json"
        with open(out_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Saved JSON metrics to {out_file}")

    elif rank == 1:
        for _ in range(iterations_bw):
            comm.recv(source=0, tag=20)
            comm.send(bw_buffer, dest=0, tag=21)

if __name__ == "__main__":
    main()
