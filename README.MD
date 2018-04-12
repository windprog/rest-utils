## Introduction ##

Rest-Utils 为使用 SQLAlchemy (or Flask-SQLAlchemy) 定义的数据库模型提供简单的Restful APIs生成。 
生成的API以JSON格式转换数据。内部使用 marshmallow 使得复用数据转换非常简单。

For more information, see the

  * [documentation](https://windprog.github.io/rest-utils/),
  * [Python Package Index listing](https://pypi.python.org/pypi/rest-utils),
  * [source code repository](https://github.com/windprog/rest-utils).
  * **Online Example**: [ADMIN](http://rest-utils.codedig.com:5000/admin), [API](http://rest-utils.codedig.com:5000/api/Track?_num=20&_expand=1), 
  * [最佳实践](https://github.com/windprog/rest-utils-sample).

## Install

    # 可以从页面下载。不过推荐使用pip，virtualenv安装。
    pip install Rest-Utils

## Quick Start

    pip install Rest-Utils flask_sqlalchemy
    wget https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite_AutoIncrementPKs.sqlite

```python
import flask
from flask_sqlalchemy import SQLAlchemy
from rest_utils import APIManager

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./Chinook_Sqlite_AutoIncrementPKs.sqlite'
db = SQLAlchemy(app)
api = APIManager(app, db=db)
api.auto_create()
app.run()
```

    curl http://127.0.0.1:5000/api/Track?_num=20&_expand=1

详细使用参见：[快速开始](https://windprog.github.io/rest-utils/guide/quickstart/)


# Change Log

## 1.0.0

* RESTful API风格，完整CRUD支持。
* sqlachemy ORM 模型生成 marshmallow Schema and fields。
* 从已有数据库自动生成API。

## 1.0.4

* Change APIManager.auto_create to SQLAlchemy Automap.
* 添加APIManager.register_admin.详情可参见：/example/auto_create_admin.py
* add windows support


# TODO

* 添加schema文档
* 在整理切分文档
