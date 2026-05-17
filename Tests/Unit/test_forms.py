import unittest
from flask import Flask
from App.Backend.forms import LoginForm, RegistrationForm

class FormTests(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "test"
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    # LoginForm Tests

    #normal login
    def test_login_form_valid(self):
        form = LoginForm(data={
            "username": "unituser",
            "password": "password123"
        })
        self.assertTrue(form.validate())

    #if there's a missing username
    def test_login_form_missing_username(self):
        form = LoginForm(data={
            "username": "",
            "password": "password123"
        })
        self.assertFalse(form.validate())

    #if there's a missing password
    def test_login_form_missing_password(self):
        form = LoginForm(data={
            "username": "unituser",
            "password": ""
        })
        self.assertFalse(form.validate())

    # RegistrationForm Tests

    #normal sign up
    def test_register_form_valid(self):
        form = RegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "password": "secret123",
            "confirm_password": "secret123"
        })
        self.assertTrue(form.validate())

    #if anything went missing
    def test_register_form_missing_fields(self):
        form = RegistrationForm(data={
            "first_name": "",
            "last_name": "",
            "username": "",
            "password": "",
            "confirm_password": ""
        })
        self.assertFalse(form.validate())

    #the confirm password with the wrong password
    def test_register_form_password_mismatch(self):
        form = RegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "password": "secret123",
            "confirm_password": "different"
        })
        self.assertFalse(form.validate())
        self.assertIn("Passwords must match", form.confirm_password.errors)

    #with the right password
    def test_register_form_password_match(self):
        form = RegistrationForm(data={
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "password": "secret123",
            "confirm_password": "secret123"
        })
        self.assertTrue(form.validate())

    #when the username is too long
    def test_register_form_password_mismatch(self):
        form = RegistrationForm(data={
            "first_name": "it",
            "last_name": "s",
            "username": "itsoverninethousandsssssssssssss",
            "password": "secret123",
            "confirm_password": "secret123"
        })
        self.assertFalse(form.validate())

if __name__ == "__main__":
    unittest.main()