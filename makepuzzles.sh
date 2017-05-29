#! /bin/bash

# count of files in ~/Documents/Photos
# loop to repeat cnee call that many times
# cnee creates the puzzle and then copy-pastes the url into Geany

cd ~/Documents/Photos
for i in $(ls); do
cnee --replay --file ~/Documents/git/Jigidize/cneeScript.xns -force-core-replay
mv $i ~/Documents/cneed/
done

