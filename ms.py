#!/usr/bin/env python3

import requests, lxml.html, sys, logging, logging.handlers, smtplib, configparser
import time, os, shutil, urllib.request

# TODO make puzzle and puzzlepub files into lists
# TODO add scrape of my puzzles to bookmark and build puzzle list

# set up the logger
log = logging.getLogger('ms')
hdlr = logging.handlers.RotatingFileHandler('/home/pi/Documents/logs/ms.log',\
                                            'a',500000,2)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)
log.info("__________Blank Space_________")
log.info("##### Starting to Scrape MS #####")

imgDir = '/home/pi/Downloads/img/ms'

# URLs
baseUrl = "https://malibustrings.com"
contriUrl = baseUrl + "/competition.html"

# some global variables
fail = 0
picAdds = []
contriLinks = []
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
    platform = config.get('settings','platform')
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
    platform = input('computer name?')
    config.set('settings','platform','platform')
    config.set('settings','testing','0')
    testing = 0
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
        contris_html = lxml.html.fromstring(contrisPage.text)
        contris = contris_html.xpath(r'//td[@align="center"]/child::a') 
        log.debug(contris)
        counter = 0
        for i in contris:
            link = i.attrib['href']
            log.debug(link)
            if link.startswith("/competition"):
                counter += 1
                contriLinks.append(link)
                log.debug("added " + link)
            if counter >= 5:
                return
        log.debug(contriLinks)

def getGal(indexUrl, pageFile):
    # get gallery link from index page
    # returns the latest link
    log.debug("getting gallery link from " + indexUrl)
    page_html = lxml.html.fromstring(pageFile.text)
    galLinks = page_html.xpath(r'//td[@align="center"]/child::a')
    log.debug(galLinks)
    galLink = galLinks[-1].attrib['href']
    log.debug("gallery link is " + galLink)
    return galLink

def scrapeImages(pageUrl, pageFile):
    # get the images from the contribution page
    log.debug("Scraping " + pageUrl)
    page_html = lxml.html.fromstring(pageFile.text)
    picLinks = page_html.xpath(r'//div[@id="vlightbox1"]/child::a[@class="vlightbox1"]')
    for i in picLinks:
        picAdds.append(pageUrl + i.attrib['href'])
        log.debug("added " + i.attrib['href'])
    log.debug("total pics " + str(len(picAdds)))
    log.debug(picAdds)
    
def getPic(url):
    # saves the pic to local storage
    global totalAdds
    image_name = url.split('/')[-4] + '-' + url.split('/')[-1]
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
        return False
    finally:
        pass

def sendEmail():
    # send completion notification
    log.debug("starting to send email")
    global totalAdds, totalFollows, totalComments, fileEmpty, sender, \
            smtpPassword, smtpServer, mailComment
    mailHeader = "From: Raspberry Pi <" + sender + ">\nto: " + username + \
    " <" + reciever + ">\nSubject: Report MS " + platform + "\n"
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
    #login = s.get(logInUrl) # initiates login
    #form = {'email':username,'password':password}
    #response = s.post(signInUrl, data=form) # send login data
    if start.status_code == requests.codes.ok:
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
    if link.endswith("index.html"):
        page = loadPage(baseUrl+link)
        galLink = getGal(link, page)
    else: galLink = baseUrl+link
    page = loadPage(galLink)
    scrapeImages(galLink, page)
    
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
