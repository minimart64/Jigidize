#!/usr/bin/env python3

import pygame, sys, pickle
import time, os, shutil, imghdr

#directory paths
localDir = '/home/pi/Downloads' # parent of local filders
photosDir = '/home/pi/Documents/Photos'
localGoodDir = localDir + '/img/good' # classified good
localBadDir = localDir + '/img/bad' # classified bad
buDir = '/media/pi/storage/Stuff/classified' # long term storage parent 
buGoodDir = buDir + '/good'
buBadDir = buDir + '/bad'
stagingDir = '/home/pi/Documents/staging' # for jigidize
imgDir = localDir + '/img'
cneeingDir = '/home/pi/Documents/cneeing'
cneedDir = '/home/pi/Documents/cneed'
imageSigsFile = '/home/pi/Documents/logs/imageSigs'

# check to see if arguments were passed in with the command
inputValues = sys.argv # 0 is this script, 1 and 2 are inputs
inputDir = imgDir
inputFunction = 'F'

if len(inputValues) > 1: # 1 extra argument was entered
    if inputValues[1] == '-a': # dedupeGlobal all
        inputFunction = 'A'
    elif inputValues[1] == '-m': # routine dedupe and move files around
        inputFunction = 'M'
    elif inputValues[1] =='-h': # help
        print("-f for folder, -g for global followed by the path to dedupe. \
            -a for all, -m for dedupe and move")
        raise SystemExit
    elif inputValues[1] == '-f' or inputValues[1] == '-g': 
        if len(inputValues) == 2:
            print("These switches need to be followed by a path")
            raise SystemExit
    else: 
        print("invalid argument")
        raise SystemExit
if len(inputValues) > 2: # 2 or more extra arguments were entered
    inputDir = inputValues[2]
    # need to validate path
    # first clean it up a little
    if inputDir.startswith('~'):
        inputDir = '/home/pi' + inputDir[1:]
    elif not inputDir.startswith('/'):
        inputDir = '/' + inputDir
    else: # not sure what else could go wrong
        inputDir = inputDir
    # now check to see if it's a real path
    if os.path.isdir(inputDir):
        print(inputDir)
    elif os.path.isdir('/home/pi' + inputDir):
        inputDir = '/home/pi' + inputDir
    elif os.path.isdir(localDir + inputDir):
        inputDir = localDir + inputDir
    elif os.path.isdir(buDir + inputDir):
        inputDir = buDir + inputDir
    else: # nothing works... it's bad
        print("The directory you specified is not valid")
        raise SystemExit
    if inputValues[1] == '-f':
        inputFunction = 'F'
    elif inputValues[1] == '-g':
        inputFunction = 'G'
    else:
        print("invalid argument")
        raise SystemExit
else: # no input values, we assume -f imgDir
    inputDir = imgDir
    inputFunction = 'F'
   

def getFeatures(pic):
    picture = pygame.image.load(pic)
    # resize the pic
    picName = pic.split('/')[-1]
    w = picture.get_width()
    h = picture.get_height()
    picString = pygame.image.tostring(picture, 'RGB')
    l = len(picString)
    s = sum(picString)
    a = s/l
    # print(str(w)+', '+str(h)+', '+str(l)+', '+str(s)+', '+picName)
    features = (w, h, l, s, a, picName)
    return features

def loadList(listFile):
    # loads codeList from listFile
    print("loading list file " + listFile)
    with open(listFile, 'rb') as fp:
        codeList = pickle.load(fp)
    print("This list has " + str(len(codeList)) + " codes")
    return codeList

def writeList(codeList, listFile):
    # saves codeList to listFile
    with open(listFile, 'wb') as fp:
        pickle.dump(codeList, fp)

def moveFiles():
    # moves files from the local classified folders to storage
    # if a file already exists in storage, delete it instead
    badList = os.listdir(buBadDir)
    fileList = os.listdir(localBadDir)
    for pic in fileList:
        try:
            badList.index(pic)
        except:
            shutil.copy(localBadDir + '/' + pic, buBadDir)
        finally:
            os.remove(localBadDir + '/' + pic)
    goodList = os.listdir(buGoodDir)
    fileList = os.listdir(localGoodDir)
    for pic in fileList:
        try:
            goodList.index(pic)
        except:
            shutil.copy(localGoodDir + '/' + pic, buGoodDir)
        finally:
            os.remove(localGoodDir + '/' + pic)

