import argparse
import json
import logging
import os
import random
from time import sleep

from appium import webdriver
from appium.webdriver.appium_service import AppiumService
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class BurbnBot:
    dc = {}
    logPath = "log/"
    username = ""
    driver = ""

    def search_hashtag(self, hashtag):
        hashtag = hashtag.replace('#', '').lower()
        self.logging.info("Searching for hashtag: {}.".format(hashtag))
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

    def hashtag_interact(self, hashtag: str = None, aba: str = "top", stories: bool = False):
        self.driver.switch_to.context("NATIVE_APP")
        if self.search_hashtag(hashtag=hashtag):
            try:
                self.driver.find_element_by_xpath(xpath="//*[@text='{}']".format(aba.upper())).click()
            except Exception as err:
                self.logging.info("No 'Top' or 'Recent' for hashtag {}, check this champs.".format(hashtag))
                pass
            if stories:
                try:
                    self.driver.find_element_by_id("hashtag_feed_header_container").find_element_by_id(
                        "profile_image").click()
                    self.watch_stories(home=False)
                except Exception as err:
                    self.logging.info("No Stories for hashtag {}, sorry.".format(hashtag))
                    pass

            rows = self.driver.find_elements_by_xpath(xpath="//*[@class='android.widget.LinearLayout']")
            for row in rows:
                for p in row.find_elements_by_xpath("//*[@class='android.widget.ImageView']"):
                    p.click()
                    if self.get_type_post() == "carousel":
                        self.swipe_carousel()
                    elif self.get_type_post() == "video":
                        self.watch_video()
                    else:
                        self.logging.info("Only a picture, be nice.")

                    self.logging.info("Moving to next post.")
                    breakpoint()

                    self.driver.back()

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
            n = int(self.driver.find_element_by_xpath(
                "//*[@resource-id='com.instagram.android:id/carousel_bumping_text_indicator']").text.split('/')[1])
            self.logging.info("Let's check all the {} images here.".format(n))
            for x in range(n - 1):
                self.driver.swipe(800, 600, 250, 600, random.randint(1000, 1500))
            for x in range(n - 1):
                self.driver.swipe(300, 650, 800, 600, random.randint(1000, 1500))

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

    def __init__(self, configfile: str = None):
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-settings', type=str, help="json settings file")
        args = parser.parse_args()
        settings = json.load(open(args.settings))

        # self.dc['udid'] = 'emulator-5554'
        self.dc['appPackage'] = 'com.instagram.android'
        self.dc['isHeadless'] = 'false'
        self.dc['disableWindowAnimation'] = 'true'
        self.dc['appActivity'] = '.activity.MainTabActivity'
        self.dc['noReset'] = 'true'
        self.dc['platformName'] = 'android'
        self.dc['automationName'] = 'UiAutomator2'
        self.dc['deviceName'] = 'Dev'
        self.dc['autoGrantPermissions'] = 'true'
        self.dc['newCommandTimeout'] = '600'
        self.dc['androidDeviceReadyTimeout'] = '30'
        self.dc['avd'] = 'Dev'

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

            os.environ.setdefault(key="ANDROID_HOME", value=settings['commands']['android_home'])

            self.logging.info("Starting Appium service.")
            self.appiumservice = AppiumService()
            self.appiumservice.stop()
            self.appiumservice.start()

            if self.appiumservice.is_running:
                self.logging.info("Appium Server is running.")
                self.driver = webdriver.Remote('http://localhost:4723/wd/hub', self.dc)

                self.logging.info("Connected with Appium Server.")


        except Exception as err:
            self.do_exception(err)
            self.end()
            pass

    def do_exception(self, err):
        self.logging.error(err)

    def end(self):
        self.appiumservice.stop()
        # subprocess.Popen(shlex.split("adb -s emulator-5554 emu kill"))
        self.logging.info("That's all folks! Bye bye!")
        quit()

    def check_element_exist(self, id):
        try:
            self.driver.find_element_by_id(id)
        except NoSuchElementException:
            return False
        return True
