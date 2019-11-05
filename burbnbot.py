import time

from BurbnBot.BurbnBot import BurbnBot

burbn = BurbnBot(configfile="config/credentials.json")

burbn.test(profile="black.h.i.v.e")

burbn.check_post()

breakpoint()

burbn.get_info_post()