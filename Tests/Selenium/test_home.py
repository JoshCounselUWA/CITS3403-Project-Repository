import unittest
import multiprocessing
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By


TEST_DB = "Tests/Selenium/test_database.db"

#Flasj runner
def run_flask():
    os.environ["TEST_DB_PATH"] = TEST_DB
    from App.Backend.main import app
    app.run(port=5000, use_reloader=False)


class TestHomePageSelenium(unittest.TestCase):

    def setUp(self):
        # Reset test DB
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                pass

        # Start Flask server
        self.server = multiprocessing.Process(target=run_flask)
        self.server.start()
        time.sleep(1.5)

        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()
        self.server.terminate()
        self.server.join()

    def test_homepage_loads(self):
        self.driver.get("http://localhost:5000/")
        self.assertIn("DICE", self.driver.title)

        hero_text = self.driver.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Inventory management", hero_text)

    def test_nav_login_button(self):
        self.driver.get("http://localhost:5000/")
        login_btn = self.driver.find_element(By.LINK_TEXT, "Log In")
        login_btn.click()

        self.assertIn("/login", self.driver.current_url)

    def test_nav_register_button(self):
        self.driver.get("http://localhost:5000/")
        register_btn = self.driver.find_element(By.LINK_TEXT, "Get Started")
        register_btn.click()

        self.assertIn("/register", self.driver.current_url)

    def test_hero_cta(self):
        self.driver.get("http://localhost:5000/")
        cta_btn = self.driver.find_element(By.XPATH, "//a[contains(text(),'Create Your Account')]")
        cta_btn.click()

        self.assertIn("/register", self.driver.current_url)

    def test_pricing_buttons(self):
        self.driver.get("http://localhost:5000/")

        # Starter plan button
        starter_btn = self.driver.find_element(By.XPATH, "//div[h3='Starter']//a")
        starter_btn.click()
        self.assertIn("/register", self.driver.current_url)

        # Go back to homepage
        self.driver.get("http://localhost:5000/")

        # Team plan button
        team_btn = self.driver.find_element(By.XPATH, "//div[h3='Team']//a")
        team_btn.click()
        self.assertIn("/register", self.driver.current_url)

    def test_contact_link(self):
        self.driver.get("http://localhost:5000/")

        contact_link = self.driver.find_element(By.LINK_TEXT, "Contact Us")
        contact_link.click()

        self.assertIn("#contact", self.driver.current_url)
