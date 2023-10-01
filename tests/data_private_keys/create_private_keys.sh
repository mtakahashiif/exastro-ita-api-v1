#!/bin/bash

for sequence_number in "00" "10" "11" "12" "13" "14" "15" "16" "17" "18" "19" "20"; do
    echo "dummy private key (${sequence_number})" > "private-${sequence_number}.key"
done