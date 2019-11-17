import argparse
import inspect
import json
import os
import random
import re
import sys
import threading
import time
from datetime import datetime
from itertools import groupby
from time import sleep

import instabot
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction
from loguru import logger
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm

from .ElementXpath import ElementXpath
from .Predict import Predict
from .Types import MediaType


def isdebugging():
    for frame in inspect.stack():
        if frame[1].endswith("pydevd.py"):
            return True
    return False


class BurbnBot:
    actions = []
    amount_followed: int = 0
    amount_liked: int = 0
    appiumservice = None
    driver = ""
    follow_percentage: int = 0
    instabot = None
    logPath: str = "log/"
    logger = ""
    posts_to_follow = ""
    predict = ""
    settings = {}
    touchaction = None

    def __init__(self, configfile: str = None):
        self.configfile = configfile
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-settings', type=str, help="json settings file")
        args = parser.parse_args()
        self.settings = json.load(open(args.settings))

        self.logger = logger
        self.logger.add("log/{}.log".format(self.settings['instagram']['username']), backtrace=True, diagnose=True,
                        level="WARNING")

        try:
            self.logger.info("Lets do it!.")

            self.predict = Predict(api_key=self.settings['clarifai']['api_key'], logger=self.logger)

            self.instabot = instabot.Bot(base_path="InstaBot/")
            self.instabot.logger = self.logger
            self.instabot.api.logger = self.logger

            self.instabot.login(
                username=self.settings['instagram']['username'],
                password=self.settings['instagram']['password'],
                proxy=None
            )

        except Exception as err:
            self.treat_exception(err)
            self.end()
            pass

    def start_driver(self):
        try:
            sys.stdout.flush()
            self.logger.info("Starting Appium service.")
            os.environ.setdefault(key="ANDROID_HOME", value=self.settings['android']['android_home'])
            self.appiumservice = AppiumService()
            self.appiumservice.stop()
            self.appiumservice.start()

            if self.appiumservice.is_running:
                self.logger.info("Appium Server is running.")
                self.driver = webdriver.Remote(
                    command_executor="http://localhost:4723/wd/hub",
                    desired_capabilities=self.settings['desired_caps']
                )
                self.logger.info("Connected with Appium Server.")
                self.driver.switch_to.context("NATIVE_APP")
                self.driver.implicitly_wait(time_to_wait=10)
                self.touchaction = TouchAction(self.driver)
            self.driver.get(url="https://www.instagram.com/{}/".format(self.settings['instagram']['username']))
            self.driver.get(url="https://www.instagram.com/")
            sys.stdout.write('\r' + 'finished               \n')
        except Exception as err:
            self.logger.critical("Appium not started")
            self.treat_exception(err)

    def stop_driver(self):
        self.driver.quit()
        self.driver.stop_client()
        self.appiumservice.stop()

    def unsave(self, p):
        try:
            self.driver.get(url="https://www.instagram.com/p/{}/".format(p))
            self.driver.find_element_by_xpath(ElementXpath.row_feed_button_save).click()
            self.driver.find_element_by_xpath(ElementXpath.btn_remove_from_collection).click()
            return True
        except Exception as err:
            self.treat_exception(err)
            return False

    def unfollow(self, user):
        self.driver.get(url="https://www.instagram.com/{}/".format(user))
        if self.check_element_exist(ElementXpath.btn_follow):
            self.logger.info("You aren't following {}.".format(user))
            return False
        self.logger.info("Unfollowing user {}, I hope they don't take it personal.".format(user))
        self.driver.find_element_by_xpath(ElementXpath.btn_Following).click()
        self.driver.find_element_by_xpath(ElementXpath.btn_unfollow).click()

        if self.check_element_exist(ElementXpath.button_positive):
            self.driver.find_element_by_xpath(ElementXpath.button_positive).click()
            self.logger.info("If you change your mind, you'll have to request to follow @{} again.".format(user))
        try:
            self.driver.find_element_by_xpath(ElementXpath.btn_follow)
        except NoSuchElementException:
            return False
        return True

    def unfollow_non_followers(self, avoid_saved=True, amount=None):
        self.logger.info("Unfollowing non-followers.")
        following = []
        for a in self.instabot.api.get_total_followings(user_id=self.instabot.user_id):
            following.append(a["username"])

        followers = []
        for b in self.instabot.api.get_total_followers(user_id=self.instabot.user_id):
            followers.append(b["username"])

        if avoid_saved:
            users_saved = self.get_owner_saved_post()
            followers = followers + users_saved

        non_followers = [x for x in following if x not in followers]
        self.logger.info("Setting command to unfollow users.")
        for username in tqdm(non_followers[:amount], desc="Selecting user to unfollow.", unit=" users"):
            self.actions.append(
                {
                    "function": "unfollow",
                    "argument": username
                }
            )

    def get_owner_saved_post(self):
        self.instabot.api.get_saved_medias()
        saveds = self.instabot.last_json['items']
        r = []
        self.logger.info("Getting owner of saved posts")
        for p in saveds:
            r.append(str(p['media']['user']['username']))
        return r

    def treat_exception(self, err):
        self.logger.exception(err)
        if isdebugging:
            breakpoint()

    def end(self):
        self.appiumservice.stop()
        self.logger.info("That's all folks! Bye bye!")
        quit()

    def check_element_exist(self, xpath):
        try:
            self.driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def chimping_timeline(self):
        try:
            self.refreshing()
            amount = random.randint(5, 15)
            count = 0
            self.logger.info("Let's chimping the timeline a bit.")
            el1 = self.driver.find_element_by_id("com.instagram.android:id/action_bar_root")
            start_x = el1.rect["width"] - 50
            start_y = el1.rect["height"] - 50
            end_x = el1.rect["x"] + 50
            end_y = el1.rect["y"] + 50
            while count < amount:
                self.driver.swipe(start_x, start_y, end_x, end_y, duration=random.randint(2500, 4000))
                count += 1
        except Exception as err:
            self.treat_exception(err)
            pass

    def refreshing(self):
        try:
            self.driver.get(url="https://www.instagram.com/")
            self.driver.find_element_by_xpath(ElementXpath.tab_bar_home).click()
            self.driver.find_element_by_xpath(ElementXpath.tab_bar_home).click()
            self.driver.find_element_by_xpath(ElementXpath.top_title).click()

            el1 = self.driver.find_element_by_xpath(ElementXpath.row_feed_photo_profile_name)
            el2 = self.driver.find_element_by_xpath(ElementXpath.tab_bar_camera)

            start_x = el1.rect["x"]
            start_y = el1.rect["y"]
            end_x = el2.rect["x"]
            end_y = el2.rect["y"] - 100
            self.driver.swipe(start_x, start_y, end_x, end_y, duration=random.randint(350, 400))
        except Exception as err:
            self.treat_exception(err)
            pass

    def chimping_stories(self):
        self.refreshing()
        count = 0
        amount = random.randint(2, 5)
        try:
            stories_thumbnails = self.driver.find_elements_by_xpath(ElementXpath.stories_thumbnails)
            stories_thumbnails[1].click()
            self.logger.info("Watching {} stories.".format(amount))
            while count < amount:
                t = random.randint(5, 10)
                sleep(t)
                if self.check_element_exist(xpath=ElementXpath.reel_viewer_texture_view):
                    x1 = random.randint(750, 850)
                    y1 = random.randint(550, 650)
                    x2 = random.randint(200, 300)
                    y2 = random.randint(550, 650)
                    self.driver.swipe(x1, y1, x2, y2, random.randint(500, 1000))
                count += 1
        except Exception as err:
            self.logger.warning("Ops, something wrong while waching stories, sorry.")
            self.treat_exception(err)
            pass

        self.driver.get(url="https://www.instagram.com/{}/".format(self.settings['instagram']['username']))
        self.driver.get(url="https://www.instagram.com/")

    def interact_by_location(self, amount: int = 15, location_id: int = ""):
        self.instabot.api.get_location_feed(location_id=213819997, max_id=9999)
        last_json = self.instabot.last_json
        if amount > len(last_json['items']):
            amount = len(last_json['items'])
        counter = 0
        while counter < amount:
            self.interact(last_json['items'][counter]['id'])
            counter += 1

    def check_item(self, item, concepts=[], concepts_skip=[], max_likes=1000, min_likes=0):
        if not item['like_count'] in range(min_likes, max_likes):
            return False
        if item['has_liked']:
            return False

        if isinstance(concepts, list) and isinstance(concepts_skip, list):
            if item['media_type'] == MediaType.PHOTO:
                url_image = item['image_versions2']['candidates'][0]['url']
            elif item['media_type'] == MediaType.CAROUSEL:
                url_image = item['carousel_media'][0]['image_versions2']['candidates'][0]['url']
            else:
                url_image = item['video_versions'][0]['url']
            predict = self.predict.check(url=url_image, tags=concepts, tags_skip=concepts_skip,
                                         is_video=item['media_type'] == 2)
        else:
            predict = True

        return predict

    def interact_by_hashtag(self, amount: int = 15,
                            hashtag: str = "",
                            ranked_items: bool = True,
                            concepts=[],
                            concepts_skip=[],
                            max_likes=100,
                            min_likes=0):
        try:
            items = []
            next_max_id = ""
            while self.instabot.api.get_hashtag_feed(hashtag, max_id=next_max_id):
                last_json = self.instabot.api.last_json
                next_max_id = last_json['next_max_id']
                if ranked_items:
                    if "ranked_items" in last_json:
                        items = items + last_json['ranked_items']
                items = items + last_json['items']
                items = [i for i in items[0:amount] if self.check_item(item=i,
                                                                       concepts=concepts,
                                                                       concepts_skip=concepts_skip,
                                                                       max_likes=max_likes,
                                                                       min_likes=min_likes)]
                if amount == len(items[0:amount]):
                    items = items[0:amount]
                    break

            return [item for item in items if self.add_action(item, "like")]
        except Exception as err:
            self.logger.warning("Ops, something wrong while working with hashtag #{}, sorry.".format(hashtag))
            self.treat_exception(err)
            pass

    def interact_by_location(self, amount: int = 15,
                             location_id: int = "",
                             ranked_items: bool = True,
                             concepts=[],
                             concepts_skip=[],
                             max_likes=100,
                             min_likes=0):
        try:
            items = []
            next_max_id = ""
            while self.instabot.api.get_location_feed(location_id, max_id=next_max_id):
                last_json = self.instabot.api.last_json
                next_max_id = last_json['next_max_id']
                if ranked_items:
                    if "ranked_items" in last_json:
                        items = items + last_json['ranked_items']
                items = items + last_json['items']
                items = [i for i in items if self.check_item(item=i,
                                                             concepts=concepts,
                                                             concepts_skip=concepts_skip,
                                                             max_likes=max_likes,
                                                             min_likes=min_likes)]
                if amount == len(items[0:amount]):
                    items = items[0:amount]
                    break

            return [item for item in items if self.add_action(item, "like")]
        except Exception as err:
            self.logger.warning("Ops, something wrong while working with location {}, sorry.".format(location_id))
            self.treat_exception(err)
            pass

    def add_action(self, item, function):
        try:
            self.actions.append(
                {
                    "function": function,
                    "argument": {
                        "url": "https://www.instagram.com/p/{}/".format(item["code"]),
                        "media_type": item['media_type']
                    }
                }
            )
            return True
        except:
            return False

    def set_do_follow(self, follow_percentage: int = 0):
        self.follow_percentage = follow_percentage

    def do_actions(self):
        likes_actions = [i for i in self.actions if i["function"] == "like"]
        self.posts_to_follow = []
        if self.follow_percentage > 0:
            self.posts_to_follow = random.sample(range(0, len(likes_actions)),
                                                 int(len(likes_actions) * (self.follow_percentage / 100)))

        amount_actions = int(len(self.actions) / 2)
        if not isdebugging():
            for i in tqdm(range(1, amount_actions), desc="Let's include some (not so real) actions.", unit=" actions"):
                self.actions.append({"function": "chimping_timeline"})
                self.actions.append({"function": "chimping_stories"})

        random.shuffle(self.actions)
        self.actions = [i[0] for i in groupby(self.actions)]

        self.start_android()

        for action in tqdm(self.actions, desc="Execution actions on the phone/emulator", unit=" actions"):
            try:
                method_to_call = getattr(self, action['function'])
                if "argument" in action:
                    method_to_call(action['argument'])
                    sleep(random.randint(3, 10))
                else:
                    method_to_call()
            except Exception as err:
                self.logger.warning(
                    "Ops, something with the action {} ({}), sorry.".format(action['function'], action['argument']))
                self.treat_exception(err)
                pass
        self.stop_driver()

    def start_android(self):
        starting_appium = threading.Thread(name='process', target=self.start_driver)
        starting_appium.start()
        while starting_appium.isAlive():
            self.animated_loading()

    def follow(self):
        if self.save_in_collection():
            try:
                self.driver.find_element_by_xpath(ElementXpath.btn_follow).click()
                user = self.driver.find_element_by_xpath(ElementXpath.action_bar_textview_title).text
                self.logger.info("Following user {}.".format(user))
                self.amount_followed += 1
                print(self.amount_followed)
                return True
            except Exception as err:
                self.treat_exception(err)
                return False
                pass
        else:
            return False

    def save_in_collection(self):
        try:
            button_save = self.driver.find_element_by_xpath(ElementXpath.row_feed_button_save)
            self.touchaction.long_press(button_save)
            self.touchaction.perform()

            strdate = datetime.now().strftime("%Y%m%d")

            if self.check_element_exist(ElementXpath.create_collection_edit_text):
                self.logger.info("Zero collection, let's create the first one.")
                collection_today = []
            else:
                collection_names = self.driver.find_elements_by_xpath(ElementXpath.collection_name)
                collection_today = [i for i in collection_names if i.text == strdate]

            if len(collection_today) > 0:
                collection_today[0].click()
            else:
                if self.check_element_exist(ElementXpath.save_to_collection_new_collection_button):
                    self.driver.find_element_by_xpath(ElementXpath.save_to_collection_new_collection_button).click()
                self.driver.find_element_by_xpath(ElementXpath.create_collection_edit_text).send_keys(strdate)
                self.driver.find_element_by_xpath(ElementXpath.save_to_collection_action_button).click()

            self.driver.find_element_by_xpath(ElementXpath.row_feed_photo_profile_name).click()
            return True
        except Exception as e:
            self.logger.warning("Post not saved!")
            self.treat_exception(e)
            return False

    def like(self, param):
        url = param["url"]
        media_type = param["media_type"]
        self.driver.get(url=url)
        try:
            e = self.driver.find_element_by_xpath(ElementXpath.row_feed_button_like)
            if e.tag_name == "Liked":
                self.logger.info("Ops, you already like this one, sorry.")
                return False
            else:

                if media_type == MediaType.VIDEO:
                    self.wait_random()
                elif media_type == MediaType.CAROUSEL:
                    self.swipe_carousel()

                e.click()
                # sleep(random.randint(1, 3))
                self.logger.info("Image {} Liked.".format(url))
                if self.amount_liked in self.posts_to_follow:
                    self.follow()
                return True
        except Exception as err:
            self.logger.warning("Ops, something wrong on try to like {}, sorry.".format(url))
            self.logger.error(err)
            self.treat_exception(err)
            return False
            pass

    def watch_stories(self):
        try:
            while self.check_element_exist(xpath=ElementXpath.reel_viewer_texture_view):
                t = random.randint(2, 10)
                self.logger.info("Sleeping for {} seconds.".format(t))
                sleep(t)
                if self.check_element_exist(xpath=ElementXpath.reel_viewer_texture_view):
                    self.logger.info("Tap")
                    self.driver.tap([(800, 600)], random.randint(3, 10))
        except Exception as err:
            self.logger.warning("Ops, something wrong while waching stories, sorry.")
            self.treat_exception(err)
            pass

    def get_info(self):
        row_feed_photo_profile_name = self.driver.find_element_by_xpath(ElementXpath.row_feed_photo_profile_name)
        owner_username = row_feed_photo_profile_name.text.replace(" •", "")
        has_liked = self.driver.find_element_by_id("com.instagram.android:id/row_feed_button_like").tag_name == "Liked"
        self.get_type_post()

    def swipe_carousel(self):
        try:
            carousel_image = self.driver.find_element_by_xpath(ElementXpath.carousel_image)
            match = re.search(r"(\d+).*?(\d+)", carousel_image.tag_name)
            n = int(match.group(2))
        except NoSuchElementException as err:
            n = 2  # if don't find the number of pictures work with only 2
            pass
        self.logger.warning("Let's check all the {} images here.".format(n))
        for x in range(n - 1):
            self.driver.swipe(800, 600, 250, 600, random.randint(500, 1000))
        for x in range(n - 1):
            self.driver.swipe(300, 650, 800, 600, random.randint(500, 1000))

    @staticmethod
    def wait_random():
        t = random.randint(5, 15)
        sleep(t)

    def get_collections(self):
        self.instabot.api.send_request("collections/list/")
        return self.instabot.last_json

    def get_collection(self, collection_id):
        self.instabot.api.send_request("feed/collection/{}/".format(collection_id))
        return self.instabot.last_json

    def unfollow_by_collection(self, name):
        collections = self.get_collections()
        for c in collections["items"]:
            if c['collection_name'] == name:
                collection = self.get_collection(collection_id=c['collection_id'])
                for i in tqdm(collection["items"], desc="Getting users from colletion {} to unfollow.".format(name)):
                    self.actions.append(
                        {
                            "function": "unfollow",
                            "argument": i['media']['user']['username']
                        }
                    )
                    self.actions.append(
                        {
                            "function": "unsave",
                            "argument": i['media']['code']
                        }
                    )

    @staticmethod
    def animated_loading():
        chars = "/—\|"
        for char in chars:
            sys.stdout.write('\r' + 'loading service...' + char)
            time.sleep(.1)
            sys.stdout.flush()
