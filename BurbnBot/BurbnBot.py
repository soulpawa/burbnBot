# This sample code uses the Appium python client
# pip install Appium-Python-Client
# Then you can paste this into a file and simply run with Python
import argparse
import json
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
from selenium.webdriver.common.by import By




class BurbnBot:
    def __init__(self, configfile: str = None):
        caps = {
            "platformName": "Android",
            "deviceName": "Dev",
            'automationName': 'UiAutomator2'
        }

        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-settings', type=str, help="json settings file")
        args = parser.parse_args()

        settings = json.load(open(args.settings))
        self.username = settings['instagram']['username']
        self.logPath = "log/"
        self.appiumservice = AppiumService()

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
            # subprocess.Popen(shlex.split(settings['commands']['emulator']))
            # sleep(15)

            # self.appiumservice.start()

            self.driver = webdriver.Remote(desired_capabilities=caps, command_executor="http://127.0.0.1:4723/wd/hub")
            self.logging.info("Connected with Appium Server.")

            self.driver.start_session(caps)
            self.logging.info(msg="Appium session started ID: {}".format(self.driver.session_id))
        except Exception as err:
            self.do_exception(err)
            self.end()
            pass

        if self.driver.is_app_installed("com.instagram.android"):
            self.logging.info("Instagram installed.")
            self.driver.terminate_app('com.instagram.android')
            self.driver.find_element_by_accessibility_id("Instagram").click()
            self.logging.info("Instagram starting.")
            self.driver.implicitly_wait(time_to_wait=15)

    def test(self, profile):
        try:
            self.driver.find_element_by_xpath(
                xpath='//android.widget.FrameLayout[@content-desc="Search and Explore"]').click()
            self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text").click()
            self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text").send_keys(profile)

            self.driver.find_element_by_id("com.instagram.android:id/row_search_user_username").click()

            profile_viewpager = self.driver.find_element_by_class_name(name="androidx.recyclerview.widget.RecyclerView")
            breakpoint()
            list_posts = profile_viewpager.find_elements_by_class_name(name="android.widget.ImageView")

            list_posts[1]

        except Exception as err:
            self.do_exception(err)
            pass

    def wait(self, limit: float = 5):
        sleep(random.uniform(2, limit))

    def do_exception(self, err):
        breakpoint()
        self.logging.error(err)

    def swipe_right_left(self):
        TouchAction(self.driver).press(x=1030, y=500).move_to(x=30, y=500).release().perform()

    def swipe_left_right(self):
        TouchAction(self.driver).press(x=30, y=500).move_to(x=1030, y=500).release().perform()

    def check_post(self):
        breakpoint()
        has_liked = self.driver.find_element_by_id("com.instagram.android:id/row_feed_button_like").tag_name == "Liked"

        n_comments = re.sub('[^0-9]', '', self.driver.find_element_by_id(
            "com.instagram.android:id/row_feed_view_all_comments_text").text)

        media_caption = re.sub('[^0-9]', '', self.driver.find_element_by_id(
            "com.instagram.android:id/row_feed_view_all_comments_text").text)

        owner_username = self.driver.find_element_by_id("com.instagram.android:id/row_feed_photo_profile_name").text

        breakpoint()
        try:
            is_video = isinstance(
                self.driver.find_element_by_id("com.instagram.android:id/media_group").find_elements_by_class_name(
                    name="class android.widget.ProgressBar"), list)
        except Exception as err:
            is_video = False
            pass

        breakpoint()

    def like_by_tags(self, tags: list = None, amount: int = 50, skip_top_posts: bool = True):
        self.wait(3)

        self.logging.info("")

        self.driver.find_element_by_accessibility_id("Search and Explore").click()

        btn_search_bar = self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text")
        btn_search_bar.click()
        btn_search_bar.send_keys(hashtag)

        top_bar = self.driver.find_element_by_id(
            "com.instagram.android:id/fixed_tabbar_tabs_container").find_elements_by_class_name(
            "android.widget.FrameLayout")
        top_bar[2].click()

        breakpoint()

        # fix down
        for e in self.driver.find_element_by_id("android:id/list").find_elements_by_class_name(
                name="android.widget.FrameLayout"):
            e.click()

        self.do_feed()

    def scrool_down(self):
        rect = self.driver.find_element_by_id("com.instagram.android:id/layout_container_main").rect
        press_x = random.randint(rect['x'] + 10, rect['width'] - 10)
        press_y = rect['height'] - random.randint(5, 10)
        move_to_x = random.randint(2, 5)
        move_to_y = random.randint(2, 5)
        TouchAction(self.driver).press(x=press_x, y=press_y).move_to(x=move_to_x, y=move_to_y).release().perform()
        breakpoint()

    def get_info_post(self):
        options = self.driver.find_element_by_accessibility_id("Options")
        options.click()
        copy_link = self.driver.find_element_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.ListView/android.widget.FrameLayout[2]")
        copy_link.click()

        print(pyperclip.paste())

        breakpoint()

    def do_feed(self):
        breakpoint()

    def get_following(self):
        breakpoint()
        self.driver.find_element_by_accessibility_id("Profile").click()
        sleep(2)
        self.driver.find_element_by_accessibility_id("Profile").click()
        self.driver.find_element_by_id("com.instagram.android:id/row_profile_header_following_container").click()

    def end(self):
        self.appiumservice.stop()
        quit()
