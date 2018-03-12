#!/usr/bin/env python3

import requests, lxml.html, sys, logging, logging.handlers, smtplib, configparser
import time

# TODO make puzzle and puzzlepub files into lists
# TODO add scrape of my puzzles to bookmark and build puzzle list

# set up the logger
log = logging.getLogger('jigidize')
hdlr = logging.handlers.RotatingFileHandler('/home/pi/Documents/logs/jigidize.log',\
                                            'a',500000,7)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)
log.info("__________Blank Space_________")
log.info("##### Starting to Jigidize #####")

puzzleListFile = "/home/pi/Documents/logs/puzzles" # private
publishListFile = "/home/pi/Documents/logs/puzzlesPublic" # prod pi
newPuzzFile = "/home/pi/Documents/logs/newpuzzles" # private
newPubFile = "/home/pi/Documents/logs/newpuzzlespub" # public

# URLs
baseUrl = "https://www.jigidi.com"
logInUrl = baseUrl + "/login.php"
puzzleUrl = baseUrl + "/jigsaw-puzzle/"
createdUrl = baseUrl + "/created.php?id="
myPuzzlesUrl = baseUrl + "/created_puzzles.php"
setBookmarkUrl = baseUrl + "/ajax/set_bookmark.php"
setFollowUrl = baseUrl + "/ajax/notify.php"
addCommentUrl = baseUrl + "/ajax/comment_add.php"
publishUrl = baseUrl + "/ajax/change_puzzle.php"
notifsUrl = baseUrl + '/notifications.php'

# some global variables
true = 1
false = 0
fail = 0
addCodes = []
followCodes = []
myCodes = []
loadTimes = []
totalAdds = totalFollows = totalComments = 0
fileEmpty = 0
loadFailCount = 0
loadErrCount = 0
mailComment = ""

# check to see if arguments were passed in with the command
inputValues = sys.argv
userUrl = None
publishCount = newPuzzleCount = newPubPuzzCount = setSize = notif = \
    scrapeMyPuzzles = recoverMyPuzzles = privatize = 0

if len(inputValues) > 1: # extra arguements were entered
    log.info("passed in values:")
    log.info(inputValues)
    if inputValues[1] == '-u': # next argument should be a username
        if len(inputValues) > 2:
            userUrl = 'https://www.jigidi.com/user/' + inputValues[2]
        else:
            log.info("User selected, but no username provided")
    elif inputValues[1] == '-p': # publish some puzzles
        if len(inputValues) > 2:
            publishCount = int(inputValues[2])
        else:
            publishCount = 2
        notif = True
        log.info("Publishing " + str(publishCount) + " puzzles")
    elif inputValues[1] == '-x': # xnee just finished making more puzzles
        if len(inputValues) > 2:
            newPuzzleCount = int(inputValues[2])
            if len(inputValues) > 3:
                if inputValues[3] == 'priv':
                    privatize = True
        else:
            newPuzzleCount = 1
        log.info("Adding New Puzzles: " + str(newPuzzleCount))
    elif inputValues[1] == '-xp': # xnee just finished making public puzzles
        if len(inputValues) > 2:
            newPubPuzzCount = int(inputValues[2])
        else:
            newPubPuzzCount = 1
        log.info("Adding New Public Puzzles: " + str(newPubPuzzCount))
    elif inputValues[1] == '-d': # deep dive in notifications
        notifsUrl += '?all'
        notif = True
        log.info("Deep dive on Notifs")
    elif inputValues[1] == '-m': # scrape my puzzles
        scrapeMyPuzzles = True
        log.info("Scraping my puzzles")
    elif inputValues[1] == '-r': # recover my puzzles
        recoverMyPuzzles = True
        log.info("Recovering my puzzles")
    elif inputValues[1] == '-s': # build publish puzzle sets
        if len(inputValues) > 2:
            setSize = int(inputValues[2])
        else:
            setSize = 3
        log.info("Building Public Puzzle sets with setSize: " + str(setSize))
    else:
        print("invalid argument")
        raise SystemExit
else: notif = True
    

