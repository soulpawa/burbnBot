import argparse
import inspect
import json
import logging
import os
import random
import re
import sys
import threading
import time
import traceback
from datetime import datetime
from itertools import groupby
from time import sleep

import instabot
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
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
    logPath = "log/"
    username = ""
    driver = ""
    instabot = None
    appiumservice = None
    touchaction = None
    settings = {}
    actions = []
    follow_percentage = 50
    amount_liked = 0
    amount_followed = 0

    def __init__(self, configfile: str = None):
        self.configfile = configfile
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-settings', type=str, help="json settings file")
        args = parser.parse_args()
        self.settings = json.load(open(args.settings))

        if isdebugging:
            debuglevel = logging.ERROR
        else:
            debuglevel = logging.INFO

        logging.basicConfig(
            level=debuglevel,
            format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
            handlers=[
                logging.FileHandler("{0}/{1}.log".format(self.logPath, self.settings['instagram']['username'])),
                logging.StreamHandler()
            ])

        self.logger = logging.getLogger()

        try:
            self.logger.info("Lets do it!.")

            self.predict = Predict(api_key=self.settings['clarifai']['api_key'])

            self.instabot = instabot.Bot(base_path="InstaBot/")

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
                self.driver.implicitly_wait(time_to_wait=30)
                self.touchaction = TouchAction(self.driver)
            self.driver.get(url="https://www.instagram.com/{}/".format(self.settings['instagram']['username']))
            sys.stdout.write('\r' + 'finished               \n')
        except Exception as err:
            self.treat_exception(err)

    def stop_driver(self):
        self.driver.quit()
        self.driver.stop_client()
        self.appiumservice.stop()

    def unfollow(self, user):
        self.driver.get(url="https://www.instagram.com/{}/".format(user))
        self.logger.info("Unfollowing user {}, I hope they don't take it personal.".format(user))

        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, ElementXpath.btn_Following)))
        self.driver.find_element_by_xpath(ElementXpath.btn_Following).click()

        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, ElementXpath.btn_unfollow)))
        self.driver.find_element_by_xpath(ElementXpath.btn_unfollow).click()

        sleep(2)
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
        if type(err).__name__ == 'WebDriverException':
            self.start_android()
            self.logger.error(msg=err.msg)
            self.logger.error(msg=traceback.format_exc())
            pass
        elif hasattr(err, 'msg'):
            self.logger.error(msg=err.msg)
        self.logger.error(msg=traceback.format_exc())
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
            self.driver.get(url="https://www.instagram.com/{}/".format(self.username))
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.XPATH, ElementXpath.tab_bar_home)))
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
            self.logger.info("Ops, something wrong while waching stories, sorry.")
            self.treat_exception(err)
            pass

        self.driver.get(url="https://www.instagram.com/{}/".format(self.username))

    def interact_by_location(self, amount: int = 15, location_id: int = ""):
        self.instabot.api.get_location_feed(location_id=213819997, max_id=9999)
        last_json = self.instabot.last_json
        if amount > len(last_json['items']):
            amount = len(last_json['items'])
        counter = 0
        while counter < amount:
            self.interact(last_json['items'][counter]['id'])
            counter += 1

    def interact_by_hashtag(self, amount: int = 15, hashtag: str = None):
        try:
            hashtag_medias = self.instabot.get_hashtag_medias(hashtag=hashtag, filtration=False)
            counter = 0
            if amount > len(hashtag_medias):
                amount = len(hashtag_medias)

            for i in tqdm(range(0, amount), desc="Selecting posts with the hashtag #{}.".format(hashtag),
                          unit=" posts"):
                if self.interact(hashtag_medias[counter]):
                    counter += 1
        except Exception as err:
            self.logger.info("Ops, something wrong while working with hashtag #{}, sorry.".format(hashtag))
            self.treat_exception(err)
            pass

    def interact(self, id_medias):
        try:
            post_info = self.instabot.get_media_info(media_id=id_medias)

            if post_info[0]['media_type'] == MediaType.PHOTO:
                url_image = post_info[0]['image_versions2']['candidates'][0]['url']
            elif post_info[0]['media_type'] == MediaType.CAROUSEL:
                url_image = post_info[0]['carousel_media'][0]['image_versions2']['candidates'][0]['url']
            else:
                url_image = post_info[0]['video_versions'][0]['url']

            p = "https://www.instagram.com/p/{}/".format(post_info[0]['code'])
            self.logger.info("Checking post {}.".format(p))

            if not post_info[0]['has_liked']:
                if self.predict.check(self.logger, url=url_image,
                                      tags=self.settings['clarifai']['concepts'],
                                      tags_skip=self.settings['clarifai']['concepts_skip'],
                                      is_video=(post_info[0]['media_type'] == 2)):
                    self.actions.append(
                        {
                            "function": "like",
                            "argument": {
                                "url": p,
                                "media_type": post_info[0]['media_type']
                            }
                        }
                    )
            return True
        except Exception as err:
            self.treat_exception(err)
            return False
            pass

    def set_do_follow(self, follow_percentage: int = 0):
        self.follow_percentage = follow_percentage

    def do_actions(self):
        likes_actions = [i for i in self.actions if i["function"] == "like"]
        self.posts_to_follow = random.sample(range(0, len(likes_actions)),
                                             int(len(likes_actions) * (self.follow_percentage / 100)))

        amount_actions = len(self.actions)
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
                self.logger.info(
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
            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.XPATH, ElementXpath.btn_follow)))
            self.driver.find_element_by_xpath(ElementXpath.btn_follow).click()
            user = self.driver.find_element_by_xpath(ElementXpath.action_bar_textview_title).text
            self.logger.info("Following user {}.".format(user))
            return True
        except Exception as err:
            self.treat_exception(err)
            return False
            pass

    def like(self, param):
        url = param["url"]
        media_type = param["media_type"]
        self.driver.get(url=url)
        try:
            WebDriverWait(self.driver, 10).until(expected_conditions.presence_of_element_located(
                (By.XPATH, ElementXpath.row_feed_button_like)))
            e = self.driver.find_element_by_xpath(ElementXpath.row_feed_button_like)
            if e.tag_name == "Liked":
                self.logger.info("Ops, you already like this one, sorry.")
                return False
            else:

                if media_type == MediaType.VIDEO:
                    self.watch_video()
                elif media_type == MediaType.CAROUSEL:
                    self.swipe_carousel()

                e.click()
                sleep(random.randint(1, 3))
                self.logger.info("Image {} Liked.".format(url))
                if self.amount_liked in self.posts_to_follow:
                    self.follow()
                return True
        except Exception as err:
            self.logger.info("Ops, something wrong on try to like {}, sorry.".format(url))
            self.logger.error(err)
            self.treat_exception(err)
            return False
            pass

    def watch_stories(self):
        try:
            while self.check_element_exist(xpath=ElementXpath.reel_viewer_texture_view):
                t = random.randint(5, 15)
                self.logger.info("Sleeping for {} seconds.".format(t))
                sleep(t)
                if self.check_element_exist(xpath=ElementXpath.reel_viewer_texture_view):
                    self.logger.info("Tap")
                    self.driver.tap([(800, 600)], random.randint(3, 10))
        except Exception as err:
            self.logger.info("Ops, something wrong while waching stories, sorry.")
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
        except Exception as err:
            n = 2  # if don't find the number of pictures work with only 2
            pass
        self.logger.info("Let's check all the {} images here.".format(n))
        for x in range(n - 1):
            self.driver.swipe(800, 600, 250, 600, random.randint(500, 1000))
        for x in range(n - 1):
            self.driver.swipe(300, 650, 800, 600, random.randint(500, 1000))

    def watch_video(self):
        t = random.randint(5, 15)
        try:
            clock = self.driver.find_element_by_id("com.android.systemui:id/status_bar_left_side")
            t = ((clock.text.split(':')[0] * 60) + clock.text.split(':')[1])
        except Exception as err:
            self.treat_exception(err)
            pass
        self.logger.info('Watching video for {} seconds.'.format(t))
        sleep(t)

    def animated_loading(self):
        chars = "/—\|"
        for char in chars:
            sys.stdout.write('\r' + 'loading service...' + char)
            time.sleep(.1)
            sys.stdout.flush()
