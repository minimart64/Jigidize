#!/usr/bin/env python3

import pygame, os, pickle, sys, time
pygame.init()

trainingDir = '/media/pi/storage/Stuff/classified/good'
imageSigsFile = '/home/pi/Documents/logs/imageSigs'


def getFeatures(pic):
    picture = pygame.image.load(trainingDir + '/' + pic)
    w = picture.get_width()
    h = picture.get_height()
    picString = pygame.image.tostring(picture, 'RGB')
    l = len(picString)
    s = sum(picString)
    a = s/l
    # print(str(w)+', '+str(h)+', '+str(l)+', '+str(s)+', '+pic)
    features = (w, h, l, s, a, pic)
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

startTime = time.time()
try: 
    imageSignatures = loadList(imageSigsFile)
except:
    imageSignatures = []
finally:
    writeList(imageSignatures, imageSigsFile)

fileList = os.listdir(trainingDir)

fileCount = 0
for img in fileList:
    if os.path.isfile(trainingDir + '/' + img):
        try:
            picSig = getFeatures(img)
            matched = False
            for i in imageSignatures:
                if picSig[-1] == i[-1]:
                    print(img + ' is a duplicate')
                    matched = True
                    break
                elif picSig[0:-1] == i[0:-1]:
                    print(img+' is the same as '+i[-1])
                    os.remove(trainingDir + '/' + img)
                    matched = True
                    break
            if not matched:
                # print('added '+picSig[3])
                imageSignatures.append(picSig)
        except:
            print('invalid file: ' + img)
        finally:
            fileCount += 1
            if (fileCount % 1000 == 0):
                print(fileCount)

print('images in the set ' + str(len(imageSignatures)))
writeList(imageSignatures, imageSigsFile)
elapsedTime = time.time() - startTime
print(elapsedTime)
