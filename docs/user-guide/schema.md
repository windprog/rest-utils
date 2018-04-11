# 介绍

> 在我们的日常开发中，框架自带的 Restful API 增删改查不一定能满足所有情况。我们也需要自定义api。

> 利用schema可以让 **数据校验** 和 **动态字段** 变得非常简单。

例子如下，具体项目可以参考：[最佳实践](https://github.com/windprog/rest-utils-sample/blob/master/api/user_api.py)

## models.py

```python
class User(db.Model):
    """
    用户
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(32), unique=True)
```

## schemas.py

```python
import random
from rest_utils import ModelSchema
from rest_utils import fields
from models import User


class UserSchema(ModelSchema):
    """
    marshmallow例子可参见：http://marshmallow.readthedocs.io/
    """
    
    __model__ = User
    # 实现动态字段
    sort = fields.Function(
        serialize=lambda obj: random.randint(10, 20),
    )
```

编写完 schemas 之后，我们可以随时在自己的api中序列化和反序列化数据库对象。
在这个过程中可以利用marshmallow的能力添加动态字段。

## app.py

```python
from flask import jsonify
from rest_utils.utils import get_session
import random
from api import app
from models import User
from schemas import UserSchema

@app.route('/api/query_first_user')
def query_first_user():
    first_user = User.query.first()
    data, errors = UserSchema().dump(first_user)
    return jsonify({
        "first_user": data
    })

@app.route('/api/create_random_user')
def create_random_user():
    session = get_session()
    schema = UserSchema(session=session)
    ins, errors = schema.load({
        "name": "test_user" + str(random.randint(1, 100))
    })
    session.add(ins)
    session.commit()
    return jsonify({
        "random_user": schema.dump(ins).data
    })
```

## Request
这样我们就可以访问自定义api了

```
GET /api/query_first_user

HTTP/1.1 200 OK
{
  "first_user": {"id": 1, "name": "windpro", sort: 15}
}
```
