#!/bin/bash

for sequence_number in "01" "02" "10" "11" "12" "13" "14" "15" "16" "17" "18" "19" "20" "21" "22" "23" "24" "25" "26" "27" "28" "29"; do
    echo "dummy private key (${sequence_number})" > "private-${sequence_number}.key"
done