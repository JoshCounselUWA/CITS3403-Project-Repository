#This is a file for log-in unit tests
import unittest
from unittest.mock import patch
from werkzeug.security import generate_password_hash

from Tests.__init__ import create_test_app, create_test_db
from App.Backend.main import app as real_app
from App.Backend.models import Account


class LoginTests(unittest.TestCase):

    def setUp(self):
        # Use the real app with real routes
        from App.Backend.main import app as real_app
        self.app = real_app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        # Create isolated test mock DB session
        self.test_session = create_test_db()

        # Use the mock DB instead
        patcher = patch('App.Backend.main.session', self.test_session)
        self.addCleanup(patcher.stop)
        patcher.start()

        # Insert a user into the mock DB
        user = Account(
            userName='unituser',
            password_hash=generate_password_hash('password123'),
            accountType='business_admin'
        )
        self.test_session.add(user)
        self.test_session.commit()
    # normal login
    def test_login_success(self):
        response = self.client.post('/login', data={
            'username': 'unituser',
            'password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
    # wrong password
    def test_login_invalid_password(self):
        response = self.client.post('/login', data={
            'username': 'unituser',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        self.assertIn(b'Invalid password', response.data)
    # wrong username
    def test_login_invalid_username(self):
        response = self.client.post('/login', data={
            'username': 'fakeuser',
            'password': 'password123'
        }, follow_redirects=True)

        self.assertIn(b'Invalid username', response.data)
