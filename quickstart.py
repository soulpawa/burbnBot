from BurbnBot.BurbnBot import BurbnBot

burbn = BurbnBot()

burbn.unfollow_non_followers(avoid_saved=True, amount=10)

burbn.interact_by_hashtag(amount=35, hashtag="fitbabe")

burbn.unfollow_by_collection(name="20191114")

burbn.set_do_follow(follow_percentage=50)

burbn.do_actions()
