import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or "dev_secret_key_change_me"