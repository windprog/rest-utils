#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/15
Desc    :   
"""
# 与from flask_sqlalchemy import SQLAlchemy 使用形式一样
from rest_utils import SQLAlchemy
import os
import datetime
from flask import Flask
from rest_utils.api_exception import handler_app
import logging

# 创建APP
app = Flask(__name__)
# 处理通用异常
handler_app(app)
# 模型
db = SQLAlchemy(app)

logger = logging.getLogger(__name__)


@app.route('/')
def index():
    from random import randint
    a, b = randint(1, 15), randint(1, 15)
    logging.info('global level Adding two random numbers {} {}'.format(a, b))
    logger.info('module level Adding two random numbers {} {}'.format(a, b))
    return str(a + b)


# 测试数据库路径
DB_LOC = os.path.abspath(os.path.join(os.path.dirname(__file__), "test.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///%s' % DB_LOC


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship(
        'Category',
        backref=db.backref('posts', lazy=True)
    )


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)


def restless():
    # 绑定模型对应的api
    from flask_restless import APIManager
    with app.app_context():
        manager = APIManager(app, flask_sqlalchemy_db=db)
        manager.create_api(Post, methods=['GET', 'PUT', 'POST'])
        manager.create_api(Category, methods=['GET', 'PUT', 'POST'])
        return manager


restless()
