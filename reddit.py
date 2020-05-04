#!/usr/bin/env python3

import requests, lxml.html, sys, logging, logging.handlers, smtplib, configparser
import time, os, shutil, urllib.request, ssl, socket
from pprint import pprint
import json, praw

# set up the logger
log = logging.getLogger('reddit')
hdlr = logging.handlers.RotatingFileHandler('/home/pi/Documents/logs/reddit.log',\
                                            'a',500000,2)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)
log.info("__________Blank Space_________")
log.info("##### Starting to Scrape Reddit #####")

imgDir = '/home/pi/Downloads/img/reddit'

# URLs
baseUrl = "https://www.reddit.com"
logInUrl = baseUrl + "/login"
signInUrl = baseUrl + "/user/ajax/signin"
contriUrl = baseUrl + "/contributions/redclouds-regular"

# some global variables
true = 1
false = 0
fail = 0
time_delay = 60*60*6
picAdds = []
contriLinks = []
followCodes = []
myCodes = []
loadTimes = []
totalAdds = totalFollows = totalComments = 0
fileEmpty = 0
loadFailCount = loadErrCount = 0
mailComment = ""
platform = socket.gethostname()

# read in the configuration file
# try to open the file, if it's not there, create one
# add -c switch to allow editing of the file
config = configparser.ConfigParser()
config.read('/var/lib/scrape/reddit.cfg')
try:
    # platform = config.get('settings','platform')
    my_username = config.get('credentials','username')
    my_password = config.get('credentials','password')
    clientid = config.get('credentials','clientid')
    clientsecret = config.get('credentials','clientsecret')
    useragent = config.get('credentials','useragent')
    sender = config.get('credentials','sender')
    smtpPassword = config.get('credentials','smtpPassword')
    reciever = config.get('settings','reciever')
    smtpServer = config.get('settings','smtpServer')
except:
    log.info("Configuration file error - recreating the file")
    print("There was a proplem with the configuration file, it needs to be recreated")
    config = configparser.SafeConfigParser()
    config.add_section("credentials")
    my_username = input("Reddit Username?")
    config.set('credentials','username',my_username)
    my_password = input("Reddit Password?")
    config.set('credentials','password',my_password)
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
    with open('/var/lib/scrape/reddit.cfg','w') as configFile:
        config.write(configFile)
finally:
    pass

###### Methods ######
    
def getPic(url):
    # saves the pic to local storage
    global totalAdds
    image_name = url.split('/')[-1].split('?')[0]
    if image_name.endswith(".jpg") or image_name.endswith(".png") \
            or image_name.endswith(".jpeg"):
        log.debug("get image at " + url)
        #splits = image_name.split('?')
        #if len(splits) >1:
        #    image_name = splits[0]
        image = requests.get(url, stream=True)
        with open (imgDir + '/' + image_name, 'wb') as fd:
            for chunk in image.iter_content(chunk_size=128):
                fd.write(chunk)
        totalAdds += 1

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
    mailHeader = "From: Raspberry Pi <" + sender + ">\nto: " + my_username + \
    " <" + reciever + ">\nSubject: Report Reddit " + platform + "\n"
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

#############################
## actual code starts here ##

# if there are already over 1,000 pics in img, dont get more
if len(os.listdir(imgDir)) > 1000:
    print("You already have 1,000 imgs")
    raise SystemExit

# attempt to connect to the API
try:
    reddit = praw.Reddit(client_id=clientid,
                     client_secret=clientsecret,
                     user_agent=useragent,
                     username = my_username,
                     password = my_password)
except:
    print("Failed to load api")
    log.warning("Failed to load api")
    raise SystemExit
finally:
    pass

# read the first 300 items in the front page
for submission in reddit.front.new(limit=300):
    log.debug(submission.url)
    if submission.is_video:
        log.debug("video")
    elif submission.created_utc < time.time() - time_delay:
        log.debug("too old " + str(submission.created_utc))
    else:
        picAdds.append(submission.url)
    
# get the actual images
log.info("images to add: " + str(len(picAdds)))
for pic in picAdds:
    # get each image and save it
    getPic(pic)

log.info("Total Adds:" + str(totalAdds))
sendEmail()

# all done
