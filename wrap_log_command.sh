#!/usr/bin/env zsh

destination_file=${LOG_FILE:-/tmp/debug}
echo "Check the results in the file: $destination_file"

echo "Start collecting info about command $(date)" > $destination_file

# append from here on

echo "Sourcing config"
# source $HOME/config.sh
# export $($HOME/config.sh)
[ -f $HOME/config.sh ] && . $HOME/config.sh

echo "PATH: ${PATH}" >>$destination_file

echo "SHELL: ${SHELL}" >>$destination_file

echo "Python info" >>$destination_file
echo "whereis python $(whereis python3)" >>$destination_file
echo "which python $(which python3 )" >>$destination_file
echo "python3 -V: $(python3 -V)" >>$destination_file


echo "Args: $@" >> $destination_file

echo "Result below:" >>$destination_file
"$@" >>$destination_file 2>&1
