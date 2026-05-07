#This is for providing tables for inventory, requests and login

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Enum, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
from flask_login import UserMixin

Base = declarative_base()

class Inventory(Base):
    __tablename__ = 'inventory'
    itemID = Column(Integer, primary_key=True) #primary
    itemName = Column(String, nullable=False)
    itemDescription = Column(String) #optional?
    itemquantity = Column(Integer, default=0)
    itemphoto = Column(String) #optional I guess, for url or file path of course

    departmentID = Column(Integer, ForeignKey('Department.departmentID'))
    department = relationship("Department",back_populates='inventory')
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

class MembershipRole(enum.Enum):
    admin = "admin"
    member = "member"

class MembershipStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

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
    requester = relationship("Account", foreign_keys=[requesterID], back_populates="requests_made")
    approver = relationship("Account", foreign_keys=[approverID], back_populates="requests_reviewed")

    departmentID = Column(Integer, ForeignKey('Department.departmentID'))
    department = relationship("Department", back_populates="requests")

    items = relationship("RequestItems", back_populates="request", cascade="all, delete-orphan")

    def to_json(self):
        return {
            "requestID": self.requestID,
            "requestTitle": self.requestTitle,
            "status": self.status.value,
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

class Account(UserMixin, Base):
    __tablename__ = 'Account'
    fName = Column(String)
    lName = Column(String)
    userID = Column(Integer, primary_key=True)
    userName = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False) 

    # departmentID = Column(Integer, ForeignKey('Department.departmentID'))
    # department = relationship("Department", back_populates="accounts")
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")

    requests_made = relationship(
        "Request",
        foreign_keys="Request.requesterID",
        back_populates="requester"
    )
    requests_reviewed = relationship(
        "Request",
        foreign_keys="Request.approverID",
        back_populates="approver"
    )

    def to_json(self):
        return{
            "fName": self.fName,
            "lName": self.lName,
            "userID": self.userID,
            "userName": self.userName,
        }
    
    def get_id(self):
        return str(self.userID)
    
    def is_admin_of(self, depID):
        for m in self.memberships:
            if (m.departmentID == depID and m.role == MembershipRole.admin and m.status == MembershipStatus.accepted):
                return True
        return False
    
    def is_member_of(self, depID):
        for m in self.memberships:
            if (m.departmentID == depID and m.status == MembershipStatus.accepted):
                return True
        return False
    
    def active_departments(self):
        return [m.department for m in self.memberships
            if m.status == MembershipStatus.accepted]
                
    def __repr__(self):
        return f"<Account(userId={self.userID})>"
    
class Membership(Base):
    __tablename__ = 'Membership'
    id = Column(Integer, primary_key=True)
    userID = Column(Integer, ForeignKey(Account.userID), nullable=False)
    departmentID = Column(Integer, ForeignKey('Department.departmentID'), nullable=False)
    role = Column(Enum(MembershipRole), nullable=False)
    status = Column(Enum(MembershipStatus), nullable=False, default=MembershipStatus.pending)
    createdAt = Column(DateTime, default=datetime.utcnow)

    user = relationship("Account", back_populates="memberships")
    department = relationship("Department", back_populates="memberships")

    __table_args__ = (UniqueConstraint('userID', 'departmentID'),)

    def to_json(self):
        return {
            "id" : self.id,
            "userID" : self.userID,
            "departmentID" : self.departmentID,
            "role" : self.role.value,
            "status" : self.status.value
        }
    
    def __repr__(self):
        return f"<Membership(user={self.userID}, dept={self.departmentID}, role={self.role}, status={self.status})>"
    
class Department(Base):
    __tablename__ = 'Department'
    departmentID = Column(Integer, primary_key=True)
    departmentName = Column(String)

    inventory = relationship("Inventory", back_populates="department")
    # accounts = relationship("Account", back_populates="department")
    requests = relationship("Request", back_populates="department")
    memberships = relationship("Membership", back_populates="department", cascade="all, delete-orphan")

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
