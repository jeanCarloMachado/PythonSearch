#!/bin/bash

file_name="$1"
mv $file_name ${file_name}init.without_bom ; printf '\xEF\xBB\xBF' | cat -  ${file_name}init.without_bom > $file_name

