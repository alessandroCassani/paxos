#!/usr/bin/env bash  

# Generate n random numbers, where 'n' is provided as a command-line argument

n="$1"   # Store the first command-line argument (number of random values) in variable 'n'

# Check if 'n' is empty (i.e., no argument was provided)
if [[ $n == "" ]]; then
    # If no argument is provided, print usage message and exit the script
    echo "Usage: $0 <number of values>"  # $0 is the name of the script
    exit  
fi

# Loop 'n' times to generate and print random numbers
for (( i = 0; i < $n; i++ )); do
    echo $RANDOM   
done
