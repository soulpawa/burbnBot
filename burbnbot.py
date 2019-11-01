import time

from BurbnBot.BurbnBot import BurbnBot

burbn = BurbnBot(configfile="config/credentials.json")


burbn.test()

burbn.scrool_down()