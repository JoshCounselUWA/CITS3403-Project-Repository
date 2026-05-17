import unittest
from App.Backend.main import app, session
from App.Backend.models import Account, Department, Request, RequestItems, Inventory, Status
from werkzeug.security import generate_password_hash

class TestRoutes(unittest.TestCase):

    def setUp(self):
        # disable CSRF for WTForms so login works
        app.config["WTF_CSRF_ENABLED"] = False

        # Flask test client
        self.client = app.test_client()

        # test admin acc
        self.admin = session.query(Account).filter_by(userName="testuser").first()
        if not self.admin:
            self.admin = Account(
                fName="Test",
                lName="User",
                userName="testuser",
                password_hash=generate_password_hash("password123"),
                accountType="business_admin"
            )
            session.add(self.admin)
            session.commit()

        # test normal acc
        self.normal_user = session.query(Account).filter_by(userName="normaluser").first()
        if not self.normal_user:
            self.normal_user = Account(
                fName="Normal",
                lName="User",
                userName="normaluser",
                password_hash=generate_password_hash("password123"),
                accountType="user"
            )
            session.add(self.normal_user)
            session.commit()

    def login_admin(self):
        return self.client.post("/login", data={
            "username": "testuser",
            "password": "password123",
            "remember_me": "y",
            "submit": "Login"
        }, follow_redirects=True)

    def login_normal(self):
        return self.client.post("/login", data={
            "username": "normaluser",
            "password": "password123",
            "remember_me": "y",
            "submit": "Login"
        }, follow_redirects=True)
    
    # routes
    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_dashboard_logged_in(self):
        self.login_admin()
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)

    def test_inventory_requires_login(self):
        response = self.client.get("/inventory")
        self.assertEqual(response.status_code, 302)

    def test_inventory_logged_in(self):
        self.login_admin()
        response = self.client.get("/inventory")
        self.assertEqual(response.status_code, 200)

    # app settings for admin
    # as normal
    def test_appsettings_requires_admin(self):
        self.login_normal()
        response = self.client.get("/appsettings")
        self.assertEqual(response.status_code, 403)
    # as admin
    def test_appsettings_admin(self):
        self.login_admin()
        response = self.client.get("/appsettings")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