# read in the configuration file
# try to open the file, if it's not there, create one
# add -c switch to allow editing of the file
config = configparser.SafeConfigParser()
config.read('/var/lib/jigidize/config.cfg')
try:
    testing = int(config.get('settings','testing'))
    username = config.get('credentials','username')
    password = config.get('credentials','password')
    sender = config.get('credentials','sender')
    smtpPassword = config.get('credentials','smtpPassword')
    reciever = config.get('settings','reciever')
    smtpServer = config.get('settings','smtpServer')
except:
    log.info("Configuration file error - recreating the file")
    print("There was a proplem with the configuration file, it needs to be recreated")
    config = configparser.SafeConfigParser()
    config.add_section("credentials")
    username = input("Jigidi Username?")
    config.set('credentials','username',username)
    password = input("Jigidi Password?")
    config.set('credentials','password',password)
    sender = input("Sender E-Mail Address?")
    config.set('credentials','sender',sender)
    smtpPassword = input("SMTP Password?")
    config.set('credentials','smtpPassword',smtpPassword)
    config.add_section('settings')
    config.set('settings','testing','1')
    testing = 1
    config.set('settings','senderEmail',sender)
    reciever = input("Email address of Reciever?")
    config.set('settings','reciever',reciever)
    smtpServer = input("SMTP Server address?")
    config.set('settings','smtpServer',smtpServer)
    config.set('settings','mailHeader',"From: Raspberry Pi <%(senderEmail)s>\nto: %(username)s <%(reciever)s>\nSubject: Report\n")
    with open('/var/lib/jigidize/config.cfg','w') as configFile:
        config.write(configFile)
finally:
    pass


def loadPage(pageUrl):
    global loadTimes, loadFailCount, loadErrCount
    try:
        log.debug('loading ' + pageUrl)
        startTime = time.time()
        page = s.get(pageUrl)
        if page.status_code == requests.codes.ok: # page loaded successfully
            # need to add a way to handle 'that puzzle couldn't be found'
            loadTime = time.time() - startTime
            loadTimes.append(loadTime)
            log.debug('success: load time = ' + str(loadTime))
            return page
        else:
            log.warning("Failed to load " + pageUrl)
            loadFailCount += 1
            return page
    except:
        log.exception("Exception loading " + pageUrl)
        loadErrCount += 1
        return false
    finally:
        pass

def loadList(listFile):
    log.debug("loading list file " + listFile)
    textList = open(listFile, 'r') # opens the list file
    codes = textList.read().split('\n')
    textList.close
    log.debug("This list has " + str(len(codes)) + " codes")
    return codes

def creatorCheck(puzzlePage):
    # check to see if it was created by me - returns true or false
    log.debug("Starting creatorCheck on " + puzzlePage.url)
    html = lxml.html.fromstring(puzzlePage.text)
    creatorSet = html.xpath(r'//a[@itemprop="creator"]/child::text()')
    if len(creatorSet) == 1:
        if creatorSet[0] == username:
            # this puzzle is mine
            log.debug("created by me")
            return true
        else:
            log.debug("created by someone else " + creatorSet[0])
            return false        
    elif len(creatorSet) > 1:
        # multiple creator links, so I don't know what to do
        log.warning("multiple creators")
        log.warning(creatorSet)
        return false
    else:
        log.warning("No Creator found on page " + puzzlePage.url)
        return false

def lastCommentCheck(puzzlePage):
    # check to see if the last comment was created by me
    # if it wasn't, returns the total number of comments on the page
    log.debug("Starting lastCommentCheck on " + puzzlePage.url)
    html = lxml.html.fromstring(puzzlePage.text)
    commentors = html.xpath(r'//a[@class="post_author"]/span[@itemprop="creator"]/child::text()')
    log.debug("commentors:"+str(len(commentors)))
    if len(commentors) > 1:
        # the first commentor is actually the puzzle creator
        if commentors[1] == username:
            #last comment was by me
            log.debug("last comment was made by me")
            return true
        else:
            log.debug("Last comment was made by someone else")
            return false
    else:
        log.debug("No comments on this puzzle")
        return true # it's my puzzle and no one has commented

def followCheck(puzzlePage):
    # check to see if it's followed - returns true or false
    log.debug("Starting followCheck on " + puzzlePage.url)
    html = lxml.html.fromstring(puzzlePage.text)
    if len(html.xpath(r'//span[@class="js_follow js_link on"]')) > 0:
        # follow link is on, so puzzle is followed
        log.debug("Follow is on")
        return true
    elif len(html.xpath(r'//span[@class="js_follow js_link off"]')) > 0:
        # follow link is off, so puzzle is not followed
        log.debug("Follow is off")
        return false
    else:
        log.warning("No Follow Link found on page " + puzzlePage.url)

