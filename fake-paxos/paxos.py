#!/usr/bin/env python3
import sys
import socket
import struct


def mcast_receiver(hostport):
    """Create a multicast socket listening to the specified address"""
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # Create a UDP socket
    recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    recv_sock.bind(hostport)  # Bind to the specified host and port

    # Join the multicast group
    mcast_group = struct.pack("4sl", socket.inet_aton(hostport[0]), socket.INADDR_ANY)
    recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mcast_group)
    return recv_sock  # Return the configured receiving socket


def mcast_sender():
    """Create a UDP socket for sending messages"""
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    return send_sock  # Return the sending socket


def parse_cfg(cfgpath):
    """Parse the configuration file to extract roles and corresponding host/port mappings"""
    cfg = {}
    with open(cfgpath, "r") as cfgfile:
        for line in cfgfile:
            (role, host, port) = line.split()  # Split each line into role, host, and port
            cfg[role] = (host, int(port))  # Store the mapping in the config dictionary
    return cfg  # Return the parsed configuration


# ----------------------------------------------------


def acceptor(config, id):
    """Behavior of an acceptor process"""
    print("-> acceptor", id)
    state = {}  # Placeholder for future state management
    r = mcast_receiver(config["acceptors"])  # Set up a receiver for acceptor messages
    s = mcast_sender()  # Set up a sender to forward messages
    while True:
        msg = r.recv(2**16)  # Receive messages with a maximum size of 64KB
        # Fake acceptor: forwards messages to the learners
        if id == 1:
            # print "acceptor: sending %s to learners" % (msg)
            s.sendto(msg, config["learners"])  # Forward the message to the learners


def proposer(config, id):
    """Behavior of a proposer process"""
    print("-> proposer", id)
    r = mcast_receiver(config["proposers"])  # Set up a receiver for proposer messages
    s = mcast_sender()  # Set up a sender to forward messages
    while True:
        msg = r.recv(2**16)  # Receive messages with a maximum size of 64KB
        # Fake proposer: forwards messages to the acceptors
        if id == 1:
            # print "proposer: sending %s to acceptors" % (msg)
            s.sendto(msg, config["acceptors"])  # Forward the message to the acceptors


def learner(config, id):
    """Behavior of a learner process"""
    r = mcast_receiver(config["learners"])  # Set up a receiver for learner messages
    while True:
        msg = r.recv(2**16)  # Receive messages with a maximum size of 64KB
        print(msg)  # Print the received message (this could be a learned value)
        sys.stdout.flush()  # Flush the output to ensure immediate printing


def client(config, id):
    """Behavior of a client process"""
    print("-> client ", id)
    s = mcast_sender()  # Set up a sender to send messages to the proposers
    for value in sys.stdin:  # Read values from the standard input (client's input)
        value = value.strip()  # Remove any extra whitespace
        print("client: sending %s to proposers" % (value))
        s.sendto(value.encode(), config["proposers"])  # Send the value to the proposers
    print("client done.")  # Indicate the client is done sending


if __name__ == "__main__":
    # Main entry point of the script

    # Parse the configuration file and command-line arguments
    cfgpath = sys.argv[1]  # Path to the configuration file
    config = parse_cfg(cfgpath)  # Parse the configuration
    role = sys.argv[2]  # The role of the process (acceptor, proposer, learner, client)
    id = int(sys.argv[3])  # The ID of the process

    # Assign the appropriate role function based on the role
    if role == "acceptor":
        rolefunc = acceptor
    elif role == "proposer":
        rolefunc = proposer
    elif role == "learner":
        rolefunc = learner
    elif role == "client":
        rolefunc = client

    # Execute the corresponding role function
    rolefunc(config, id)
