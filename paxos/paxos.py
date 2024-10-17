#!/usr/bin/env python3
import sys
import socket
import struct
from collections import defaultdict
import PhaseMessage_pb2
import Message

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
acceptor_state = defaultdict(lambda: {'rnd': 0, 'v-rnd': 0, 'v-val': None})

def acceptor(config, id):
    print(f"-> acceptor {id} running")
    recv = mcast_receiver(config["acceptors"])
    send = mcast_sender()

    while True:
        data = recv.recv(65536)

        # Handling PHASE_1A messages
        try:
            msg = PhaseMessage_pb2.Phase1A()
            msg.ParseFromString(data)

            c_rnd = msg.c_rnd

            if c_rnd > acceptor_state[id]['rnd']:  # Update state if the round is higher
                acceptor_state[id]['rnd'] = c_rnd
                response = Message.phase_1b(acceptor_state[id]['rnd'], acceptor_state[id]['v-rnd'], acceptor_state[id]['v-val'], "PHASE_1B")
                send.sendto(response, config["proposers"])  # Respond to proposers

        except Exception as e:
            # Handle PHASE_2A messages
            try:
                msg = PhaseMessage_pb2.Phase2A()
                msg.ParseFromString(data)

                c_rnd = msg.c_rnd
                c_val = msg.c_val

                if c_rnd >= acceptor_state[id]['rnd']:  # Accept if the round is acceptable
                    acceptor_state[id]['v-rnd'] = c_rnd
                    acceptor_state[id]['v-val'] = c_val
                    response = Message.phase_2b(acceptor_state[id]['v-rnd'], acceptor_state[id]['v-val'], "PHASE_2B")
                    send.sendto(response, config["learners"])  # Respond to learners
            except Exception as e:
                print(f"Acceptor {id} received unknown message type or error: {e}")

# ----------------------------------------------------
# Proposer role
proposer_state = {'c-rnd': 0, 'c-val': None, 'ack_count': 0}

def proposer(config, id):
    print(f"Proposer {id} running")
    recv = mcast_receiver(config["proposers"])
    send = mcast_sender()

    proposer_state['c-rnd'] += 1
    send.sendto(Message.phase_1a(proposer_state['c-rnd'], "PHASE_1A"), config["acceptors"])

    v_rnds = []
    v_vals = []

    while True:
        data = recv.recv(65536)

        # Handling PHASE_1B messages
        try:
            msg = PhaseMessage_pb2.Phase1B()
            msg.ParseFromString(data)

            rnd = msg.rnd
            v_rnd = msg.v_rnd
            v_val = msg.v_val

            if rnd == proposer_state['c-rnd']:  
                v_rnds.append(v_rnd)
                v_vals.append(v_val)

                if len(v_rnds) >= 2:  # Quorum check
                    k = max(v_rnds)

                    if k > 0:
                        proposer_state['c-val'] = v_vals[v_rnds.index(k)]
                    else:
                        proposer_state['c-val'] = proposer_state['c-val']
                 
                    send.sendto(Message.phase_2a(proposer_state['c-rnd'], proposer_state['c-val'], "PHASE_2A"), config["acceptors"])

        except Exception as e:
            # Handling PHASE_2B messages
            try:
                msg = PhaseMessage_pb2.Phase2B()
                msg.ParseFromString(data)

                v_rnd = msg.v_rnd
                v_val = msg.v_val
            
                if v_rnd == proposer_state['c-rnd']:
                    proposer_state['ack_count'] += 1

                    if proposer_state['ack_count'] >= 2:  # Quorum check
                        print(f"Proposer {id}: Value {proposer_state['c-val']} accepted by quorum")
                        send.sendto(Message.decision(proposer_state['c-val'], "DECIDE"), config["learners"])
                        
                        proposer_state['ack_count'] = 0  # Reset
                        v_rnds.clear()
                        v_vals.clear()
            except Exception as e:
                print(f"Proposer {id} received unknown message type or error: {e}")

# ----------------------------------------------------
def learner(config, id):
    print(f"Learner {id} running")
    recv = mcast_receiver(config["learners"])

    while True:
        data = recv.recv(65536)

        try:
            msg = PhaseMessage_pb2.Decide()
            msg.ParseFromString(data)

            phase = msg.phase
            v_val = msg.v_val

            if phase == "DECIDE":
                print(f"Learner {id} learned value: {v_val}")
                sys.stdout.flush()
        except Exception as e:
            print(f"Learner {id} received unknown message type or error: {e}")

# ----------------------------------------------------
def client(config, id):
    print(f"-> client {id} running")
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