def bookmarkCheck(puzzlePage):
    # check to see if it's bookmarked - returns true or false
    log.debug("Starting bookmarkCheck on " + puzzlePage.url)
    html = lxml.html.fromstring(puzzlePage.text)
    if len(html.xpath(r'//span[@class="js_bookmark js_link on"]')) > 0:
        # bookmark link is on, so puzzle is bookmarked
        log.debug("Bookmark is on")
        return true
    elif len(html.xpath(r'//span[@class="js_bookmark js_link off"]')) > 0: 
        # bookmark link is off, so puzzle is not bookmarked
        log.debug("Bookmark is off")
        return false
    else:
        log.warning("No Bookmark Link found on page " + puzzlePage.url)

def solvedCheck(puzzlePage):
    # check ro see if i have solved this one before
    log.debug("Starting solvedCheck on " + puzzlePage.url)
    html = lxml.html.fromstring(puzzlePage.text)
    if len(html.xpath(r'//div[@id="user_progress"]')) > 0:
        # I have solved this one
        log.debug("Already solved")
        return true
    else: 
        # I have not solved this one
        log.debug("Not solved")
        return false

def solveCount(puzzlePage):
    # returns count of solves
    log.debug("Starting solveCount on " + puzzlePage.url)
    solveCount = 0
    html = lxml.html.fromstring(puzzlePage.text)
    puzzleStats = html.xpath(r'//div[@class="stat"]/strong/child::text()')
    log.debug(puzzleStats)
    # Stats are pieces, comments, solves, so we want the 3rd stat
    solveCount = int(puzzleStats[2])
    log.debug("solveCount=" + str(solveCount))
    # get the number from div-stat, but there are 3 and we need the third one... 
    # not sure how to get it
    return solveCount

def keywordCheck(puzzlePage):
    # returns keyword if this puzzle has one
    log.debug("Starting keywordCheck on " + puzzlePage.url)
    html = lxml.html.fromstring(puzzlePage.text)
    keywordSet = html.xpath(r'//input[@name="keywords"]')
    keywords = [i.attrib['value'] for i in keywordSet]
    log.debug("Keywords: " + str(len(keywords)))
    if len(keywords) > 0:
        log.debug("Keyword 1: " + keywords[0])
        return keywords[0]
    else:
        return False
  
def pubCheck(puzzlePage):
    # returns true if this puzzle looks like I tried to publish it
    log.debug("Starting pubCheck on " + puzzlePage.url)
    html = lxml.html.fromstring(puzzlePage.text)
    descText = html.xpath(r'//div[@id="description_section"]/child::text()')
    log.debug("Desc lines: " + str(len(descText)))
    if len(descText) >1:
        return True
    elif len(descText) == 1 and len(descText[0].strip()) > 0:
        log.debug("Desc line 1: " + str(len(descText[0].strip())))
        return True
    else:
        return False
    puzzleStats = html.xpath(r'//div[@class="stat"]/strong/child::text()')
    log.debug(puzzleStats)

def justBookmark(puzzlePage, puzzleId):
    log.debug("Starting justBookmark on " + puzzlePage.url)
    global totalAdds
    if bookmarkCheck(puzzlePage):
        log.debug("Already Bookmarked")
        return true
    else:
        headers = {'Referer':puzzlePage.url}
        form = {"id":puzzleId,"set":1,"state":1}
        response = s.post(setBookmarkUrl, data = form, headers = headers)
        if response.status_code == requests.codes.ok:
            totalAdds += 1
            log.info("Puzzle " + puzzleId + " Bookmarked")
            return true
        else:
            log.warning("Return status code not ok on " + puzzlePage.url)
            return false
        
def justFollow(puzzlePage, puzzleId):
    global totalFollows
    if followCheck(puzzlePage):
        return true
    else:
        headers = {'Referer':puzzlePage.url}
        form = {'type':'p','sender':puzzleId,'state':1}
        response = s.post(setFollowUrl, data = form, headers = headers)
        if response.status_code == requests.codes.ok:
            totalFollows += 1
            return true
        else:
            return false

