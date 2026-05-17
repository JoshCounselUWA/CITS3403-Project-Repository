#this is the unit test file for inventory related methods

import unittest
from App.Backend.models import Inventory, Department
from Tests.__init__ import create_test_db

class TestInventoryModel(unittest.TestCase):

    def setUp(self):
        self.session = create_test_db()

    def tearDown(self):
        self.session.close()

    #just the basic add method 
    def test_create_inventory_item(self):
        item = Inventory(
            itemName="Laptop",
            itemDescription="A test laptop",
            itemquantity=10,
            itemphoto=None,
            departmentID=None
        )

        self.session.add(item)
        self.session.commit()

        saved = self.session.query(Inventory).first()
        self.assertEqual(saved.itemName, "Laptop")
        self.assertEqual(saved.itemquantity, 10)

    #checking the update method
    def test_update_inventory_quantity(self):
        item = Inventory(
            itemName="Mouse",
            itemDescription="Test mouse",
            itemquantity=5
        )
        self.session.add(item)
        self.session.commit()
        #changing the quantity of the item
        item.itemquantity = 12
        self.session.commit()

        saved = self.session.query(Inventory).first()
        self.assertEqual(saved.itemquantity, 12)

    #checking the delete method
    def test_delete_inventory_item(self):
        item = Inventory(
            itemName="Keyboard",
            itemDescription="Test keyboard",
            itemquantity=3
        )
        self.session.add(item)
        self.session.commit()
        #delete after the added item
        self.session.delete(item)
        self.session.commit()

        remaining = self.session.query(Inventory).all()
        self.assertEqual(len(remaining), 0)

    def test_inventory_department_relationship(self):
        dept = Department(departmentName="IT")
        self.session.add(dept)
        self.session.commit()

        item = Inventory(
            itemName="Monitor",
            itemDescription="Test monitor",
            itemquantity=2,
            departmentID=dept.departmentID
        )
        self.session.add(item)
        self.session.commit()

        saved = self.session.query(Inventory).first()
        self.assertEqual(saved.department.departmentName, "IT")
