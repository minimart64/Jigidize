#!/usr/bin/env python3

import requests, lxml.html, sys, logging, logging.handlers, smtplib, configparser
import time, os, shutil, urllib.request

# TODO make puzzle and puzzlepub files into lists
# TODO add scrape of my puzzles to bookmark and build puzzle list

# set up the logger
log = logging.getLogger('rc')
hdlr = logging.handlers.RotatingFileHandler('/home/pi/Documents/logs/rc.log',\
                                            'a',500000,7)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)
log.info("__________Blank Space_________")
log.info("##### Starting to Scrape RC #####")

imgDir = '/home/pi/Downloads/img'

# URLs
baseUrl = "https://www.redclouds.com"
logInUrl = baseUrl + "/user/signin"
signInUrl = baseUrl + "/user/ajax/signin"
contriUrl = baseUrl + "/contributions/redclouds-regular"

# some global variables
true = 1
false = 0
fail = 0
picAdds = []
contriLinks = []
followCodes = []
myCodes = []
loadTimes = []
totalAdds = totalFollows = totalComments = 0
fileEmpty = 0
loadFailCount = loadErrCount = 0
mailComment = ""

# check to see if arguments were passed in with the command
inputValues = sys.argv
userUrl = None
publishCount = newPuzzleCount = newPubPuzzCount = setSize = notif = \
    scrapeMyPuzzles = recoverMyPuzzles = privatize = makingPuzzles = \
    privatizingPuzzles = testing = 0

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
    else:
        print("invalid argument")
        raise SystemExit
else: notif = True
    

# read in the configuration file
# try to open the file, if it's not there, create one
# add -c switch to allow editing of the file
config = configparser.SafeConfigParser()
config.read('/var/lib/scrape/rc.cfg')
try:
    #testing = int(config.get('settings','testing'))
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
    username = input("RC Username?")
    config.set('credentials','username',username)
    password = input("RC Password?")
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
    with open('/var/lib/scrape/rc.cfg','w') as configFile:
        config.write(configFile)
finally:
    pass

###### Methods ######

def scrapeContris():
	# get all the new contributions
    log.info("scraping contributions")
    contrisPage = loadPage(contriUrl)
    if contrisPage:
        date = time.strftime("%Y-%m-%d")
        contris_html = lxml.html.fromstring(contrisPage.text)
        contris = contris_html.xpath(r'//div[@data-date="' + date + '"]/child::a[@class="pv"]') 
        log.debug(contris)
        for i in contris:
            contriLinks.append(i.attrib['href'])
            log.debug("added " + i.attrib['href'])
        log.debug(contriLinks)
        
def scrapeImages(pageUrl, pageFile):
    # get the images from the contribution page
    log.debug("Scraping " + pageUrl)
    page_html = lxml.html.fromstring(pageFile.text)
    picLinks = page_html.xpath(r'//a[@class="one-preview"]')
    for i in picLinks:
        picAdds.append(i.attrib['href'])
        log.debug("added " + i.attrib['href'])
    #pics = [i.attrib['href'] for i in picLinks]
    #log.debug("pics to add")
    #log.debug(pics)
    #picAdds.append(pics)
    log.debug("total pics " + str(len(picAdds)))
    log.debug(picAdds)
    
def getPic(url):
    # saves the pic to local storage
    global totalAdds
    image_name = url.split('/')[-1]
    log.debug("get image at " + url)
    image = s.get(url, stream=True)
    with open (imgDir + '/' + image_name, 'wb') as fd:
        for chunk in image.iter_content(chunk_size=128):
            fd.write(chunk)
    totalAdds += 1
    #urllib.request.urlretrieve(url, imgDir + '/' + image_name)

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

def sendEmail():
    # send completion notification
    log.debug("starting to send email")
    global totalAdds, totalFollows, totalComments, fileEmpty, sender, \
            smtpPassword, smtpServer, mailComment
    mailHeader = "From: Raspberry Pi <" + sender + ">\nto: " + username + \
    " <" + reciever + ">\nSubject: Report fan RC\n"
    recievers = [reciever]
    mailBody = str(totalAdds) + "-A "
    if len(loadTimes) > 0:
        statistics = str(loadFailCount) + "-LF " + \
                    str(loadErrCount) + "-LE " + str(len(loadTimes)) \
                    + "-TPL - "
        statistics += "ALT = " + str(sum(loadTimes)/len(loadTimes))
    else:
        statistics = ""
    msg = mailHeader + mailBody + statistics
    log.debug("Mail message: " + msg)
    mailServer = smtplib.SMTP('smtp.comcast.net', 587)
    mailServer.login(sender, smtpPassword)
    mailServer.starttls()
    try:
        mailServer.sendmail(sender, recievers, msg)
        log.info('Mail sent')
        log.info(statistics)
    except:
        log.warning('Mail not sent')

#############################
## actual code starts here ##
try:
    s = requests.Session()# open a session and login
    start = s.get(baseUrl) # starts the secure session - gets cookies
    login = s.get(logInUrl) # initiates login
    form = {'email':username,'password':password}
    response = s.post(signInUrl, data=form) # send login data
    if response.status_code == requests.codes.ok:
        log.debug("login successful")
    else:
        log.warning("login failure")
        raise SystemExit
except:
    log.warning("Failed to load login pages")
    raise SystemExit
finally:
    pass

# start scraping puzzles
if testing: # in config file or -test passed in
    log.info("Testing")
    #puzzle = loadPage(puzzleUrl + '26ZCX2BQ')
    #addCodes.append('6X8PDQQN') 
    #myCodes.append('26ZCX2BQ') #pumpkin in her jacket
    #myCodes.append('MUM8225R') #pretty in pink
    #if puzzle:
        #addMine(puzzle, '26ZCX2BQ') #pumpkin in her jacket
        #publishPuzzle('26ZCX2BQ') #pumpkin in her jacket
    #scrapePuzzle('US8EUSFG') #Hubble
    #scrapeUser('https://www.jigidi.com/user/Spiritual')
    #scrapeMine()
if not testing:
    scrapeContris()

# get links to images
log.info("contris to scrape: " + str(len(contriLinks)))
for link in contriLinks:
    page = loadPage(baseUrl+link)
    scrapeImages(link, page)
    
# get the actual images
log.info("images to add: " + str(len(picAdds)))
for pic in picAdds:
    # get each image and save it
    getPic(pic)

log.info("Total Adds:" + str(totalAdds))
#log.info("Total Follows:" + str(totalFollows))
#log.info("Total Comments:" + str(totalComments))

#writeList(puzzleFile, puzzleListFile)
sendEmail()

# all done
