#!/usr/bin/env python3

import requests, lxml.html, sys, logging, logging.handlers, smtplib

# set up the logger
log = logging.getLogger('jigidize')
hdlr = logging.handlers.RotatingFileHandler('/home/pi/Documents/logs/jigidize.log',\
                                            'a',20000,7)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)
log.info("__________Blank Space_________")
log.info("##### Starting to Jigidize #####")

testing = 1

if testing:
    log.info("Testing")

# check to see if a userUrl was passed in with the command
try:
    inputValue = sys.argv[1]
    if inputValue[:5] == 'https': # if so it's a whole url
        userUrl = inputValue 
    else: # if not, assume it's just the name
        userUrl = 'https://www.jigidi.com/user/' + inputValue
    log.info("passed in value " + inputValue)
except:
    userUrl = None
    log.info("no input provided")
finally:
    pass

baseUrl = "https://www.jigidi.com"
logInUrl = "https://www.jigidi.com/login.php"
puzzleUrl = "https://www.jigidi.com/jigsaw-puzzle/"
setBookmarkUrl = "https://www.jigidi.com/ajax/set_bookmark.php"
setFollowUrl = "https://www.jigidi.com/ajax/notify.php"
addCommentUrl = "https://www.jigidi.com/ajax/comment_add.php"
puzzleListFile = "/home/pi/Documents/python/jigidi.txt"
username = 'Minimart64'
password = 'worthing'

# some global variables
true = 1
false = 0
fail = 0
addCodes = []
followCodes = []
totalAdds = 0
totalFollows = 0
totalComments = 0
fileEmpty = 0

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
        return false

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
            log.debug("Bookmarked")
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

def addComment(puzzlePage, puzzleId):
    global fileEmpty, totalComments
    log.debug("getting the Java g_key and g_count values")
    html = lxml.html.fromstring(puzzlePage.text)
    javaScriptSet = html.xpath(r'//script[@type="text/javascript"]/child::text()')
    for script in javaScriptSet:
        start = script.find("g_key")
        if start > 0:
            g_key = script[start+9:start+15]
            log.debug("g_key is " + g_key)
            print("g_key is " + g_key)
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
            log.debug("posted comment on " + puzzleId)
            addCodes.append(code)
            totalComments += 1
            return true
        else:
            log.warning("tried and failed to post comment on " + puzzleId)
            return false
    else:
        fileEmpty = 1
        log.info("can't post comments, the file is empty")

def addPuzzle(puzzCode):
    # this bookmarks and follows a puzzle if it's not already followed
    puzzle = s.get(puzzleUrl + puzzCode)
    if puzzle.status_code == requests.codes.ok:
        if followCheck(puzzle):
            log.info("Puzzle " + puzzCode + " already followed")
        else:
            if justBookmark(puzzle, puzzCode) and justFollow(puzzle, puzzCode):
                log.info("Puzzle " + puzzCode + " added")
            else:
                log.info("Puzzle " + puzzCode + " not added")
        return true
    else:
        log.warning("Puzzle " + puzzCode + " did not load")
        return false
    
def followPuzzle(puzzCode):
    # this just follows a puzzle
    puzzle = s.get(puzzleUrl + puzzCode)
    # if it's mine, we are going to add a comment
    if creatorCheck(puzzle):
        log.debug("this one is mine " + puzzle.url)
        if not(lastCommentCheck(puzzle)):
            log.debug("and teh last comment isn't mine")
            addComment(puzzle, puzzCode)
    if puzzle.status_code == requests.codes.ok:
        if justFollow(puzzle, puzzCode):
            log.info("Puzzle " + puzzCode + " followed")
        else:
            log.info("Puzzle " + puzzCode + " not followed")
        return true
    else:
        log.warning("Puzzle " + puzzCode + " did not load")
        return false

