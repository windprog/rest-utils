[toc]
# 安装

    可以从GitHub的页面下载。 不过推荐使用pip，virtualenv安装。
    pip install rest-utils


# 快速入门

    用户-地址模型、多对一

## 编写模型

models.py：
```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
import datetime

# 模型
db = SQLAlchemy()
MYSQL_URI = "mysql://root:windpro@localhost/demo?charset=utf8"


class Post(db.Model):

    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    body = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship(
        'Category',
        backref=db.backref('posts')
    )


class Category(db.Model):

    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)


if __name__ == '__main__':
    def create_sql():
        from sqlalchemy import create_engine
        engine = create_engine(MYSQL_URI, echo=False)
        db.Model.metadata.drop_all(engine)  # 清空数据库
        db.Model.metadata.create_all(engine)
    # 创建数据库
    create_sql()
```

### 同步数据库

    # 重复运行可清空数据库
    python models.py


### 运行服务

#### 入口

run.py：运行wsgi服务
```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask
from rest_utils import APIManager
import models

def create_app():
    app = Flask(__name__)
    app.config.setdefault('SQLALCHEMY_ECHO', False)
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', models.MYSQL_URI)
    return app

def create_api(app):
    api =  APIManager(app, db=models.db, prefix="/api")
    
    api.add(models.Post, methods=['GET', 'PUT', 'POST'])
    api.add(models.Category, methods=['GET', 'PUT', 'POST'], key_field='name')
    
    return api


# 创建APP
app = create_app()
api = create_api(app)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8888, use_debugger=True)

```

#### 运行

    python run.py
    
结果:

     * Running on http://0.0.0.0:8888/ (Press CTRL+C to quit)

### 测试

### 编写测试
test_api.py：测试wsgi
```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
from json import dumps, loads
from run import app

client = app.test_client()

def test_func():
    """
    创建用户
    :param req: 跟requests库的用法一致
    :return:
    """
    res = client.post('/api/categories', data=dumps({
        "name": "Python",
        'posts': [
            {
                'title': 'Hello Python!',
                'body': 'Python is pretty cool',
            },
            {
                'title': 'Snakes',
                'body': 'Ssssssss',
            },
        ]
    }))
    assert res.status_code == 201  # 创建分类成功
    assert loads(res.data)['name'] == 'Python'

    # 检查创建分类
    addr = client.get('/api/categories/@Python')
    assert 'name' in loads(addr.data)
    
    # 检查文章创建
    posts = client.get('/api/posts?title=Snakes')
    assert len(loads(addr.data)["items"]) == 1

```

#### 运行测试

    py.test

结果

    platform darwin -- Python 2.7.10, pytest-2.9.1, py-1.4.31, pluggy-0.3.1
    rootdir: /Users/windpro/code/netease/devrest, inifile: 
    collected 1 items 
    
    test_api.py .
