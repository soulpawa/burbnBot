import argparse
import json
import logging
import os
import random
from time import sleep

from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from .GraphQL import GraphQl
from .Predict import Predict


class BurbnBot:
    dc = {}
    logPath = "log/"
    username = ""
    driver = ""
    graphql = GraphQl()
    instabot = None
    settings = {}

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

        self.logging = logging.getLogger()

        try:
            self.logging.info("Lets do it!.")

            os.environ.setdefault(key="ANDROID_HOME", value=self.settings['android']['android_home'])

            self.logging.info("Starting Appium service.")
            self.appiumservice = AppiumService()
            self.appiumservice.stop()
            self.appiumservice.start()

            if self.appiumservice.is_running:
                self.logging.info("Appium Server is running.")
                self.driver = webdriver.Remote(
                    command_executor="http://localhost:4723/wd/hub",
                    desired_capabilities=self.settings['desired_caps']
                )
                self.logging.info("Connected with Appium Server.")
                self.driver.switch_to.context("NATIVE_APP")

                self.actions = TouchAction(self.driver)

                self.predict = Predict(api_key=self.settings['clarifai']['api_key'])

                # self.instabot = instabot.Bot(base_path="InstaBot/")

        except Exception as err:
            self.do_exception(err)
            self.end()
            pass

    def do_exception(self, err):
        self.logging.error(err)

    def end(self):
        self.appiumservice.stop()
        self.logging.info("That's all folks! Bye bye!")
        quit()

    def check_element_exist(self, id):
        try:
            self.driver.find_element_by_id(id)
        except NoSuchElementException:
            return False
        return True

    def search_hashtag(self, hashtag):
        hashtag = hashtag.replace('#', '').lower()
        self.logging.info("Searching for hashtag: {}.".format(hashtag))
        self.graphql.tags(tag=hashtag)
        self.driver.switch_to.context("NATIVE_APP")
        self.driver.find_element_by_accessibility_id("Search and Explore").click()
        self.driver.find_element_by_id('action_bar_search_edit_text').click()
        self.driver.find_element_by_xpath(xpath="//*[@text='TAGS']").click()
        self.driver.find_element_by_id('action_bar_search_edit_text').send_keys('#{}'.format(hashtag))
        WebDriverWait(self.driver, 30).until(expected_conditions.presence_of_element_located(
            (By.XPATH, "//*[@resource-id='com.instagram.android:id/row_hashtag_textview_tag_name']")))
        try:
            rows_result = self.driver.find_elements_by_xpath(
                xpath="//*[@resource-id='com.instagram.android:id/row_hashtag_textview_tag_name']")
        except Exception as err:
            return False
            pass
        else:
            sleep(3)
            self.logging.info("Hashtag {} founded, opening now.".format(hashtag))
            rows_result[0].click()
            sleep(3)
            return True

    def hashtag_interact(self, amount: int = 15, hashtag: str = None, aba: str = "top", stories: bool = False):
        if self.search_hashtag(hashtag=hashtag):
            try:
                self.driver.find_element_by_xpath(xpath="//*[@text='{}']".format(aba.upper())).click()
            except Exception as err:
                self.logging.info("No 'Top' or 'Recent' for hashtag {}, check this champs.".format(hashtag))
                pass
            if stories:
                try:
                    self.driver.find_element_by_id("hashtag_feed_header_container").find_element_by_id(
                        "branding_badge").click()
                    self.watch_stories(home=False)
                except Exception as err:
                    self.logging.info("No Stories for hashtag {}, sorry.".format(hashtag))
                    pass
            n = 1
            while n <= amount:
                for i in self.graphql.tags(tag=hashtag, aba=aba):
                    p = "https://www.instagram.com/p/{}/".format(i['node']['shortcode'])
                    post_info = self.graphql.post_info(url=p)
                    self.driver.get(url=p)
                    self.logging.info("Checking post {}.".format(p))
                    if not post_info['is_ad']:
                        if self.predict.check(self.logging, url=post_info['media_url'],
                                              tags=self.settings['clarifai']['concepts'],
                                              tags_skip=self.settings['clarifai']['concepts_skip'],
                                              is_video=post_info['is_video']):
                            self.like()

                    self.driver.back()
                    sleep(random.randint(2, 5))
                    n += 1
                    if n % 9:
                        self.driver.swipe(
                            start_x=random.randint(50, 1000), start_y=random.randint(1700, 1900),
                            end_x=random.randint(50, 1000), end_y=random.randint(900, 1000),
                            duration=random.randint(500, 900)
                        )

    def like(self):
        try:
            WebDriverWait(self.driver, 10).until(expected_conditions.presence_of_element_located(
                (By.XPATH, "//*[@resource-id='com.instagram.android:id/row_feed_button_like']")))
            e = self.driver.find_element_by_xpath("//*[@resource-id='com.instagram.android:id/row_feed_button_like']")
            if e.tag_name == "Liked":
                self.logging.info("Ops, you already like this one, sorry.")
            else:
                e.click()
                sleep(random.randint(1, 3))
                self.logging.info("Image Liked.")
        except Exception as err:
            self.logging.info("Ops, something wrong on like, sorry.")
            self.logging.error(err)
            pass

    def like_double_tap(self):
        try:
            try:
                e = self.driver.find_element_by_id("zoomable_view_container")
            except Exception as e:
                e = self.driver.find_element_by_id("carousel_media_group")
                pass
            self.driver.tap(
                positions=[(e.rect["width"] / 2, e.rect["height"] / 2), (e.rect["width"] / 2, e.rect["height"] / 2)],
                duration=1)
            sleep(3)
            breakpoint()
        except Exception as err:
            self.logging.info("Ops, something wrong, sorry.")
            self.logging.error(err)
            pass

    def watch_stories(self, home: bool = True):
        try:
            while self.check_element_exist(id="reel_viewer_texture_view"):
                t = random.randint(5, 15)
                self.logging.info("Sleeping for {} seconds.".format(t))
                sleep(t)
                if self.check_element_exist(id="reel_viewer_texture_view"):
                    self.logging.info("Tap")
                    self.driver.tap([(800, 600)], random.randint(3, 10))
        except Exception as err:
            self.logging.info("Ops, something wrong while waching stories, sorry.")
            self.logging.error(err)
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
                n = int(self.driver.find_element_by_id("carousel_bumping_text_indicator").text.split('/')[1])
            except Exception as err:
                n = 2  # if don't find the number of pictures work with only 2
                pass
            self.logging.info("Let's check all the {} images here.".format(n))
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
        self.logging.info('Watching video for {} seconds.'.format(t))
        sleep(t)

    def get_type_post(self):
        r = "photo"
        if self.check_element_exist(id="com.instagram.android:id/carousel_page_indicator"):
            r = "carousel"
        elif self.check_element_exist("com.instagram.android:id/progress_bar"):
            r = "video"

        return r
