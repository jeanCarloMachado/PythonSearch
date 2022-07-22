#!/bin/bash

destination_file=${LOG_FILE:-/tmp/debug}
echo "Check the results in the file: $destination_file"

echo "Start collecting info about command $(date)" > $destination_file
whereis python3 >>$destination_file
which python3 >>$destination_file

echo $(python3 -V) >> $destination_file
echo "Args $@" >> $destination_file

echo "Result below:" >>$destination_file
"$@" >>$destination_file 2>&1