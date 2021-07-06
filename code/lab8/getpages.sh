#!/bin/bash

for m in `cat universities.txt`
do 
	echo "Getting https://en.wikipedia.org/wiki/${m}"
	lynx -dump "https://en.wikipedia.org/wiki/${m}" | grep -v :// | sed 's/\[.*\]//g' > "Data/${m}.txt"
done
