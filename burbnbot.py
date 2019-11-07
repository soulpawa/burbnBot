from BurbnBot.BurbnBot import BurbnBot

# https://www.instagram.com/p/B4fgT13nYkZ/?igshid=bv81bcl5jz0n
burbn = BurbnBot(configfile="config/credentials.json")

burbn.hashtag_interact(hashtag="chicagomodel", aba="top", stories=False)