def cleanDir(targetDir):
    # remove files from targetDir that are not jpg or png
    # get directories from bu and check for duplicates
    if targetDir == buGoodDir:
        goodList = ()
    elif targetDir == buBadDir:
        goodList = os.listdir(buGoodDir)
    else:
        goodList = os.listdir(buGoodDir)
        badList = os.listdir(buBadDir)
        goodList.extend(os.listdir(buBadDir))
    print('good list count ' + str(len(goodList)))
    fileList = os.listdir(targetDir)
    renamed = removed = 0
    for img in fileList:
        try:
            goodList.index(img) # if its in the list, we delete it
            print('duplicate ' + img)
            os.remove(targetDir + '/' + img)
            removed += 1
        except:
            if os.path.isfile(targetDir + '/' + img):
                splits = img.split('?') # if name contains a ? we rename it
                if len(splits) >1:
                    os.rename(targetDir + '/' + img, targetDir + '/' + splits[0])
                    img = splits[0]
                    renamed += 1
                if not img.endswith(".jpg") and not img.endswith(".png") \
                    and not img.endswith(".jpeg"):
                    fileType = imghdr.what(targetDir + '/' + img)
                    if fileType not in ('jpeg', 'jpg', 'png'):
                        print("bad one " + img + ' - ' + str(fileType))
                        os.remove(targetDir + '/' + img)
                        removed += 1
        finally:
            pass
    print('Renamed-' + str(renamed) + ', Removed-' + str(removed))

def dedupeGlobal(targetDir):
    # checks file features against list of files that have been published
    # files that match signatures are deleted
    # files that do not match are moved to photos directory 
    # and added to the list  
    print("globally deduping the folder " + targetDir)
    removed = 0   
    try: 
        imageSignatures = loadList(imageSigsFile)
    except:
        imageSignatures = []
    finally:
        if targetDir == buGoodDir:
            imageSignatures = []
        writeList(imageSignatures, imageSigsFile)
    fileList = os.listdir(targetDir)
    for img in fileList:
        if os.path.isfile(targetDir + '/' + img):
            try:
                picSig = getFeatures(targetDir + '/' + img)
                matched = False
                for i in imageSignatures:
                    if picSig[-1] == i[-1]:
                        print(img + ' is a duplicate')
                        matched = True
                        break
                    elif picSig[0:-1] == i[0:-1]:
                        print(img+' is the same as '+i[-1])
                        matched = True
                        break
                if matched:
                    os.remove(targetDir + '/' + img)
                    removed += 1
                else:
                    imageSignatures.append(picSig)
            except:
                print('invalid file: ' + img)
            finally:
                pass
    print('images in the set ' + str(len(imageSignatures)))
    print('Removed '+ str(removed) +' duplicates')
    writeList(imageSignatures, imageSigsFile)

def dedupeFolder(targetDir):
    # gets features for images in the directory and builds the list
    # if a duplicate is found, it is deleted
    # does not retain the list
    print("deduping the folder " + targetDir)
    removed = 0   
    imageSignatures = []
    fileList = os.listdir(targetDir)
    for img in fileList:
        if os.path.isfile(targetDir + '/' + img):
            try:
                picSig = getFeatures(targetDir + '/' + img)
                matched = False
                for i in imageSignatures:
                    if picSig[0:-1] == i[0:-1]:
                        print(img+' is the same as '+i[-1])
                        os.remove(targetDir + '/' + img)
                        removed += 1
                        matched = True
                        break
                if not matched:
                    imageSignatures.append(picSig)
            except:
                print('invalid file: ' + img)
            finally:
                pass
    print('images in the set ' + str(len(imageSignatures)))
    print('Removed '+ str(removed) +' duplicates')
    writeList(imageSignatures, imageSigsFile)

#-----------------#
# Code starts here
#-----------------#

if inputFunction == 'F':
    dedupeFolder(inputDir)
elif inputFunction == 'G':
    if inputDir == buBadDir:
        dedupeGlobal(buGoodDir)
        dedupeGlobal(buBadDir)
    else:
        dedupeGlobal(inputDir)
elif inputFunction == 'A':
    print("deduping everything")
    dedupeGlobal(buGoodDir)
    dedupeGlobal(buBadDir)
    dedupeGlobal(localGoodDir)
    dedupeGlobal(localBadDir)
    dedupeGlobal(imgDir)
elif inputFunction == 'M':
    print("dedupe and move")
    dedupeGlobal(localGoodDir)
    dedupeGlobal(localBadDir)
    dedupeGlobal(imgDir)
    moveFiles()
else:
    print("nothing to do") # this should not be possible

# all done
