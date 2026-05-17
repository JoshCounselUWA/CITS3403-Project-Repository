#This is a unit test file for request and requestItems related methods

import unittest
from App.Backend.models import (Account, Request, RequestItems, Inventory, Status)
from Tests.__init__ import create_test_db

class TestRequestModel(unittest.TestCase):

    def setUp(self):
        self.session = create_test_db()

        #create a requester account
        self.user = Account(
            fName="John",
            lName="Doe",
            userName="johndoe",
            password_hash="hashed",
            accountType="user"
        )
        self.session.add(self.user)
        self.session.commit()

    def tearDown(self):
        self.session.close()

    def test_create_request(self):
        req = Request(
            requestTitle="Borrow Laptop",
            requestJustification="For event",
            requesterID=self.user.userID,
            status=Status.waiting
        )

        self.session.add(req)
        self.session.commit()

        saved = self.session.query(Request).first()
        self.assertEqual(saved.requestTitle, "Borrow Laptop")
        self.assertEqual(saved.status, Status.waiting)
        self.assertEqual(saved.requesterID, self.user.userID)

    def test_add_items_to_request(self):
        #create inventory items
        item1 = Inventory(itemName="Laptop", itemquantity=10)
        item2 = Inventory(itemName="Mouse", itemquantity=20)
        self.session.add_all([item1, item2])
        self.session.commit()

        #create request
        req = Request(
            requestTitle="Event Equipment",
            requesterID=self.user.userID
        )
        self.session.add(req)
        self.session.commit()

        #add items
        ri1 = RequestItems(requestID=req.requestID, itemID=item1.itemID, quantity=2)
        ri2 = RequestItems(requestID=req.requestID, itemID=item2.itemID, quantity=5)

        self.session.add_all([ri1, ri2])
        self.session.commit()

        saved_items = self.session.query(RequestItems).filter_by(requestID=req.requestID).all()
        self.assertEqual(len(saved_items), 2)
        self.assertEqual(saved_items[0].quantity, 2)
        self.assertEqual(saved_items[1].quantity, 5)

    def test_request_item_relationship(self):
        item = Inventory(itemName="Projector", itemquantity=3)
        self.session.add(item)
        self.session.commit()

        req = Request(
            requestTitle="Borrow Projector",
            requesterID=self.user.userID
        )
        self.session.add(req)
        self.session.commit()

        ri = RequestItems(requestID=req.requestID, itemID=item.itemID, quantity=1)
        self.session.add(ri)
        self.session.commit()

        saved = self.session.query(RequestItems).first()
        self.assertEqual(saved.inventory.itemName, "Projector")
        self.assertEqual(saved.request.requesterID, self.user.userID)