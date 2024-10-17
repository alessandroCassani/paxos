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
# Proposer role
proposer_state = {'c-rnd': 0, 'c-val': None, 'ack_count': 0}

def proposer(config, id):
    print(f"Proposer {id} running")
    recv = mcast_receiver(config["proposers"])
    send = mcast_sender()

    proposer_state['c-rnd'] += 1
    send.sendto(f"PHASE1A {proposer_state['c-rnd']}".encode(), config["acceptors"])

    v_rnds, v_vals = []

    while True:
        msg = recv.recv(65536).decode().split()
        phase, rnd, v_rnd, v_val = msg[0], int(msg[1]), int(msg[2]), msg[3]

        # Phase 1B - Collect responses from acceptors
        if phase == "PHASE1B" and rnd == proposer_state['c-rnd']:
            v_rnds.append(v_rnd)
            v_vals.append(v_val if v_val != 'None' else None)

            if len(v_rnds) >= 2:  # Majority = 2 out of 3
                k = max(v_rnds)
                proposer_state['c-val'] = v_vals[v_rnds.index(k)] if k > 0 else proposer_state['c-val']
                send.sendto(f"PHASE2A {proposer_state['c-rnd']} {proposer_state['c-val']}".encode(), config["acceptors"])

        # Phase 2B - Handle acknowledgments from acceptors
        elif phase == "PHASE2B" and rnd == proposer_state['c-rnd']:
            proposer_state['ack_count'] += 1

            # If a majority of acceptors have acknowledged the value, notify learners (Phase 3)
            if proposer_state['ack_count'] >= 2:  # Majority = 2 out of 3
                print(f"Proposer {id}: Value {proposer_state['c-val']} accepted by majority")
                send.sendto(f"LEARN {proposer_state['c-val']}".encode(), config["learners"])
                proposer_state['ack_count'] = 0  # Reset for future rounds

# ----------------------------------------------------
def learner(config, id):
    print(f"Learner {id} running")
    recv = mcast_receiver(config["learners"])

    while True:
        msg = recv.recv(65536).decode().split()
        phase, v_val = msg[0], msg[1]

        if phase == "LEARN":
            print(f"Learner {id} learned value: {v_val}")
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
