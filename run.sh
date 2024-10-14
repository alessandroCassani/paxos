#!/usr/bin/env bash

# Get the project directory and the number of values per proposer from command line arguments
projdir="$1"
conf="$(pwd)/paxos.conf"  # Set the configuration file path to the current working directory
n="$2"  # The number of values to generate for each proposer

# Check if the required arguments are provided
if [[ x$projdir == "x" || x$n == "x" ]]; then
    echo "Usage: $0 <project dir> <number of values per proposer>"  # Print usage instructions
    exit 1  # Exit the script with an error code
fi

# Kill any running processes that have the configuration file in their command line
pkill -f "$conf" 

# Change directory to the project directory provided as an argument
cd $projdir

# Generate two sets of proposed values and save them to prop1 and prop2
../generate.sh $n >../prop1  # Generate proposals for the first client
../generate.sh $n >../prop2  # Generate proposals for the second client

echo "starting acceptors..."  # Notify that acceptor processes are starting

# Start three acceptor processes in the background
./acceptor.sh 1 "$conf" &
./acceptor.sh 2 "$conf" &
./acceptor.sh 3 "$conf" &

# Wait for 1 second to ensure acceptors are up and running
sleep 1
echo "starting learners..."  # Notify that learner processes are starting

# Start two learner processes, redirecting their output to learn1 and learn2
./learner.sh 1 "$conf" >../learn1 &
./learner.sh 2 "$conf" >../learn2 &

# Wait for another second for learners to initialize
sleep 1
echo "starting proposers..."  # Notify that proposer processes are starting

# Start two proposer processes in the background
./proposer.sh 1 "$conf" &
./proposer.sh 2 "$conf" &

# Notify that the script is waiting for clients to start
echo "waiting to start clients"
sleep 10  # Wait for 10 seconds to ensure all previous processes are ready
echo "starting clients..."  # Notify that client processes are starting

# Start two client processes, providing them with the generated proposal values
./client.sh 1 "$conf" <../prop1 &  # Client 1 reads proposals from prop1
./client.sh 2 "$conf" <../prop2 &  # Client 2 reads proposals from prop2

# Wait for 5 seconds to allow clients to finish processing
sleep 5

# Kill any remaining processes associated with the configuration file
pkill -f "$conf"
wait  # Wait for all background jobs to finish

# Return to the previous directory
cd ..
