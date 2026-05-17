import unittest
import multiprocessing
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By


TEST_DB = "Tests/Selenium/test_database.db"

# Flask runner
def run_flask():
    os.environ["TEST_DB_PATH"] = TEST_DB
    from App.Backend.main import app
    app.run(port=5000, use_reloader=False)


class TestLoginSelenium(unittest.TestCase):

    def setUp(self):
        # Reset test DB and keep clean
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                pass

        # Start Flask
        self.server = multiprocessing.Process(target=run_flask)
        self.server.start()
        time.sleep(1.5)

        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()
        self.server.terminate()
        self.server.join()

    def test_login_success(self):
        self.driver.get("http://localhost:5000/login")

        self.driver.find_element(By.ID, "username").send_keys("testuser")
        self.driver.find_element(By.ID, "password").send_keys("password123")
        self.driver.find_element(By.ID, "submit").click()

        self.assertIn("/dashboard", self.driver.current_url)

    def test_login_invalid_username(self):
        self.driver.get("http://localhost:5000/login")

        self.driver.find_element(By.ID, "username").send_keys("wronguser")
        self.driver.find_element(By.ID, "password").send_keys("password123")
        self.driver.find_element(By.ID, "submit").click()

        flash = self.driver.find_element(By.CLASS_NAME, "flash-messages").text
        self.assertIn("Invalid username", flash)

    def test_login_invalid_password(self):
        self.driver.get("http://localhost:5000/login")

        self.driver.find_element(By.ID, "username").send_keys("testuser")
        self.driver.find_element(By.ID, "password").send_keys("wrongpass")
        self.driver.find_element(By.ID, "submit").click()

        flash = self.driver.find_element(By.CLASS_NAME, "flash-messages").text
        self.assertIn("Invalid password", flash)
