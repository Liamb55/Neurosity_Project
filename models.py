from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, func, text

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.mapped_column(db.Integer, primary_key=True)
    username = db.mapped_column(db.String(50), unique=True)
    password = db.mapped_column(db.String(80))
    
    #ds_owned = db.mapped_column(db.Integer, db.ForeignKey('datasets.owner_id'), nullable=True)
    ds_owned = db.relationship('DatasetInfo',  backref=db.backref('owner', lazy=True))
    ds_subscribed = db.relationship('DatasetInfo', secondary='subscriptions', backref=db.backref('subscribers', lazy=True))
    
    def __init__(self, username, password):
        #NextFreeID = db.session.query(func.max(User.user_id)).scalar() + 1
        #self.user_id = NextFreeID

        self.username = username #+ str(NextFreeID)
        self.password = password

    def __repr__(self):
        return f"<User(username={self.username})>"
    
    def get_id(self):
        """A loader method for flask_login"""
        return str(self.user_id)
    

class DatasetInfo(db.Model):
    __tablename__ = 'datasets'
    ds_id = db.mapped_column(db.Integer, primary_key=True)
    name = db.mapped_column(db.String(50))
    owner_id = db.mapped_column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    owner_username = db.mapped_column(db.String(50))
    path = db.mapped_column(db.String(256))
    description = db.mapped_column(db.String(1024))
    comments = db.relationship('Comment',  backref=db.backref('owner_dataset', lazy=True))

    def __init__(self, name, owner_id, owner_username, path, desc):
        self.name = name
        self.owner_id = owner_id
        self.owner_username = owner_username
        self.path = path
        self.description = desc

    def __repr__(self):
        return f"<DatasetInfo(owner_username={self.owner_username})>"
        

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    user_id = db.mapped_column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    ds_id = db.mapped_column(db.Integer, db.ForeignKey('datasets.ds_id'), primary_key=True)
    
    def __init__(self, user_id, ds_id):
        self.user_id = user_id
        self.ds_id = ds_id


class Comment(db.Model):
    __tablename__ = 'comments'
    time_created = Column(DateTime(timezone=True), server_default=func.now(), primary_key=True)
    ds_id = db.mapped_column(db.Integer, db.ForeignKey('datasets.ds_id'), nullable=False)
    user_id = db.mapped_column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    username = db.mapped_column(db.String(50))
    commenttext = db.mapped_column(db.String(1024))
    
    
    def __init__(self, user_id, ds_id, username, commenttext):
        self.user_id = user_id
        self.ds_id = ds_id
        self.username = username
        self.commenttext = commenttext
    

    def __repr__(self):
        return f"<Comment(comment={self.commenttext})>"    