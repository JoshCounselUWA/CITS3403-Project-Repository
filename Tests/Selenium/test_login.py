import unittest
import multiprocessing
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# Flask runner
def run_flask():
    from App.Backend.main import app
    app.run(port=5000, use_reloader=False)


class TestFormsSelenium(unittest.TestCase):

    def setUp(self):
        # Start Flask server
        self.server = multiprocessing.Process(target=run_flask)
        self.server.start()
        time.sleep(1)  # give server time to start
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()
        self.server.terminate()
        self.server.join()

    def test_register_password_match(self):
        self.driver.get("http://localhost:5000/register")

        self.driver.find_element(By.ID, "first_name").send_keys("John")
        self.driver.find_element(By.ID, "last_name").send_keys("Doe")
        self.driver.find_element(By.ID, "username").send_keys("johndoe")
        self.driver.find_element(By.ID, "password").send_keys("secret123")
        self.driver.find_element(By.ID, "confirm_password").send_keys("secret123")

        self.driver.find_element(By.ID, "submit").click()

        self.assertIn("/login", self.driver.current_url)


    def test_register_password_mismatch(self):
        self.driver.get("http://localhost:5000/register")

        self.driver.find_element(By.ID, "first_name").send_keys("John")
        self.driver.find_element(By.ID, "last_name").send_keys("Doe")
        self.driver.find_element(By.ID, "username").send_keys("johndoe")
        self.driver.find_element(By.ID, "password").send_keys("secret123")
        self.driver.find_element(By.ID, "confirm_password").send_keys("different")

        self.driver.find_element(By.ID, "submit").click()
    
        error = self.driver.find_element(By.ID, "confirm_password_error").text
        self.assertIn("Passwords must match", error)
