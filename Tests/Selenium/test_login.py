import unittest
import multiprocessing
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# Flask runner
def run_flask():
    from App.Backend.main import app
    app.run(port=5000, use_reloader=False)

class TestLoginSelenium(unittest.TestCase):

    def setUp(self):
        # Start Flask server
        self.server = multiprocessing.Process(target=run_flask)
        self.server.start()
        time.sleep(2)  # allow server to start

        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()
        self.server.terminate()
        self.server.join()

    def test_login_success(self):
        """Test valid login redirects to dashboard"""
        self.driver.get("http://localhost:5000/login")

        self.driver.find_element(By.ID, "username").send_keys("johndoe")
        self.driver.find_element(By.ID, "password").send_keys("secret123")

        self.driver.find_element(By.ID, "submit").click()

        # Adjust expected redirect if needed
        self.assertIn("/dashboard", self.driver.current_url)

    def test_login_failure(self):
        """Test invalid login shows error message"""
        self.driver.get("http://localhost:5000/login")

        self.driver.find_element(By.ID, "username").send_keys("wronguser")
        self.driver.find_element(By.ID, "password").send_keys("wrongpass")

        self.driver.find_element(By.ID, "submit").click()

        # Flash messages appear in <ul class="flash-messages">
        error_box = self.driver.find_element(By.CLASS_NAME, "flash-messages")
        self.assertTrue("Invalid" in error_box.text or "incorrect" in error_box.text)


if __name__ == "__main__":
    unittest.main()
