import unittest
import multiprocessing
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By


TEST_DB = "Tests/Selenium/test_database.db"

# FLASK RUNNER
def run_flask():
    os.environ["TEST_DB_PATH"] = TEST_DB
    from App.Backend.main import app
    app.run(port=5000, use_reloader=False)


class TestFormsSelenium(unittest.TestCase):

    def setUp(self):
        # Ensure test DB is fresh BEFORE starting Flask
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
            except PermissionError:
                pass

        # start Flask server
        self.server = multiprocessing.Process(target=run_flask)
        self.server.start()

        time.sleep(1.5)

        self.driver = webdriver.Chrome()


    def tearDown(self):
        self.driver.quit()
        self.server.terminate()
        self.server.join()

    def test_register_password_match(self):
        self.driver.get("http://localhost:5000/register")

        self.driver.find_element(By.ID, "first_name").send_keys("John")
        self.driver.find_element(By.ID, "last_name").send_keys("Doe")

        username = f"user_match_{int(time.time())}"
        self.driver.find_element(By.ID, "username").send_keys(username)

        self.driver.find_element(By.ID, "password").send_keys("secret123")
        self.driver.find_element(By.ID, "confirm_password").send_keys("secret123")

        self.driver.find_element(By.ID, "submit").click()

        self.assertIn("/login", self.driver.current_url)


    def test_register_password_mismatch(self):
        self.driver.get("http://localhost:5000/register")

        self.driver.find_element(By.ID, "first_name").send_keys("John")
        self.driver.find_element(By.ID, "last_name").send_keys("Doe")

        username = f"user_mismatch_{int(time.time())}"
        self.driver.find_element(By.ID, "username").send_keys(username)

        self.driver.find_element(By.ID, "password").send_keys("secret123")
        self.driver.find_element(By.ID, "confirm_password").send_keys("different")

        self.driver.find_element(By.ID, "submit").click()

        error = self.driver.find_element(By.ID, "confirm_password_error").text
        self.assertIn("Passwords must match", error)
