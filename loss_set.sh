#!/usr/bin/env bash   

# Store the first argument as 'LOSS', representing the packet loss percentage
LOSS="$1"

# Check if 'LOSS' is empty (i.e., no argument was provided)
if [[ x$LOSS == "x" ]]; then
    # If no argument is provided, display a usage message and exit with status 1
    echo "Usage: $0 <loss percentage (0.0 to 1.0)>"  # $0 refers to the script's name
    exit 1  # Exit with a non-zero status to indicate an error
fi

# Use 'iptables' to introduce packet loss for incoming traffic to the IP multicast group 239.0.0.1
# The packet loss probability is specified by the 'LOSS' variable
sudo iptables -A INPUT -d 239.0.0.1 -m statistic --mode random --probability $LOSS -j DROP
