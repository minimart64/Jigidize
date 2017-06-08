#! /bin/bash

# count of files in ~/Documents/Photos
# loop to repeat cnee call that many times
# cnee creates the puzzles
# jigidize then adds the new puzzle codes to the list (non-publish)

cd ~/Documents/Photos
declare -i count; count=0
for i in $(ls); do
cnee --replay --file ~/Documents/git/Jigidize/cneeScript.xns -force-core-replay
mv $i ~/Documents/cneed/
count+=1
echo $count
done
~/Documents/git/Jigidize/jigidize.py -x $count
