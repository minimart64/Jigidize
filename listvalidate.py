#!/usr/bin/env python3

# open the files, check for duplicates and remove them
# then check for codes that exist in both files and put them in a third file 

puzzleListFile = "/home/pi/Documents/logs/puzzles" # private
publishListFile = "/home/pi/Documents/logs/puzzlesPublic" # prod pi
duplicateListFile = "/home/pi/Documents/logs/duplicates"
newPuzzFile = "/home/pi/Documents/logs/newpuzzles" # private
newPubFile = "/home/pi/Documents/logs/newpuzzlespub" # public

def loadList(listFile):
    textList = open(listFile, 'r') # opens the list file
    codes = textList.read().split('\n')
    textList.close
    # print("This list has " + str(len(codes)))
    return codes

def dupCheck(codeList):
    for code in codeList:
        if codeList.count(code) > 1:
            #print("Multiples occurrances of " + code)
            first = codeList.index(code) + 1
            for i in range(codeList.count(code) - 1):
                next = codeList.index(code, first)
                del codeList[next]
    # print("Now it has " + str(len(codeList)))

def writeOut(codeList, listFile):
    codeText = '\n'.join(codeList)
    # print(codeText)
    # write out the puzzle file list
    fileOut = open(listFile, 'w')
    fileOut.write(codeText)
    fileOut.close()

def reconcile(list1, list2):
    # removes codes that are in both lists and puts them in the duplicate file
    delList = []
    for code in list1:
        try:
            dupe = list2.index(code)
            with open(duplicateListFile, 'a') as dupeFile:
                dupeFile.write(code + '\n')
            delList.append(code)
            list2.remove(code)
            # del list1[list1.index(code)]
            # del list2[dupe]
        except:
            pass
        finally:
            for code in delList:
                list1.remove(code)

def compare(list1, list2):
    # removes codes from list 1 that are in list 2
    for code in list2:
        try:
            dupe = list1.index(code)
            list1.remove(code)
            # list2.remove(code)
            # del list1[list1.index(code)]
            # del list2[dupe]
        except:
            pass
        finally:
            pass

# actual code starts here
privateCodes = loadList(puzzleListFile)
publicCodes = loadList(publishListFile)
newCodes = loadList(newPuzzFile)
newPubCodes = loadList(newPubFile)       

# check for codes that are in a list more than once
dupCheck(privateCodes)
dupCheck(publicCodes)
dupCheck(newCodes)
dupCheck(newPubCodes)

# check for codes in new list that are in regular lists too
compare(newCodes, privateCodes)
compare(newPubCodes, publicCodes)
compare(newCodes, publicCodes)
compare(newPubCodes, privateCodes)

# check for codes that are in the pub lis and in the non-pub list
reconcile(privateCodes, publicCodes)



# save the new lists
writeOut(privateCodes, puzzleListFile)
writeOut(publicCodes, publishListFile)
writeOut(newCodes, newPuzzFile)
writeOut(newPubCodes, newPubFile)