def getGKey(html):
    javaScriptSet = html.xpath(r'//script[@type="text/javascript"]/child::text()')
    for script in javaScriptSet:
        start = script.find("g_key")
        if start > 0:
            g_key = script[start+9:start+15]
            log.debug("g_key is " + g_key)
            return g_key

def addComment(puzzlePage, puzzleId):
    global fileEmpty, totalComments
    html = lxml.html.fromstring(puzzlePage.text)
    log.debug("getting the Java g_key and g_count values")
    g_key = getGKey(html)
    log.debug("Figuring out g_count")
    commentors = html.xpath(r'//a//span[@itemprop="creator"]/child::text()')
    g_count = len(commentors) # don't need to add one since puzzle creator is in this list
    log.debug("g_count is " + str(g_count))
    g_request_key = g_key + '|' + str(g_count)
    puzzle = puzzleFile.readline().split('\n')
    code = puzzle[0][-8:]
    if code:
        commentText = puzzleUrl + code
        headers = {'Referer':puzzlePage.url}
        form = {'id':puzzleId,'type':'puzzle','message':commentText,'request_key':g_request_key}
        response = s.post(addCommentUrl, data = form, headers = headers)
        if response.status_code == requests.codes.ok:
            log.info("posted comment on " + puzzleId)
            addCodes.append(code)
            totalComments += 1
            return true
        else:
            log.warning("tried and failed to post comment on " + puzzleId)
            return false
    else:
        fileEmpty = 1
        log.info("can't post comments, the file is empty")

def addPuzzle(puzzle, puzzCode):
    # this bookmarks and follows a puzzle if it's not already followed
    if puzzle.status_code == requests.codes.ok:
        if followCheck(puzzle):
            log.debug("Puzzle " + puzzCode + " already followed")
            return false
        else:
            if justBookmark(puzzle, puzzCode) and justFollow(puzzle, puzzCode):
                log.debug("Puzzle " + puzzCode + " added")
            else:
                log.info("Puzzle " + puzzCode + " add failed")
            return true
    else:
        log.warning("Puzzle " + puzzCode + " did not load")
        return false
    
def followPuzzle(puzzle, puzzCode):
    # this just follows a puzzle
    # if it's mine, we are going to add a comment
    if creatorCheck(puzzle):
        log.debug("this one is mine " + puzzle.url)
        if not(lastCommentCheck(puzzle)):
            log.debug("and the last comment isn't mine")
            addComment(puzzle, puzzCode)
    if puzzle.status_code == requests.codes.ok:
        if justFollow(puzzle, puzzCode):
            log.debug("Puzzle " + puzzCode + " followed")
        else:
            log.info("Puzzle " + puzzCode + " follow failed")
        return true
    else:
        log.warning("Puzzle " + puzzCode + " did not load")
        return false

def makePrivate(puzzCode):
    # tag a puzzle as private so it doesn't get recovered
    log.debug("privating puzzle " + puzzCode)
    puzzlePage = loadPage(createdUrl + puzzCode)
    if puzzlePage:
        html = lxml.html.fromstring(puzzlePage.text)
        g_key = getGKey(html)
        key = g_key + "#info form_1"
        titleSet = html.xpath(r'//input[@name="title"]')
        title = titleSet[0].attrib['value']
        descSet = html.xpath(r'//div[@id="description_section"]/child::text()')
        description = ''
        lines = 0
        for line in descSet:
            description += line + '\n'
            lines += 1
        keywords = 'private'
        form = {'title':title, 'description':description, 'credit_name':"",\
                'credit_link':"", 'info_message':"", 'appropriate':'on', 'category':\
                0, 'copyright':0, 'keywords':keywords, 'key':key, 'pid':puzzCode}
        headers = {'Referer':puzzlePage.url}
        response = s.post(publishUrl, data = form, headers = headers)
        if response.status_code == requests.codes.ok:
            log.info("privated puzzle " + puzzCode)
            addCodes.append(puzzCode)
            return true
        else:
            log.warning("tried and failed to private puzzle " + puzzleId)
            return false

