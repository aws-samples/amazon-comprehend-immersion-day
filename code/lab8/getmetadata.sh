#!/bin/bash

declare -a mdata=(`cat universities.txt`)
len=${#mdata[@]}
echo "Generate metadata for ${len} pages"
ll=`cat .metalog`
echo "Starting from ${ll}"
ii=$ll
until [ $ii -gt $len ]
do
    echo "Working on $ii"
    pids=""
    for m in "${mdata[@]:${ii}:10}"
    do 
        echo "Working on $m"
        python3 getpagemetadata.py "Data/$m.txt" > "Meta/Data/$m.txt.metadata.json" &
	pids="$pids $!"
    done
    for p in "$pids"
    do
	if wait $p
	then
	    echo "Successful completion at ${ii}"
	else
	    echo "Exiting at ${ii}"
	    exit 1
	fi
    done
    echo ${ii} > .metalog
    ((ii=ii+10))
done
