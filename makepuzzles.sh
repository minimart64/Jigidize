#! /bin/bash

# count of files in the photos directory
# loop to repeat cnee call that many times
# cnee creates the puzzles
# jigidize then adds the new puzzle codes to the list

# open a browser window
# chromium-browser http://wwwljigidi.cim/create.php
# probably need to click the log-in button
# make it full screen

# set the field separator to enable filenames with spaces
SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

# create bonus puzzles
cd ~/Documents/Photos
declare -i count; count=0
for i in $(ls); do
    mv $i ~/Documents/cneeing/
    cnee --replay --file ~/Documents/git/jigidize/cneeScript.xns -force-core-replay --err-file ~/Documents/logs/cnee.log
    mv ~/Documents/cneeing/$i ~/Documents/cneed/
    count+=1
    echo $i
    echo $count
    # if we have made 24 puzzles, stop to get them from jigidi before we make more
    # if ((count==24)); then
    #    echo "Jigidizing 24"
    #    ~/Documents/git/jigidize/jigidize.py -x 24
    #    count=0
    #fi
done

if ((count>0)); then
    echo "Jigidizing the rest"
    ~/Documents/git/jigidize/jigidize.py -x $count
fi

# create public puzzles
cd ~/Documents/PhotosPublic
declare -i count; count=0
for i in $(ls); do
    mv $i ~/Documents/cneeing/
    cnee --replay --file ~/Documents/git/jigidize/cneeScriptPub.xns -force-core-replay --err-file ~/Documents/logs/cneepub.log
    mv ~/Documents/cneeing/$i ~/Documents/cneed/
    count+=1
    echo $count
done
if ((count>0)); then
    echo "Jigidizing pubs"
    ~/Documents/git/jigidize/jigidize.py -xp $count
fi

# create private puzzles
cd ~/Documents/PhotosPrivate
declare -i count; count=0
for i in $(ls); do
    mv $i ~/Documents/cneeing/
    cnee --replay --file ~/Documents/git/jigidize/cneeScriptPriv.xns -force-core-replay --err-file ~/Documents/logs/cneepub.log
    mv ~/Documents/cneeing/$i ~/Documents/cneed/
    count+=1
    echo $count
done
if ((count>0)); then
    echo "Jigidizing pubs"
    ~/Documents/git/jigidize/jigidize.py -x $count priv
fi

# set field separator back to spaces
IFS=$SAVEIFS

echo "clean up the lists"
~/Documents/git/jigidize/listvalidate.py
