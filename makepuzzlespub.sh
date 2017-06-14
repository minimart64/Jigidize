#! /bin/bash

# count of files in ~/Documents/Photos
# loop to repeat cnee call that many times
# cnee creates the puzzles
# jigidize then adds the new puzzle codes to the list
# this one creates public puzzles

cd ~/Documents/PhotosPublic
declare -i count; count=0
for i in $(ls); do
    mv $i ~/Documents/cneeing/
    cnee --replay --file ~/Documents/git/Jigidize/cneeScript.xns -force-core-replay
    mv ~/Documents/cneeing/$i ~/Documents/cneed/
    count+=1
    echo $count
    # if we have made 24 puzzles, stop to get them from jigid before we make more
    if ((count==24)); then
        echo "Jigidizing 24"
        ~/Documents/git/Jigidize/jigidize.py -xp 24
        count=0
    fi
done

echo "Jigidizing"
~/Documents/git/Jigidize/jigidize.py -xp $count
