#!/usr/bin/env bash  

TEST="Test 3 - Learners learned every value that was sent by some client"

# Count the number of unique proposed values in 'prop.sorted'
PROP=$(cat prop.sorted | sort -u | wc -l)

# Loop over all files passed as arguments (learned values from learners)
for learned in $@; do
    # Count the number of unique learned values in each file
    LEARNED=$(cat $learned | sort -u | wc -l)
    
    # Check if the number of unique learned values does not match the number of proposed values
    if [[ $LEARNED != $PROP ]]; then
        # If a learner didn't learn all proposed values, print the test description and failure message, then exit with status 1
        echo "$TEST"
        echo "  > Failed!"
        exit 1  # Exit with a non-zero status to indicate failure
    fi
done

# If all learners learned every proposed value, print the test description and success message
echo "$TEST"
echo "  > OK"
