## Models

    想使用本框架，你需要先定义数据库模型。可选：SQLAlchemy or Flask-SQLALchemy.

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
import flask
from flask_sqlalchemy import SQLAlchemy

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./test.db'
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(32), unique=True)
    posts = db.relationship(
        'Post',
        backref=db.backref('user')
    )


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime, nullable=False)


db.create_all()
```

If you are using pure SQLAlchemy:

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask
from sqlalchemy import Column, Date, DateTime, Float, Integer, Unicode, Text, String
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship

app = Flask(__name__)
engine = create_engine('sqlite:///./test.db', convert_unicode=True)

Base = declarative_base()
Base.metadata.bind = engine

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(32), unique=True)
    posts = relationship(
        'Post',
        backref=backref('user')
    )


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(80), nullable=False)
    body = Column(Text)
    pub_date = Column(DateTime, nullable=False)


Base.metadata.create_all()
```

## APIManager

    拥有模型之后，就可以开始添加api。

```python
import rest_utils

api = rest_utils.APIManager(app, db=db)
```

    Or if you are using pure SQLAlchemy, specify the session you created above instead:

```python
api = rest_utils.APIManager(app, engine=engine)
```

## create the API

```python
person_blueprint = api.add(User, methods=['GET', 'POST', 'DELETE'])
```

Note that you can specify which HTTP methods are available for each API endpoint. There are several more customization options; for more information, see [Customizing the Restful interface](/guide/customizing-restful.md).

