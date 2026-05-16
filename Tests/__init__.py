#The factory method
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from App.Backend.models import Base

def create_test_app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    app.config['WTF_CSRF_ENABLED'] = False
    return app

def create_test_db():
    # Mock DB
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()