def addMine(puzzle, puzzCode):
    # this bookmarks a puzzle I created if I haven’t already solved it
    if puzzle.status_code == requests.codes.ok:
        if privatize:
            makePrivate(puzzCode)
        if solvedCheck(puzzle):
            log.debug("Puzzle " + puzzCode + " already solved")
            return false
        else:
            if justBookmark(puzzle, puzzCode):
                log.debug("Puzzle " + puzzCode + " bookmark success")
            else:
                log.info("Puzzle " + puzzCode + " bookmark failed")
            return true
    else:
        log.warning("Puzzle " + puzzCode + " did not load")
        return false

def recoverMine(puzzle, puzzCode):
    # this finds puzzles I created that haven't been solved and adds them 
    # to newpuzzles or newpuzzlespub depending of whether it has a description
    if puzzle.status_code == requests.codes.ok:
        # need to make a decision here if it's a pub or not
        # if pub, change listFile to newPubFile
        listFile = newPuzzFile
        private = 0
        if pubCheck(puzzle):
            log.debug("looks like a pub")
            listFile = newPubFile
        else:
            log.debug("doesn't look like a pub")
        if keywordCheck(puzzle) == "private":
            private = 1
            log.debug("private puzzle, don't add to the list")
        if solvedCheck(puzzle):
            log.debug("Puzzle " + puzzCode + " already solved")
            log.debug("checking solve count")
            if solveCount(puzzle) <= 1 and not private:
                log.debug("add to the list")
                # append code to the file selected above
                with open(listFile, 'a') as puzzleFile:
                        puzzleFile.write(code + '\n')
            else:
                log.debug("more than 1 solve, don't add to list")
            return false
        else:
            log.debug("checking solve count")
            if solveCount(puzzle) == 0 and not private:
                log.debug("add to the list")
                # append code to the file selected above
                with open(listFile, 'a') as puzzleFile:
                        puzzleFile.write(code + '\n')
            else:
                log.debug("more than 0 solves, don't add to list")
            return true
    else:
        log.warning("Puzzle " + puzzCode + " did not load")
        return false

def scrapeNotifs():
    # get codes from notifs page
    log.info("scraping notifications")
    notifsPage = loadPage(notifsUrl)
    if notifsPage:
        notifs_html = lxml.html.fromstring(notifsPage.text)
        puzzleLinks = notifs_html.xpath(r'//div[@data-id]') 
        puzzleCodes = [i.attrib['data-id'] for i in puzzleLinks]
        comments = notifs_html.xpath(r'//div[@class="box"]/a[@href]/img[@src]')
        commentLinks = [i.attrib['src'] for i in comments]
        for comment in commentLinks:
            parts = comment.split('/')
            for part in parts:
                if len(part.strip()) == 8 and not(part.islower()):
                    puzzleCodes.append(part)
        followCodes.extend(puzzleCodes)
        log.info("Added " + str(len(puzzleCodes)) + " followCodes")

def scrapeUser(userUrl):
    # get codes from a user's pages to follow
    log.info("scraping " + userUrl)
    page = loadPage(userUrl)
    if page:
        pageNum = 1
        codeCount = 1
        addCount = 0
        while codeCount > 0:
            if page.status_code == requests.codes.ok:
                page_html = lxml.html.fromstring(page.text)
                puzzleLinks = page_html.xpath(r'//div[@data-id]') 
                puzzleCodes = [i.attrib['data-id'] for i in puzzleLinks]
                codeCount = len(puzzleCodes)
                followCodes.extend(puzzleCodes)
                pageNum += 1
                page = loadPage(userUrl + '/' + str(pageNum))
            else: codeCount = 0
            addCount += codeCount
        log.info("Added " + str(addCount) + " followCodes")

def scrapeMine():
    # get codes from my pages
    log.info("starting to scrape my puzzles")
    page = loadPage(myPuzzlesUrl)
    if page:
        pageNum = 1
        codeCount = 1
        addCount = 0
        indexCode = "test"
        while codeCount > 0:
            if page.status_code == requests.codes.ok:
                page_html = lxml.html.fromstring(page.text)
                puzzleLinks = page_html.xpath(r'//div[@data-id]') 
                puzzleCodes = [i.attrib['data-id'] for i in puzzleLinks]
                if indexCode == puzzleCodes[0]:
                    codeCount = 0
                    log.debug("repeat")
                else:
                    indexCode = puzzleCodes[0]
                    codeCount = len(puzzleCodes)
                    myCodes.extend(puzzleCodes)
                pageNum += 1
                page = loadPage(myPuzzlesUrl + '?p=' + str(pageNum))
                log.debug("scraping page " + str(pageNum))
                log.debug("URL page " + str(page.url))
            else: codeCount = 0
            addCount += codeCount
        log.info("found " + str(addCount) + " puzzle Codes")
 
