#!/usr/bin/env bash   

# Run the script 'check1.sh' with two arguments 'learn1' and 'learn2'
./check1.sh learn1 learn2

# Concatenate the contents of 'prop1' and 'prop2', sort them, and save the output to 'prop.sorted'
cat prop1 prop2 | sort > prop.sorted

# Run the script 'check2.sh' with the same arguments 'learn1' and 'learn2'
./check2.sh learn1 learn2

# Run the script 'check3.sh' with the same arguments 'learn1' and 'learn2'
./check3.sh learn1 learn2
