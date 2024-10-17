#!/usr/bin/env python3
import sys
import socket
import struct
from collections import defaultdict

# Multicast receiver for setting up sockets
def mcast_receiver(hostport):
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    recv_sock.bind(hostport)

    # Join multicast group
    mcast_group = struct.pack("4sl", socket.inet_aton(hostport[0]), socket.INADDR_ANY)
    recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mcast_group)
    return recv_sock

# Multicast sender for sending messages
def mcast_sender():
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    return send_sock

# Parse the configuration file for roles and addresses
def parse_cfg(cfgpath):
    cfg = {}
    with open(cfgpath, "r") as cfgfile:
        for line in cfgfile:
            (role, host, port) = line.split()
            cfg[role] = (host, int(port))
    return cfg

# ----------------------------------------------------
# Acceptor variables
# Each acceptor needs to store its state
acceptor_state = defaultdict(lambda: {'rnd': 0, 'v-rnd': 0, 'v-val': None})

def acceptor(config, id):
    print(f"-> acceptor {id}")
    r = mcast_receiver(config["acceptors"])
    s = mcast_sender()

    while True:
        msg = r.recv(2**16).decode().split()
        phase, c_rnd = msg[0], int(msg[1])
        
        # Process PHASE 1A (prepare request)
        if phase == "PHASE1A":
            if c_rnd > acceptor_state[id]['rnd']:
                acceptor_state[id]['rnd'] = c_rnd
                response = f"PHASE1B {acceptor_state[id]['rnd']} {acceptor_state[id]['v-rnd']} {acceptor_state[id]['v-val']}"
                s.sendto(response.encode(), config["proposers"])
        
        # Process PHASE 2A (accept request)
        elif phase == "PHASE2A":
            c_val = msg[2]
            if c_rnd >= acceptor_state[id]['rnd']:
                acceptor_state[id]['v-rnd'] = c_rnd
                acceptor_state[id]['v-val'] = c_val
                response = f"PHASE2B {acceptor_state[id]['v-rnd']} {acceptor_state[id]['v-val']}"
                s.sendto(response.encode(), config["learners"])

# ----------------------------------------------------
# Proposer variables
proposer_state = {'c-rnd': 0, 'c-val': None}

def proposer(config, id):
    print(f"-> proposer {id}")
    r = mcast_receiver(config["proposers"])
    s = mcast_sender()
    proposer_state['c-rnd'] += 1  # Generate a unique round number

    # Send PHASE 1A (prepare) to acceptors
    s.sendto(f"PHASE1A {proposer_state['c-rnd']}".encode(), config["acceptors"])

    v_rnds = []
    v_vals = []

    while True:
        msg = r.recv(2**16).decode().split()
        phase, rnd, v_rnd, v_val = msg[0], int(msg[1]), int(msg[2]), msg[3] if msg[3] != 'None' else None

        # Collect responses from acceptors for PHASE 1B
        if phase == "PHASE1B" and rnd == proposer_state['c-rnd']:
            v_rnds.append(v_rnd)
            v_vals.append(v_val)

            # Once a majority of acceptors have replied
            if len(v_rnds) >= 2:  # Assuming a system with 3 acceptors (majority = 2)
                k = max(v_rnds)
                proposer_state['c-val'] = v_vals[v_rnds.index(k)] if k > 0 else proposer_state['c-val']

                # Propose the value by sending PHASE 2A to acceptors
                s.sendto(f"PHASE2A {proposer_state['c-rnd']} {proposer_state['c-val']}".encode(), config["acceptors"])

# ----------------------------------------------------
def learner(config, id):
    print(f"-> learner {id}")
    r = mcast_receiver(config["learners"])
    learned_values = {}

    while True:
        msg = r.recv(2**16).decode().split()
        phase, v_rnd, v_val = msg[0], int(msg[1]), msg[2]

        if phase == "PHASE2B":
            # Track votes
            if v_rnd not in learned_values:
                learned_values[v_rnd] = v_val

            # When majority votes for the same value, print it as the decided value
            if len(learned_values) >= 2:  # Assuming majority = 2 out of 3
                print(f"Learned: {v_val}")
                sys.stdout.flush()

# ----------------------------------------------------
def client(config, id):
    print(f"-> client {id}")
    s = mcast_sender()

    for value in sys.stdin:
        value = value.strip()
        print(f"client: sending {value} to proposers")
        s.sendto(value.encode(), config["proposers"])

    print("client done.")

# ----------------------------------------------------
if __name__ == "__main__":
    # Parse configuration and arguments
    cfgpath = sys.argv[1]
    config = parse_cfg(cfgpath)
    role = sys.argv[2]
    id = int(sys.argv[3])

    # Execute the correct role
    if role == "acceptor":
        rolefunc = acceptor
    elif role == "proposer":
        rolefunc = proposer
    elif role == "learner":
        rolefunc = learner
    elif role == "client":
        rolefunc = client

    rolefunc(config, id)
