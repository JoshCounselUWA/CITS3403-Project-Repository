#This is for providing tables for inventory, requests and login

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class Inventory(Base):
    __tablename__ = 'inventory'
    itemID = Column(Integer, primary_key=True) #primary
    itemName = Column(String, nullable=False)
    itemDescription = Column(String) #optional?
    itemquantity = Column(Integer, default=0)
    itemphoto = Column(String) #optional I guess, for url or file path of course

    departmentID = Column(Integer, ForeignKey('Department.departmentID'))

    def to_json(self):
        return {
            "itemID": self.itemID,
            "itemName": self.itemName,
            "itemDescription": self.itemDescription,
            "itemquantity": self.itemquantity,
            "itemphoto": self.itemphoto
        }

    def __repr__(self):
        return f"<Inventory(itemName={self.itemName},quantity={self.itemquantity})>"
    
class Status(enum.Enum):
    approved = "Approved"
    rejected = "Rejected"
    waiting = "Waiting"
    returned = "Returned"
    loaned = "Loaned"

class Request(Base):
    __tablename__ = 'requests'
    requestID = Column(Integer, primary_key=True) #primary
    requestTitle = Column(String, nullable=False)
    status = Column(Enum(Status), default=Status.waiting, nullable=False)
    requestJustification = Column(String)

    eventDateStart = Column(DateTime)
    eventDateEnd = Column(DateTime)
    returnDate = Column(DateTime)

    overdue = Column(Boolean, default=False)
    requesterID = Column(Integer, ForeignKey('Account.userID'), nullable=False) #foreign user
    approverID = Column(Integer, ForeignKey('Account.userID')) #foreign user department head

    departmentID = Column(Integer, ForeignKey('Department.departmentID'))

    items = relationship("RequestItems", back_populates="request", cascade="all, delete-orphan")

    def to_json(self):
        return {
            "requestID": self.requestID,
            "requestTitle": self.requestTitle,
            "status": self.status,
            "requestJustification": self.requestJustification,
            "eventDateStart": self.eventDateStart,
            "eventDateEnd": self.eventDateEnd,
            "returnDate": self.returnDate,
            "overdue": self.overdue,
            "requesterID": self.requesterID,
            "approverID": self.approverID
        }

    def __repr__(self):
        return f"<Request(title={self.requestTitle}, status={self.status})>"

class RequestItems(Base):
    __tablename__ = 'RequestItems'
    id = Column(Integer, primary_key=True)
    requestID = Column(Integer, ForeignKey('requests.requestID'), nullable=False)
    itemID = Column(Integer, ForeignKey('inventory.itemID'), nullable=False)
    quantity = Column(Integer, default=1)

    request = relationship("Request", back_populates="items")
    inventory = relationship("Inventory")

    def to_json(self):
        return {
            "id": self.id,
            "requestID": self.requestID,
            "itemID": self.itemID,
            "quantity": self.quantity
        }

    def __repr__(self):
        return f"<RequestItems(requestID={self.requestID}, itemID={self.itemID}, qty={self.quantity})>"

class ItemList(Base):
    __tablename__ = 'ItemList'
    itemID = Column(Integer, primary_key=True)
    itemName = Column(String)

    def to_json(self):
        return{
            "itemID": self.itemID,
            "itemName": self.itemName
        }

    def __repr__(self):
        return f"<ItemList(itemID={self.itemID},itemName={self.itemName})>"

#class Appsettings(Base):
    #__tablename__ = 'Appsettings'

    #def to_json(self):

    #def __repr__(self):

#class UserSettings(Base):
   # __tablename__ = 'usersettings'
    #userID = Column(Integer, primary_key=True)

    #def to_json(self):

    #def __repr__(self):

class Account(Base):
    __tablename__ = 'Account'
    fName = Column(String)
    lName = Column(String)
    userID = Column(Integer, primary_key=True)
    userName = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) 
    accountType = Column(String,nullable=False)

    departmentID = Column(Integer, ForeignKey('Department.departmentID'))

    def to_json(self):
        return{
            "fName": self.fName,
            "lName": self.lName,
            "userID": self.userID,
            "userName": self.userName,
            "password_hash": self.password_hash,
            "accountType": self.accountType
        }

    def __repr__(self):
        return f"<Account(userId={self.userID})>"
    
class Department(Base):
    __tablename__ = 'Department'
    departmentID = Column(Integer, primary_key=True)
    departmentName = Column(String)

    def to_json(self):
        return {
            "departmentID": self.departmentID,
            "departmentName": self.departmentName
        }
    
    def __repr__(self):
        return f"<Department(departmentID={self.departmentID})>"

engine = create_engine('sqlite:///DICEapp.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()