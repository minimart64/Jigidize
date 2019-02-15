#!/usr/bin/env python3

import pygame, os, pickle, sys
pygame.init()

stagingFolder = '/home/pi/Documents/staging'
imageSigsFile = '/home/pi/Documents/logs/imageSigs'

#imageSignatures = []

def getFeatures(pic):
    picture = pygame.image.load(stagingFolder + '/' + pic)
    w = picture.get_width()
    h = picture.get_height()
    picString = pygame.image.tostring(picture, 'RGB')
    l = len(picString)
    # mx = max(picString) # always 255?
    # mn = min(picString) # always 0?
    s = sum(picString)
    a = s/l
    # print(str(w)+', '+str(h)+', '+str(a)+', '+str(l)+', '+pic)
    features = (w, h, a, pic)
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
    #codeText = '\n'.join(codeList) # put a newline between each item in the list
    #codeText = codeList # temporary line - fix me
    #fileOut = open(listFile, 'w') # open the file for writing
    #fileOut.write(codeText) # write the text to the file
    #fileOut.close() # save the file

try: 
    imageSignatures = loadList(imageSigsFile)
except:
    imageSignatures = []
finally:
    writeList(imageSignatures, imageSigsFile)

fileList = os.listdir(stagingFolder)

for img in fileList:
    if os.path.isfile(stagingFolder + '/' + img):
        picSig = getFeatures(img)
        matched = False
        for i in imageSignatures:
            if picSig[3] == i[3]:
                print(picSig[3] + ' is a duplicate')
                break
            elif picSig[0:3] == i[0:3]:
                print(picSig[3]+' is the same as '+i[3])
                # print(picSig)
                # print(i)
                matched = True
                break
        if not matched:
            # print('added '+picSig[3])
            imageSignatures.append(picSig)

# print(imageSignatures)
writeList(imageSignatures, imageSigsFile)
