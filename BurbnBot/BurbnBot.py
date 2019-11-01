# This sample code uses the Appium python client
# pip install Appium-Python-Client
# Then you can paste this into a file and simply run with Python
import random
from time import sleep

from appium import webdriver
from appium.webdriver.common.touch_action import TouchAction


class BurbnBot:
    def __init__(self, configfile: str = None):
        caps = {
            "platformName": "Android",
            "deviceName": "Pixel_3a_API_29"
        }

        self.driver = webdriver.Remote("http://localhost:4723/wd/hub", caps)
        self.driver.start_session(caps)

        if self.driver.is_app_installed("com.instagram.android"):
            self.driver.implicitly_wait(30)
            # breakpoint()
            self.driver.terminate_app('com.instagram.android')
            # self.driver.long_press_keycode(10)
            self.driver.find_element_by_accessibility_id("Instagram").click()

    def test(self):
        self.driver.implicitly_wait(30)
        el1 = self.driver.find_element_by_accessibility_id("Search and Explore")
        el1.click()
        el2 = self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text")
        el2.click()
        el3 = self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text")
        el3.send_keys("@bruluccas")
        el4 = self.driver.find_element_by_xpath(
            "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/androidx.viewpager.widget.ViewPager/android.widget.FrameLayout/android.widget.ListView/android.widget.FrameLayout[1]/android.widget.LinearLayout")
        el4.click()
        el5 = self.driver.find_element_by_accessibility_id("Photo by Bru at Row 1, Column 1")
        el5.click()

    def wait(self, limit: float = 5):
        sleep(random.uniform(2, limit))

    def swipe_right_left(self):
        TouchAction(self.driver).press(x=1030, y=500).move_to(x=30, y=500).release().perform()

    def swipe_left_right(self):
        TouchAction(self.driver).press(x=30, y=500).move_to(x=1030, y=500).release().perform()

    def do_hashtag(self, hashtag: str = None, top_posts: bool = False):
        self.wait(3)

        breakpoint()

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
        press_x = random.randint(rect['x']+10, rect['width']-10)
        press_y = rect['height']-random.randint(5, 10)
        move_to_x = random.randint(2, 5)
        move_to_y = random.randint(2, 5)
        TouchAction(self.driver).press(x=press_x, y=press_y).move_to(x=move_to_x, y=move_to_y).release().perform()
        breakpoint()

    def do_feed(self):
        breakpoint()
