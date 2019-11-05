import time

from BurbnBot.BurbnBot import BurbnBot

burbn = BurbnBot(configfile="config/credentials.json")

breakpoint()

burbn.check_post()

# burbn.hashtag_interact(hashtag="chicagomodel", top=True, recent=True)