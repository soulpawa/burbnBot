import argparse
import json
import logging
import os
import random
import re
from time import sleep

import instabot
from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

from .GraphQL import GraphQl
from .MediaType import MediaType
from .Predict import Predict


class BurbnBot:
    dc = {}
    logPath = "log/"
    username = ""
    driver = ""
    graphql = GraphQl()
    instabot = None
    appiumservice = None
    settings = {}
    do_likes = []
    actions = []

    def __init__(self, configfile: str = None):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-settings', type=str, help="json settings file")
        args = parser.parse_args()
        self.settings = json.load(open(args.settings))

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
            handlers=[
                logging.FileHandler("{0}/{1}.log".format(self.logPath, self.username)),
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
            self.do_exception(err)
            self.end()
            pass

    def start_driver(self):
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

    def stop_driver(self):
        self.driver.quit()
        self.driver.stop_client()
        self.appiumservice.stop()

    def unfollow(self, user):
        elem_following = "//*[@resource-id='com.instagram.android:id/profile_header_actions_top_row']//*[@text='Following']"
        elem_unfollow = "//*[@resource-id='com.instagram.android:id/follow_sheet_unfollow_row']"
        elem_follow = "//*[@class='android.widget.LinearLayout']//*[@text='Follow']"

        p = "https://www.instagram.com/{}/".format(user)
        self.driver.get(url=p)

        WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, elem_following)))
        self.driver.find_element_by_xpath(elem_following).click()

        WebDriverWait(self.driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, elem_unfollow)))
        self.driver.find_element_by_xpath(elem_unfollow).click()

        if self.check_element_exist("button_positive"):
            self.driver.find_element_by_xpath("//*[@resource-id='com.instagram.android:id/button_positive']").click()
            self.logger.info("If you change your mind, you'll have to request to follow @{} again.".format(user))
        try:
            self.driver.find_element_by_xpath(elem_follow)
        except NoSuchElementException:
            return False
        return True

    def unfollow_non_followers(self, avoid_saved=True, n_to_unfollows=None):
        self.logger.info("Unfollowing non-followers.")
        following = self.instabot.following

        if avoid_saved:
            users_saved = self.get_owner_saved_post()
            followers = self.instabot.followers + users_saved
        else:
            followers = self.instabot.followers

        non_followers = [x for x in following if x not in followers]
        for user_id in tqdm(non_followers[:n_to_unfollows]):
            username = self.instabot.get_username_from_user_id(user_id=user_id)
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
        for p in tqdm(saveds):
            r.append(str(p['media']['user']['pk']))
        return r

    def do_exception(self, err):
        self.logger.error(err)

    def end(self):
        self.appiumservice.stop()
        self.logger.info("That's all folks! Bye bye!")
        quit()

    def check_element_exist(self, id):
        try:
            self.driver.find_element_by_id(id)
        except NoSuchElementException:
            return False
        return True

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
        hashtag_medias = self.instabot.get_hashtag_medias(hashtag=hashtag, filtration=False)
        counter = 0
        while counter <= amount:
            self.interact(hashtag_medias[counter])
            counter += 1

    def interact(self, id_medias):
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

    def do_actions(self):
        self.start_driver()
        random.shuffle(self.actions)
        for action in tqdm(self.actions):
            try:
                method_to_call = getattr(self, action['function'])
                method_to_call(action['argument'])
            except Exception as err:
                self.do_exception(err)
                pass
        self.stop_driver()

    def like(self, param):
        url = param["url"]
        media_type = param["media_type"]
        self.driver.get(url=url)
        try:
            WebDriverWait(self.driver, 10).until(expected_conditions.presence_of_element_located(
                (By.XPATH, "//*[@resource-id='com.instagram.android:id/row_feed_button_like']")))
            e = self.driver.find_element_by_xpath("//*[@resource-id='com.instagram.android:id/row_feed_button_like']")
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
                self.logger.info("Image Liked.")
                return True
        except Exception as err:
            self.logger.info("Ops, something wrong on like, sorry.")
            self.logger.error(err)
            return False
            pass

    def watch_stories(self, home: bool = True):
        try:
            while self.check_element_exist(id="reel_viewer_texture_view"):
                t = random.randint(5, 15)
                self.logger.info("Sleeping for {} seconds.".format(t))
                sleep(t)
                if self.check_element_exist(id="reel_viewer_texture_view"):
                    self.logger.info("Tap")
                    self.driver.tap([(800, 600)], random.randint(3, 10))
        except Exception as err:
            self.logger.info("Ops, something wrong while waching stories, sorry.")
            self.logger.error(err)
            pass

    def get_info(self):
        row_feed_photo_profile_name = self.driver.find_element_by_id(
            "com.instagram.android:id/row_feed_photo_profile_name")
        owner_username = row_feed_photo_profile_name.text.replace(" •", "")
        has_liked = self.driver.find_element_by_id("com.instagram.android:id/row_feed_button_like").tag_name == "Liked"
        self.get_type_post()

    def swipe_carousel(self):
        if self.get_type_post() == "carousel":
            try:
                carousel_image = self.driver.find_element_by_xpath(
                    "//*[@resource-id='com.instagram.android:id/carousel_image']")
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
            pass
        self.logger.info('Watching video for {} seconds.'.format(t))
        sleep(t)

    def get_type_post(self):
        r = "photo"
        if self.check_element_exist(id="com.instagram.android:id/carousel_page_indicator"):
            r = "carousel"
        elif self.check_element_exist("com.instagram.android:id/progress_bar"):
            r = "video"

        return r
