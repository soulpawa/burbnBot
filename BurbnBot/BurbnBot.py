# This sample code uses the Appium python client
# pip install Appium-Python-Client
# Then you can paste this into a file and simply run with Python
import argparse
import json
import os
import random
import re
import shlex
import subprocess
import sys

import pyperclip
import logging
from time import sleep

from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.touch_action import TouchAction

# from .elements_compile import element
# from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from BurbnBot.Predict import Predict


class BurbnBot:
    def __init__(self, configfile: str = None):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-settings', type=str, help="json settings file")
        args = parser.parse_args()

        settings = json.load(open(args.settings))
        self.username = settings['instagram']['username']
        self.logPath = "log/"

        self.predict = Predict(api_key=settings['clarifai']['api_key'])

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

            self.logging.info('Starting emulator...')
            subprocess.Popen(shlex.split(settings['commands']['emulator']))

            os.environ.setdefault(key="ANDROID_HOME", value=settings['commands']['android_home'])

            self.appiumservice = AppiumService()

            self.appiumservice.start()

            if self.appiumservice.is_running:
                caps = {
                    "platformName": "Android",
                    "deviceName": "Dev",
                    'automationName': 'UiAutomator2'
                }
                self.logging.info("Appium Server is running.")
                self.driver = webdriver.Remote(desired_capabilities=caps, command_executor="http://0.0.0.0:4723/wd/hub")
                self.logging.info("Connected with Appium Server.")
                # self.driver.start_session(caps)
                # self.logging.info(msg="Appium session started ID: {}".format(self.driver.session_id))
        except Exception as err:
            self.do_exception(err)
            self.end()
            pass

        if self.driver.is_app_installed("com.instagram.android"):
            self.logging.info("Instagram installed.")
            self.driver.terminate_app('com.instagram.android')
            self.driver.find_element_by_accessibility_id("Instagram").click()
            self.logging.info("Instagram starting.")

    def hashtag_interact(self, hashtag: str = None, top: bool = False, recent: bool = False):
        try:
            if self.search_hashtag(hashtag):
                if top:
                    self.driver.find_element_by_xpath(xpath='//android.widget.TextView[@content-desc="Top"]').click()
                if recent:
                    self.driver.find_element_by_xpath(xpath='//android.widget.TextView[@content-desc="Recent"]').click()

                header_list = self.driver.find_element_by_id("com.instagram.android:id/sticky_header_list")
                list_posts = header_list.find_element_by_id("android:id/list").find_elements_by_class_name(
                    "android.widget.ImageView")
                list_posts[0].click()
                self.check_post()
                breakpoint()
            else:
                self.logging.info("No results found for {}.".format(hashtag))

        except Exception as err:
            self.do_exception(err)
            pass

    def check_post(self):
        row_feed_photo_profile_name = self.driver.find_element_by_id(
            "com.instagram.android:id/row_feed_photo_profile_name")
        owner_username = row_feed_photo_profile_name.text.replace(" •", "")

        TouchAction(self.driver).press(x=row_feed_photo_profile_name.rect["x"],
                                       y=row_feed_photo_profile_name.rect["y"]).move_to(
            x=row_feed_photo_profile_name.rect["width"], y=10).release().perform()

        has_liked = self.driver.find_element_by_id("com.instagram.android:id/row_feed_button_like").tag_name == "Liked"

        if self.check_element_exist(id="com.instagram.android:id/carousel_page_indicator"):
            carousel_amount = int(
                self.driver.find_element_by_id("com.instagram.android:id/carousel_bumping_text_indicator").text.split(
                    '/')[1])
            is_carousel = True
            is_photo = False
            is_video = False
        elif self.check_element_exist("com.instagram.android:id/progress_bar"):
            is_carousel = True
            is_photo = False
            is_video = self.check_element_exist("com.instagram.android:id/progress_bar")
        else:
            is_carousel = False
            is_photo = True
            is_video = False

        # CLARIFAI INTEGRATION
        # screenshot_as_base64 = self.driver.find_element_by_xpath(xpath='//android.widget.FrameLayout[@content-desc="Image"]/android.widget.ImageView').screenshot_as_base64
        # screenshot_as_png = self.driver.find_element_by_xpath(xpath='//android.widget.FrameLayout[@content-desc="Image"]/android.widget.ImageView').screenshot_as_png
        breakpoint()
        # self.predict.get(base64_bytes=image_as_base64)

    def search_hashtag(self, hashtag):
        self.driver.find_element_by_accessibility_id("Search and Explore").click()
        self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text").click()
        tabs = self.driver.find_element_by_id(
            "com.instagram.android:id/fixed_tabbar_tabs_container").find_elements_by_class_name(
            "android.widget.FrameLayout")
        tabs[2].click()
        self.logging.info("Searching hashtag: {}.".format(hashtag))
        self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text").send_keys(hashtag)
        try:
            rows_result = self.driver.find_element_by_id("android:id/list").find_elements_by_id(
                "com.instagram.android:id/row_hashtag_container")
        except Exception as err:
            return False
            pass
        else:
            sleep(3)
            rows_result[0].click()
            sleep(3)
            return True

    def check_element_exist(self, id):
        try:
            self.driver.find_element_by_id(id)
        except NoSuchElementException:
            return False
        return True

    def wait(self, limit: float = 5):
        sleep(random.uniform(2, limit))

    def do_exception(self, err):
        self.logging.error(err)

    def end(self):
        self.appiumservice.stop()
        quit()
