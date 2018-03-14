## 编写模型

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
import flask
import datetime
from flask_sqlalchemy import SQLAlchemy
from rest_utils import APIManager

# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./test.db'
db = SQLAlchemy(app)

class User(db.Model):
    """
    用户
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(32), unique=True)  # 用户名唯一

    # 绑定一对多关系
    # 用户文章列表
    posts = db.relationship(
        'Post',
        backref=db.backref('user')
    )


class Post(db.Model):
    """
    文章
    """
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)


# db.drop_all()  # clear database
# Create the database tables.
db.create_all()

# Create the API manager.
manager = APIManager(app, db=db)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.
manager.add(User, methods=['GET', 'POST', 'PUT', 'DELETE'], key_field="name")
manager.add(Post, methods=['GET', 'POST', 'PUT'])

if __name__ == '__main__':
    # start the flask loop
    app.run()
```

#### 运行

    python run.py

结果:

     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

#### 提交数据

    curl -X PUT --data '{"posts": [{"body": "Python is pretty cool", "title": "Hello Python!"}, {"body": "Ssssssss", "title": "Snakes"}], "name": "windprozhao"}' -H "Content-Type:application/json" http://localhost:5000/api/users

#### 验证提交

    curl http://localhost:5000/api/users
