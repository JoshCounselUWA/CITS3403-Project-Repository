#This is a file for Account related methods unit tests
import unittest
from Tests.__init__ import create_test_db
from App.Backend.models import (Account, Department, Membership, MembershipRole, MembershipStatus)
from werkzeug.security import generate_password_hash


class AccountTests(unittest.TestCase):

    def setUp(self):
        #create isolated in-memory DB
        self.session = create_test_db()
    
    def test_account_creation(self):
        #creating account
        user = Account(
            fName="John",
            lName="Doe",
            userName="johndoe",
            password_hash=generate_password_hash("secret"),
            accountType="business_admin"
        )

        self.session.add(user)
        self.session.commit()

        saved = self.session.query(Account).filter_by(userName="johndoe").first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.fName, "John")
        self.assertEqual(saved.accountType, "business_admin")

    def test_department_and_membership(self):
        #create user account + department
        user = Account(
            userName="unituser",
            password_hash=generate_password_hash("pw"),
            accountType="user"
        )
        dept = Department(departmentName="IT")

        self.session.add_all([user, dept])
        self.session.commit()

        #add membership
        membership = Membership(
            userID=user.userID,
            departmentID=dept.departmentID,
            role=MembershipRole.admin,
            status=MembershipStatus.accepted
        )
        self.session.add(membership)
        self.session.commit()

        #test helper method
        self.assertTrue(user.is_admin_of(dept.departmentID))
        self.assertTrue(user.is_member_of(dept.departmentID))

if __name__ == "__main__":
    unittest.main()
