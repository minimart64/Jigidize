#! /bin/bash

# this file sets up dependencies and files/folders to support jigidize

# install lxml for page scraping
sudo apt-get install python3-lxml -y

# install xnee for makepuzzles
sudo apt-get install xnee -y

# make the config file - should I move it?
sudo mkdir /var/lib/jigidize
sudo chmod a+w /var/lib/jigidize
touch /var/lib/jigidize/config.cfg

# make logs folder and list files - should lists be in /logs?
mkdir /home/pi/Documents/logs
touch /home/pi/Documents/logs/puzzles
touch /home/pi/Documents/logs/puzzlesPublic
touch /home/pi/Documents/logs/newpuzzles
touch /home/pi/Documents/logs/newpuzzlespub
touch /home/pi/Documents/logs/newpuzzlespriv
touch /home/pi/Documents/logs/puzzleData
mkdir /home/pi/Documents/Photos
mkdir /home/pi/Documents/PhotosPublic
mkdir /home/pi/Documents/PhotosPrivate
mkdir /home/pi/Documents/cneeing
mkdir /home/pi/Documents/cneed
mkdir /home/pi/Documents/failures


