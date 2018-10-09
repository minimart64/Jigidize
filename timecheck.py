#!/usr/bin/env python3

import logging, logging.handlers

# TODO make puzzle and puzzlepub files into lists
# 

# set up the logger
log = logging.getLogger('timecheck')
hdlr = logging.handlers.RotatingFileHandler('/home/pi/Documents/logs/timecheck.log',\
                                            'a',500000,2)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.INFO)
log.info("__________Blank Space_________")
log.info("##### Timecheck #####")
