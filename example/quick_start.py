#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/3/13
Desc    :   
"""
import datetime
import flask
from flask_sqlalchemy import SQLAlchemy
from rest_utils import APIManager

# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./test.db'
db = SQLAlchemy(app)

user_groups = db.Table(
    'user_groups', db.Model.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'))
)


class User(db.Model):
    """
    用户
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(32), unique=True)  # 用户名唯一
    email = db.Column(db.Unicode(128))
    phone = db.Column(db.CHAR(11))

    # 绑定一对一关系
    # 用户验证状态
    validation = db.relationship(
        'UserValidation',
        uselist=False,
        backref=db.backref('user')
    )

    # 绑定一对多关系
    # 用户文章列表
    posts = db.relationship(
        'Post',
        backref=db.backref('user')
    )

    # 使用 secondary 绑定多对多关系
    # 用户组列表
    groups = db.relationship(
        'Group',
        secondary=user_groups,
        backref=db.backref('users')  # 组内的用户
    )


class UserValidation(db.Model):
    """
    用户验证状态
    """
    __tablename__ = 'user_validation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    passed_email = db.Column(db.Boolean, default=False)
    passed_phone = db.Column(db.Boolean, default=False)


class Group(db.Model):
    '''
    用户组
    '''
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(128))


class Post(db.Model):
    """
    文章
    """
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(80), nullable=False, unique=True)
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)


# db.drop_all()  # clear database
# Create the database tables.
db.create_all()

# Create the API manager.
api = APIManager(app, db=db)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.
api.add(User, methods=['GET', 'POST', 'PUT', 'DELETE'], key_field="name")
api.add(Group, methods=['GET'])
api.add(Post, methods=['GET', 'POST', 'PUT'])

if __name__ == '__main__':
    # start the flask loop
    app.run()