def scrapePuzzle(puzzle, puzzCode):
    # get codes from the description and comments of a puzzle page
    log.debug("Scraping " + puzzCode)
    ######only here for testing#####
    if testing:
        # if it's mine, we are going to add a comment
        if creatorCheck(puzzle):
            log.debug("this puzzle is mine " + puzzle.url)
            if not(lastCommentCheck(puzzle)):
                log.debug("and the last comment wasn't made by me")
                addComment(puzzle, puzzCode)
    #####end test section#####
    puzzle_html = lxml.html.fromstring(puzzle.text)
    descText = puzzle_html.xpath(r'//div[@id="description_section"]/child::text()')
    commText = puzzle_html.xpath(r'//p[@class="post_message"]/child::text()')
    commText.extend(descText)
    for comm in commText:
        linkStart = comm.find('php?id=')
        if linkStart > 0:
            a = linkStart + 7
            z = a + 8
            try:
                addCodes.index(comm[a:z])
            except:
                addCodes.append(comm[a:z])
                log.debug("new code found " + comm[a:z])
            finally:
                pass
        parts = comm.split() # split by space to find orphan codes
        parts.extend(comm.split('/')) # split by slash
        parts.extend(comm.split('=')) # split by equals
        for part in parts:
            part = part.strip()
            if len(part) == 8 and part.isupper() and part.isalnum():
                try:
                   addCodes.index(part)
                except:
                    addCodes.append(part)
                    log.debug("new code found " + part)
                finally:
                    pass
    
def publishPuzzle(puzzCode):
    # publish a puzzle so anyone can solve it
    global fileEmpty
    log.debug("publishing puzzle " + puzzCode)
    puzzlePage = loadPage(createdUrl + puzzCode)
    if puzzlePage:
        log.debug("opened page " + puzzlePage.url)
        html = lxml.html.fromstring(puzzlePage.text)
        g_key = getGKey(html)
        key = g_key + "#info form_1"
        titleSet = html.xpath(r'//input[@name="title"]')
        title = titleSet[0].attrib['value']
        descSet = html.xpath(r'//div[@id="description_section"]/child::text()')
        description = ''
        lines = 0
        for line in descSet:
            description += line + '\n'
            lines += 1
        if not fileEmpty:
            adds = max(3-lines, 0)
            log.debug("description already has " + str(lines) + " lines")
            log.debug("adding " + str(adds) + " lines")
            for i in range(adds):
                puzzle = puzzleFile.readline().split('\n')
                code = puzzle[0][-8:]
                if code:
                    description += puzzleUrl + code + '\n'
                else:
                    fileEmpty = 1
        keywords = 'adult'
        form = {'title':title, 'description':description, 'credit_name':"",\
                'credit_link':"", 'info_message':"", 'publish':'on', 'category':\
                3, 'copyright':2, 'keywords':keywords, 'key':key, 'pid':puzzCode}
        headers = {'Referer':puzzlePage.url}
        response = s.post(publishUrl, data = form, headers = headers)
        if response.status_code == requests.codes.ok:
            log.info("published puzzle " + puzzCode)
            addCodes.append(puzzCode)
            return true
        else:
            log.warning("tried and failed to publish puzzle " + puzzleId)
            return false

def publishLoop(counter):
    # Loop to publish puzzles from the file
    global fileEmpty
    publishList = open(publishListFile, 'r')
    log.debug("publishing puzzles")
    for i in range(publishCount):
        if not fileEmpty:
            puzzle = publishList.readline().split('\n')
            code = puzzle[0][-8:]
            if code:
                publishPuzzle(code)
            else:
                fileEmpty = 1
    writeList(publishList, publishListFile)
    # mailComment += "\nPublished " + str(counter)

