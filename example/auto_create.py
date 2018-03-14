#!/usr/bin/python
# -*- coding: utf-8 -*-
# wget https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite_AutoIncrementPKs.sqlite
import flask
from flask_sqlalchemy import SQLAlchemy
from rest_utils import APIManager

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../tests/data/Chinook_Sqlite_AutoIncrementPKs.sqlite'
db = SQLAlchemy(app)
api = APIManager(app, db=db)
api.auto_create()
app.run()
# curl http://127.0.0.1:5000/api/Track?_num=20&_expand=1