def scrapeNotifs():
    # get codes from notifs page
    log.info("scraping notifications")
    notifs = s.get(baseUrl + '/notifications.php')
    notifs_html = lxml.html.fromstring(notifs.text)
    puzzleLinks = notifs_html.xpath(r'//div[@data-id]') 
    puzzleCodes = [i.attrib['data-id'] for i in puzzleLinks]
    comments = notifs_html.xpath(r'//div[@class="box"]/a[@href]/img[@src]')
    commentLinks = [i.attrib['src'] for i in comments]
    for comment in commentLinks:
        parts = comment.split('/')
        for part in parts:
            if len(part.strip()) == 8 and not(part.islower()):
                followCodes.append(part)
    followCodes.extend(puzzleCodes)

def scrapeUser(userUrl):
    # get codes from a user's pages to follow
    log.info("scraping " + userUrl)
    page = s.get(userUrl)
    pageNum = 1
    codeCount = 1
    addCodes = 0
    while codeCount > 0:
        if page.status_code == requests.codes.ok:
            page_html = lxml.html.fromstring(page.text)
            puzzleLinks = page_html.xpath(r'//div[@data-id]') 
            puzzleCodes = [i.attrib['data-id'] for i in puzzleLinks]
            codeCount = len(puzzleCodes)
            followCodes.extend(puzzleCodes)
            pageNum += 1
            page = s.get(userUrl + '/' + str(pageNum))
        else: codeCount = 0
        addCodes += codeCount
    log.info("Added " + str(addCodes) + " followCodes")
 
def scrapePuzzle(puzzCode):
    # get codes from the description and comments of a puzzle page
    puzzle = s.get(puzzleUrl + puzzCode)
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
                finally:
                    pass
    log.debug(addCodes)

## actual code starts here ##
puzzleFile = open(puzzleListFile, 'r') # open the puzzle list file

s = requests.Session()# open a session and login
start = s.get(baseUrl) # starts the secure session - gets cookies
login = s.get(logInUrl) # initiates login
form = {'login':'true','username':username,'password':password}
response = s.post(logInUrl, data=form) # send login data
response.raise_for_status() # raises exception if we didn't log in

# start scraping puzzles
if not(testing):
    scrapeNotifs()
if userUrl:
    scrapeUser(userUrl)
    
if testing:
    scrapePuzzle('26ZCX2BQ') #pumpkin in her jacket
    #scrapePuzzle('US8EUSFG') #Hubble
    #scrapeUser('https://www.jigidi.com/user/Spiritual')

log.debug("Follow codes at start of followCode loop " + str(len(followCodes)))
log.debug(followCodes)
for code in followCodes:
    if followPuzzle(code):
        scrapePuzzle(code)
log.debug("Add codes at start of addCode loop: " + str(len(addCodes)))
log.debug(addCodes)

for code in addCodes:
    if addPuzzle(code):
        scrapePuzzle(code)
log.info("Total Adds:" + str(totalAdds))
log.info("Total Follows:" + str(totalFollows))
log.info("Total Comments:" + str(totalComments))

# write out the puzzle file list
puzzlesLeft = puzzleFile.read()
puzzleFile.close()
puzzleFile = open(puzzleListFile, 'w')
puzzleFile.write(puzzlesLeft)
puzzleFile.close()

# send completion notification
sender = 'raspidude@comcast.net'
smtpPassword = 'Ra5pb3rry'
recievers = ['minimart@me.com']
mailHeader = """From: Raspberry Pi <raspidude@comcast.net>
to: Minimart <minimart@me.com>
Subject: Report
"""
mailBody = str(totalAdds) + " A - " + str(totalFollows) + ' F ' + \
            str(totalComments) + " C"
if fileEmpty: # the file of puzzles for comments it empty
    fileWarning = " and the file is empty"
else:
    fileWarning = ""
msg = mailHeader + mailBody + fileWarning

mailServer = smtplib.SMTP('smtp.comcast.net', 587)
mailServer.login(sender, smtpPassword)
mailServer.starttls()
try:
    mailServer.sendmail(sender, recievers, msg)
    log.debug('Mail sent')
except:
    log.warning('Mail not sent')


