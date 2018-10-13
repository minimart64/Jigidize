#!/usr/bin/env python3

import logging, logging.handlers # for the log
from gpiozero import CPUTemperature

# TODO add proc temp, etc

# set up the logger
log = logging.getLogger('timecheck')
hdlr = logging.handlers.RotatingFileHandler('/home/pi/Documents/logs/timecheck.log',\
                                            'a',500000,2)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.INFO)
log.debug("__________Blank Space_________")

# get temps and stuff
cpu = CPUTemperature()
cpuC = cpu.temperature
cpuF = cpuC * 1.8 + 32
log.debug(str(cpuC) + " / " + str(cpuF))




log.info("Timecheck - Temp: " + str(cpuC) + "/" + str(cpuF))
