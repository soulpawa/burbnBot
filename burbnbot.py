import time

from BurbnBot.BurbnBot import BurbnBot

burbn = BurbnBot(configfile="config/credentials.json")

burbn.test(profile="melanin.gram")

breakpoint()

burbn.get_info_post()