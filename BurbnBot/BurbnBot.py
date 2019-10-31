# This sample code uses the Appium python client
# pip install Appium-Python-Client
# Then you can paste this into a file and simply run with Python

from appium import webdriver

class BurbnBot:
    def __init__(self, configfile: str = None):
        caps = {
            "platformName": "Android",
            "deviceName": "Pixel_3a_API_29",
            "unicodeKeyboard": True,
            "resetKeyboard":  True
        }

        self.xpath_base = "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget." \
                          "FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget." \
                          "FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[2]/android.widget." \
                          "FrameLayout[1]/android.widget.FrameLayout"

        self.driver = webdriver.Remote("http://localhost:4723/wd/hub", caps)
        self.driver.start_session(caps)

        if self.driver.is_app_installed("com.instagram.android"):
            # breakpoint()
            self.driver.terminate_app('com.instagram.android')
            # self.driver.long_press_keycode(10)
            self.driver.find_element_by_accessibility_id("Instagram").click()
            # breakpoint()
            self.btnHome = self.driver.find_element_by_accessibility_id("Home")
            self.btnHome.click()

    def do_hashtag(self, hashtag: str = None, top_posts: bool = False):
        breakpoint()
        btnSearchExplore = self.driver.find_element_by_accessibility_id("Search and Explore")
        btnSearchExplore.click()

        btnSearchBar = self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text")
        btnSearchBar.click()
        btnSearchBar.send_keys("#halloween2019")

        list = self.driver.find_element_by_id("android:id/list").find_elements_by_class_name(name="android.widget.FrameLayout")

        list[0].click()

        self.driver.id
        breakpoint()

        # el2 = self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text")
        # el2.click()
        # el3 = self.driver.find_element_by_xpath(
        #     "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout[3]")
        # el3.click()
        # el4 = self.driver.find_element_by_id("com.instagram.android:id/action_bar_search_edit_text")
        # el4.send_keys(hashtag)
        # el4.click()
        # el5 = self.driver.find_element_by_xpath(
        #     "/hierarchy/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.LinearLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout/android.widget.FrameLayout[2]/android.widget.FrameLayout[1]/android.widget.FrameLayout/androidx.viewpager.widget.ViewPager/android.widget.FrameLayout/android.widget.ListView/android.widget.FrameLayout[1]")
        # el5.click()