def createSets(bonusCount):
    # Loop through the new pub puzzles file and add bounus puzzles to each
    pubCodes = loadList(newPubFile)
    log.debug("loaded pubCodes: " + str(len(pubCodes)))
    log.debug(pubCodes)
    bonusCodes = loadList(newPuzzFile)
    log.debug("creating sets")
    for pubCode in pubCodes:
        if pubCode:
            log.debug("building set on puzzle " + pubCode)
            puzzlePage = loadPage(createdUrl + pubCode)
            if puzzlePage:
                log.debug("opened page " + puzzlePage.url)
                html = lxml.html.fromstring(puzzlePage.text)
                g_key = getGKey(html)
                key = g_key + "#info form_1"
                titleSet = html.xpath(r'//input[@name="title"]')
                title = titleSet[0].attrib['value']
                descSet = html.xpath(r'//div[@id="description_section"]/child::text()')
                description = ''
                for line in descSet:
                    description += line + '\n'
                for i in range(bonusCount):
                    bonusCode = bonusCodes.pop(0)
                    description += puzzleUrl + bonusCode + '\n'
                keywords = 'adult'
                form = {'title':title, 'description':description, 'credit_name':"",\
                        'credit_link':"", 'info_message':"", 'publish':'off', 'category':\
                        3, 'copyright':2, 'keywords':keywords, 'key':key, 'pid':pubCode}
                headers = {'Referer':puzzlePage.url}
                response = s.post(publishUrl, data = form, headers = headers)
                if response.status_code == requests.codes.ok:
                    log.info("bult set on puzzle " + pubCode)
                else:
                    log.warning("tried and failed to build set on puzzle " + puzzleId)
    # writeList(publishList, newPubFile)
    writeOut(bonusCodes, newPuzzFile)
    # need to write out a file with nothing in it

def scrapeNewPuzzles(counter, listFile):
    # get codes from newly created puzzles
    # add try open file with puzzle name in cneed folder, if its there, add code,
    # delete the file and continue, if its not there, then stop adding
    log.info("scraping " + str(counter) + " new puzzles")
    page = loadPage(myPuzzlesUrl)
    if page:
        pageNum = 1
        codeCount = 1
        addCount = 0
        while codeCount > 0 and addCount < counter:
            if page.status_code == requests.codes.ok:
                # need to loop through codes and add until we reach counter
                page_html = lxml.html.fromstring(page.text)
                puzzleLinks = page_html.xpath(r'//div[@data-id]') 
                puzzleCodes = [i.attrib['data-id'] for i in puzzleLinks]
                codeCount = len(puzzleCodes)
                log.debug("Puzzles on page " + str(pageNum) + " of my puzzles = " + str(codeCount))
                log.debug(puzzleCodes)
                while addCount < counter and addCount < 24:
                    code = puzzleCodes[addCount]
                    log.debug("Add Codes number " + str(addCount) + " is " + puzzleCodes[addCount])
                    # append code to the file
                    with open(listFile, 'a') as puzzleFile:
                        puzzleFile.write(code + '\n')
                    # add the code to myCodes to bookmark
                    myCodes.append(code)
                    addCount += 1
                log.info("Added " + str(addCount) + " new puzzles")
                pageNum += 1
                addCount = 0
                counter -= 24
                page = loadPage(myPuzzlesUrl + '?p=' + str(pageNum))
            else: 
                codeCount = 0
                log.warning("My Puzzles page failed to load")
        #puzzleFile.close
        log.info("Added " + str(addCount) + " new puzzles")

def writeList(listVar, listFileName):
    # write out the puzzle file list
    puzzlesLeft = listVar.read()
    listVar.close()
    writeOut = open(listFileName, 'w')
    writeOut.write(puzzlesLeft)
    writeOut.close()

def writeOut(codeList, listFile):
    codeText = '\n'.join(codeList)
    # print(codeText)
    # write out the puzzle file list
    fileOut = open(listFile, 'w')
    fileOut.write(codeText)
    fileOut.close()

