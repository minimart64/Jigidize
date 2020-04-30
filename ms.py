#!/usr/bin/env python3

import requests, lxml.html, sys, logging, logging.handlers, smtplib, configparser
import time, os, shutil, urllib.request, ssl, socket

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
platform = socket.gethostname()

# read in the configuration file
# try to open the file, if it's not there, create one
# TODO make the edit a better method
config = configparser.ConfigParser()
config.read('/var/lib/scrape/rc.cfg')
try:
    # platform = config.get('settings','platform')
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
    # build the message
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
    # create a secure SSL context
    sslContext = ssl.create_default_context()
    # Try to log in to server and send email
    try:
        mailServer = smtplib.SMTP('smtp.comcast.net', 587)
        mailServer.starttls(context=sslContext)
        mailServer.login(sender, smtpPassword)
        mailServer.sendmail(sender, recievers, msg)
        log.info('Mail sent')
        log.info(statistics)
    except Exception as e:
        log.warning('Mail not sent')
        log.warning(e)
        #print the exceptiong for testing
        print(e)

#############################
## actual code starts here ##
try:
    s = requests.Session()# open a session
    start = s.get(baseUrl) # starts the secure session - gets cookies
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

# start scraping
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
sendEmail()

# all done
