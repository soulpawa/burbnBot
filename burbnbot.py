from BurbnBot.BurbnBot import BurbnBot

burbn = BurbnBot()

burbn.unfollow_non_followers(avoid_saved=True)

burbn.do_actions()

