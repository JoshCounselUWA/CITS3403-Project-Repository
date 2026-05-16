#This is a file for table classes unit tests
import unittest
from Tests.__init__ import create_test_db
from App.Backend.models import (
    Account, Department, Membership, MembershipRole, MembershipStatus,
    Inventory, Request, RequestItems, Status
)
from werkzeug.security import generate_password_hash


class ModelTests(unittest.TestCase):

    def setUp(self):
        # Create isolated in-memory DB
        self.session = create_test_db()
    
    def test_account_creation(self):
        #Creating account
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
        # Create user account + department
        user = Account(
            userName="unituser",
            password_hash=generate_password_hash("pw"),
            accountType="user"
        )
        dept = Department(departmentName="IT")

        self.session.add_all([user, dept])
        self.session.commit()

        # Add membership
        membership = Membership(
            userID=user.userID,
            departmentID=dept.departmentID,
            role=MembershipRole.admin,
            status=MembershipStatus.accepted
        )
        self.session.add(membership)
        self.session.commit()

        # Test helper method
        self.assertTrue(user.is_admin_of(dept.departmentID))
        self.assertTrue(user.is_member_of(dept.departmentID))

    def test_inventory_creation(self):
        # creating inventory
        dept = Department(departmentName="HR")
        item = Inventory(
            itemName="Laptop",
            itemDescription="Dell XPS",
            itemquantity=5,
            department=dept
        )

        self.session.add_all([dept, item])
        self.session.commit()

        saved = self.session.query(Inventory).first()
        self.assertEqual(saved.itemName, "Laptop")
        self.assertEqual(saved.department.departmentName, "HR")

    def test_request_and_request_items(self):
        # Create user acc+ dept + item
        user = Account(
            userName="unituser",
            password_hash=generate_password_hash("pw"),
            accountType="user"
        )
        dept = Department(departmentName="Finance")
        item = Inventory(itemName="Camera", itemquantity=3, department=dept)

        self.session.add_all([user, dept, item])
        self.session.commit()

        # Create request
        req = Request(
            requestTitle="Borrow Camera",
            requesterID=user.userID,
            departmentID=dept.departmentID,
            status=Status.waiting
        )
        self.session.add(req)
        self.session.commit()

        # Add request item
        req_item = RequestItems(
            requestID=req.requestID,
            itemID=item.itemID,
            quantity=2
        )
        self.session.add(req_item)
        self.session.commit()

        # Verify relationships
        saved_req = self.session.query(Request).first()
        self.assertEqual(len(saved_req.items), 1)
        self.assertEqual(saved_req.items[0].quantity, 2)

    def test_cascade_delete_request_items(self):
        # Create user acc + dept + item
        user = Account(
            userName="unituser",
            password_hash=generate_password_hash("pw"),
            accountType="user"
        )
        dept = Department(departmentName="Finance")
        item = Inventory(itemName="Camera", itemquantity=3, department=dept)

        self.session.add_all([user, dept, item])
        self.session.commit()

        # Create request + items
        req = Request(
            requestTitle="Borrow Camera",
            requesterID=user.userID,
            departmentID=dept.departmentID
        )
        self.session.add(req)
        self.session.commit()

        req_item = RequestItems(
            requestID=req.requestID,
            itemID=item.itemID,
            quantity=1
        )
        self.session.add(req_item)
        self.session.commit()

        # Delete request
        self.session.delete(req)
        self.session.commit()

        # RequestItems should be deleted automatically
        remaining = self.session.query(RequestItems).all()
        self.assertEqual(len(remaining), 0)


if __name__ == "__main__":
    unittest.main()