def sendEmail():
    # send completion notification
    log.debug("starting to send email")
    global totalAdds, totalFollows, totalComments, fileEmpty, sender, \
            smtpPassword, smtpServer, mailComment
    mailHeader = "From: Raspberry Pi <" + sender + ">\nto: " + username + \
    " <" + reciever + ">\nSubject: Report\n"
    recievers = [reciever]
    mailBody = str(totalAdds) + " A - " + str(totalFollows) + ' F - ' + \
                str(totalComments) + " C"
    if len(loadTimes) > 0:
        statistics = "\n" + str(loadFailCount) + " LF - " + \
                    str(loadErrCount) + " LE - " + str(len(loadTimes)) \
                    + "TPL"
        statistics += "\nALT = " + str(sum(loadTimes)/len(loadTimes))
    else:
        statistics = ""
    if fileEmpty: # the file of puzzles for comments is empty
        fileWarning = " and the file is empty"
    else:
        fileWarning = ""
    msg = mailHeader + mailBody + fileWarning + statistics
    log.debug("Mail message: " + msg)
    mailServer = smtplib.SMTP('smtp.comcast.net', 587)
    mailServer.login(sender, smtpPassword)
    mailServer.starttls()
    try:
        mailServer.sendmail(sender, recievers, msg)
        log.info('Mail sent')
    except:
        log.warning('Mail not sent')

#############################
## actual code starts here ##
try:
    s = requests.Session()# open a session and login
    start = s.get(baseUrl) # starts the secure session - gets cookies
    login = s.get(logInUrl) # initiates login
    form = {'login':'true','username':username,'password':password}
    response = s.post(logInUrl, data=form) # send login data
    if response.status_code == requests.codes.ok:
        log.debug("login successful")
    else:
        log.warning("login failure")
except:
    log.warning("Failed to load login pages")
    raise SystemExit
finally:
    pass

commentCodes = loadList(puzzleListFile)
puzzleFile = open(puzzleListFile, 'r') # open the puzzle list file

# start scraping puzzles
if newPuzzleCount: # passed in -x and a number
    scrapeNewPuzzles(newPuzzleCount, newPuzzFile)
if userUrl: # passed in a user to scrape
    scrapeUser(userUrl)
if publishCount: # passed in -p and a number
    publishLoop(publishCount)
    notifsUrl += '?all' # checks all notifs
if newPubPuzzCount: # passed in -xp and a number
    scrapeNewPuzzles(newPubPuzzCount, newPubFile)
if setSize: # passed in -s and a number
    createSets(setSize)
if scrapeMyPuzzles or recoverMyPuzzles: # passed in -m or -r
    scrapeMine()
if testing: # in config file
    log.info("Testing")
    #puzzle = loadPage(puzzleUrl + '26ZCX2BQ')
    myCodes.append('26ZCX2BQ') #pumpkin in her jacket
    myCodes.append('MUM8225R') #pretty in pink
    #if puzzle:
        #addMine(puzzle, '26ZCX2BQ') #pumpkin in her jacket
        #publishPuzzle('26ZCX2BQ') #pumpkin in her jacket
    #scrapePuzzle('US8EUSFG') #Hubble
    #scrapeUser('https://www.jigidi.com/user/Spiritual')
    #scrapeMine()
if not testing and notif:
    scrapeNotifs()

log.info("Follow codes at start of followCode loop " + str(len(followCodes)))
log.debug(followCodes)
for code in followCodes:
    puzzle = loadPage(puzzleUrl + code)
    if puzzle:
        if followPuzzle(puzzle, code):
            scrapePuzzle(puzzle, code)
            
log.info("Add codes at start of addCode loop: " + str(len(addCodes)))
log.debug(addCodes)
for code in addCodes:
    puzzle = loadPage(puzzleUrl + code)
    if puzzle:
        if addPuzzle(puzzle, code): # returns false if it was already followed
            scrapePuzzle(puzzle, code)

log.info("My codes at start of myCode loop: " + str(len(myCodes)))
log.debug(myCodes)
for code in myCodes:
    if recoverMyPuzzles:
        puzzle = loadPage(createdUrl + code)
    else:
        puzzle = loadPage(puzzleUrl + code)
    if puzzle:
        if recoverMyPuzzles:
            recoverMine(puzzle, code)
        else:
            addMine(puzzle, code)

log.info("Total Adds:" + str(totalAdds))
log.info("Total Follows:" + str(totalFollows))
log.info("Total Comments:" + str(totalComments))
log.info("Total Page Loads:" + str(len(loadTimes)))
log.info("Average Load Time:" + str(sum(loadTimes)/len(loadTimes)))
log.info("Load faliures:" + str(loadFailCount))
log.info("Load Exceptions:" + str(loadErrCount))

writeList(puzzleFile, puzzleListFile)
sendEmail()

# all done
