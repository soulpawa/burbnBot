# This sample code uses the Appium python client
# pip install Appium-Python-Client
# Then you can paste this into a file and simply run with Python

from appium import webdriver


class BurbnBot:
    def __init__(self, configfile: str = None):
        caps = {
            "platformName": "Android",
            "deviceName": "Pixel_3a_API_29"
        }


        self.driver = webdriver.Remote("http://localhost:4723/wd/hub", caps)
        self.driver.start_session(caps)

        if self.driver.is_app_installed("com.instagram.android"):
            breakpoint()
            self.driver.find_element_by_accessibility_id("Search").click()
            self.driver.find_element_by_id("com.google.android.googlequicksearchbox:id/search_box").send_keys("Instagram")
            self.driver.find_element_by_id("android:id/title").click()
            self.driver.find_element_by_accessibility_id("Home").click()
