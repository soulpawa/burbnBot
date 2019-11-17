from BurbnBot.BurbnBot import BurbnBot

burbn = BurbnBot()

burbn.unfollow_non_followers(avoid_saved=False, amount=999999)

breakpoint()
burbn.do_actions()
