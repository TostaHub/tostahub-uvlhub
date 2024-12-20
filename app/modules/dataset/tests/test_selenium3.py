
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver
# import pytest
from selenium.webdriver.common.by import By  # type: ignore


class TestTestrate():
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.vars = {}

        self.driver.get(get_host_for_selenium_testing())

    def teardown_method(self, method):
        self.driver.quit()

    def test_testrate(self):
        self.driver.get("http://localhost:5000/")
        self.driver.set_window_size(1850, 1053)
        self.driver.find_element(By.LINK_TEXT, "Title").click()
        self.driver.find_element(By.CSS_SELECTOR, ".nav-link:nth-child(1)").click()
        self.driver.find_element(By.CSS_SELECTOR, ".row:nth-child(2) > .col-md-6 > .mb-3").click()
        self.driver.find_element(By.ID, "email").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.LINK_TEXT, "Title").click()
        self.driver.find_element(By.CSS_SELECTOR, "span:nth-child(5)").click()
        self.driver.find_element(By.CSS_SELECTOR, "div:nth-child(1) > button").click()
