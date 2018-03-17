#!/usr/bin/python
# -*- coding: utf-8 -*-
# wget https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite_AutoIncrementPKs.sqlite
import flask
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from rest_utils import APIManager

app = flask.Flask(__name__)
engine = create_engine('sqlite:///../tests/data/Chinook_Sqlite_AutoIncrementPKs.sqlite', convert_unicode=True)
Base = declarative_base()
Base.metadata.bind = engine
api = APIManager(app, engine=engine)
api.auto_create(metadata=Base.metadata)
app.run(port=5002)
# curl http://127.0.0.1:5002/api/Track?_num=20&_expand=1
