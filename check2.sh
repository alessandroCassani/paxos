#!/usr/bin/env bash   

TEST="Test 2 - Values learned were actually proposed"

# Combine 'prop.sorted' and all files passed as arguments ($@), sort them uniquely, and count the number of unique lines
PROP_LEARNED=$(cat prop.sorted $@ | sort -u | wc -l)

# Sort the 'prop.sorted' file uniquely and count the number of unique lines
PROP=$(cat prop.sorted | sort -u | wc -l)

# Check if the number of unique learned values matches the number of unique proposed values
if [[ $PROP_LEARNED == $PROP ]]; then
    # If the counts match, print the test description and success message
    echo "$TEST"
    echo "  > OK"
else
    # If the counts don't match, print the test description and failure message
    echo "$TEST"
    echo "  > Failed!"
fi
