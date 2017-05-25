#! /bin/bash

# count of files in ~/Documents/Photos
# loop to repeat cnee call that many times

for i in $(ls ~/Documents/Photos); do
cnee --replay --file cneeScript.xns -force-core-replay
mv $i ~/Documents/cneed/
done

