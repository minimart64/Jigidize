#!/usr/bin/env python3

import requests, lxml.html, sys, logging, logging.handlers, smtplib, configparser
import time, os, shutil, imghdr

photosDir = '/home/pi/Documents/Photos'
localGoodDir = '/home/pi/Downloads/img/good'
localBadDir = '/home/pi/Downloads/img/bad'
buGoodDir = '/media/pi/storage/Stuff/classified/good'
buBadDir = '/media/pi/storage/Stuff/classified/bad'
tempStorageDir = '/home/pi/Documents/staging'
imgDir = '/home/pi/Downloads/img'
cneeingDir = '/home/pi/Documents/cneeing'
cneedDir = '/home/pi/Documents/cneed'


def moveFiles():
    # moves files from the local classified folders to storage
    # if files already exist in storage, delete them
    # move good files to temp storage for final evaluation
    # clean out cneed and cneeing
    # log.info("Moving files around")
    badList = os.listdir(buBadDir)
    fileList = os.listdir(localBadDir)
    for pic in fileList:
        # log.debug("checking for bad file in storage: " + pic)
        try:
            badList.index(pic)
        except:
            # log.debug("Moving bad file to storage: " + pic)
            shutil.copy(localBadDir + '/' + pic, buBadDir)
        finally:
            os.remove(localBadDir + '/' + pic)
    goodList = os.listdir(buGoodDir)
    fileList = os.listdir(localGoodDir)
    for pic in fileList:
        # log.debug("checking for bad file in storage: " + pic)
        try:
            goodList.index(pic)
        except:
            # log.debug("Moving bad file to storage: " + pic)
            shutil.copy(localGoodDir + '/' + pic, buGoodDir)
            shutil.copy(localGoodDir + '/' + pic, tempStorageDir)
        finally:
            os.remove(localGoodDir + '/' + pic)

def cleanDir(targetDir):
    # remove files from targetDir that are not jpg or png
    fileList = os.listdir(targetDir)
    for img in fileList:
        splits = img.split('?') # if name contains a ? we rename it
        if len(splits) >1:
            print("rename "+ img + " to " + splits[0])
            os.rename(targetDir + '/' + img, targetDir + '/' + splits[0])
        try:
            if not img.endswith(".jpg") and not img.endswith(".png"):
                # if bad name fix it
                fileType = imghdr.what(targetDir + '/' + img)
                if fileType not in ('jpeg', 'jpg', 'png'):
                    print("bad one " + img + ' - ' + str(fileType))
                    os.remove(targetDir + '/' + img)
        except:
            print("directory "+img)
        finally:
            pass
            

def cleanCneed():
    # remove files from cneed and cneeing folders
    fileList = os.listdir(cneedDir)
    for pic in fileList:
        # log.debug("removing file from cneed: " + pic)
        os.remove(cneedDir + '/' + pic)
    fileList = os.listdir(cneeingDir)
    for pic in fileList:
        # log.debug("removing file from cneeing: " + pic)
        os.remove(cneeingDir + '/' + pic)

#moveFiles()
#cleanCneed()
cleanDir(imgDir)
