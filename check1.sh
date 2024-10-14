#!/usr/bin/env bash  

TEST="Test 1 - Learners learned the same set of values in total order"

# Compare the two files passed as arguments ($1 and $2), and redirect any differences to 'test1.out'
diff "$1" "$2" >test1.out

# Check if 'test1.out' is non-empty (i.e., if the 'diff' found differences)
if [[ -s test1.out ]]; then
    # If 'test1.out' has content (indicating a difference), print the test description and failure message
    echo "$TEST"
    echo "  > Failed!"
else
    # If 'test1.out' is empty (no differences), print the test description and success message
    echo "$TEST"
    echo "  > OK"
    
    # Remove the 'test1.out' file since it's not needed 
    rm test1.out
fi
