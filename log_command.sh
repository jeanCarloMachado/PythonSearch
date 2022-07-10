#!/bin/bash

echo "Start collecting info about command $(date)" > /tmp/debug


whereis python3 >>/tmp/debug
which python3 >>/tmp/debug

echo $(python3 -V) >> /tmp/debug
echo "Args $@" >> /tmp/debug

echo "Result below" >> /tmp/debug
"$@"  2>>/tmp/debug