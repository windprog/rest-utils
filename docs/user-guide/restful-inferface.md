# Restful API设计规范

api设计遵循RESTful API设计规范。可以参考：[《RESTful API 设计指南》](http://www.ruanyifeng.com/blog/2014/05/restful_api.html)

关键字介绍：

* {endpoint}: 路径，在这里具体指的是表名
* {id}: 表的主键。一般为int的自增id。
* {key_field}: 表的唯一字段，用于快速定位资源。使用格式："/api/users/@windpro"
* {sub_field}: 子资源字段。例如用户组的字段为: [groups](https://github.com/windprog/rest-utils/blob/master/example/quick_start.py#L57). 则这样使用："/api/users/@windpro/groups"

# 数据查询

## GET /api/{endpoint}

集合查询。支持的参数：[GET Params](/user-guide/specification.md#params).

例子：返回所有 users instances. 
```
GET /api/users

HTTP/1.1 200 OK
{
  "total": 3,
  "items": [{"id": 1, "name": "windpro"}, ...]
}
```

例子：返回名称为"windpro"的用户
```
GET /api/users?name=windpro

HTTP/1.1 200 OK
{
  "total": 1,
  "items": [{"id": 1, "name": "windpro"}]
}
```


## GET /api/{endpoint}/{id}

返回单个资源对象。支持[GET Params](/user-guide/specification.md#params).

相同功能api：

* GET /api/{endpoint}/{key_field}

例子：获取id为1的用户
```
GET /api/users/1

HTTP/1.1 200 OK    
{
  "id": 1,
  "name": "windpro"
}
```


### 使用keyfield获取例子

```python
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode(32), unique=True)

apimanager.add(User, methods=['GET', 'POST', 'DELETE'], key_field="name")
```

```
GET /api/users/@windpro

HTTP/1.1 200 OK    
{
  "id": 1,
  "name": "windpro"
}
```

## GET /api/{endpoint}/{id}/{sub_field}

返回所有的子资源。支持的参数：[GET Params](/user-guide/specification.md#params).

相同功能api：

* GET /api/users/{key_field}/{sub_field}

例子：返回windpro用户所有组
```
GET /api/users/1/groups

HTTP/1.1 200 OK
{
  "total": 2,
  "items": [{"id": 1, "name": "admin"}, ...]
}
```

例子：返回windpro用户的admin组信息
```
GET /api/users/1/grups?name=admin HTTP/1.1

HTTP/1.1 200 OK
{
  "total": 1,
  "items": [{"id": 1, "name": "admin"}]
}
```

# 创建资源

## POST /api/{endpoint}

    创建一个或者多个实例

具有相同作用的api，区别是它们将url字段数据填入request data中：

* POST /api/{endpoint}/{id}
* POST /api/{endpoint}/{key_field}
    

例子：创建一个用户。

```
POST /api/users
{
  "name": "windpro"
}

HTTP/1.1 201 Created
{
  "id": 1,
  "name": "windpro"
}
```

例子：创建多个用户。

```
POST /api/users
[
  {
    "name": "windpro"
  },
  {
    "name": "alex"
  }
]

HTTP/1.1 201 Created
[
  {
    "id": 1,
    "name": "windpro"
  },
  {
    "id": 1,
    "name": "alex"
  }
]
```


## POST /api/users/{id}/{sub_field}

    新增一个或多个子资源。被添加的资源不存在会自动创建。
    
具有相同作用的api：

* POST /api/users/{key_field}/{sub_field}

### Sample Request

这里以Users.groups关系作为例子

例子：windpro 用户添加一个 admin 组。

```
POST /api/users/1/groups HTTP/1.1
{
  "name": "admin"
}

HTTP/1.1 200 OK
{
  "id": 1,
  "name": "admin"
}
```

例子：windpro 添加 admin 和 normal 组。

```
POST /api/users/1/groups HTTP/1.1
[
  {
    "name": "admin"
  },
  {
    "name": "normal"
  }
]

HTTP/1.1 200 OK
[
  {
    "id": 1,
    "name": "windpro"
  },
  {
    "id": 2,
    "name": "normal"
  }
]
```

# 修改资源

## PUT /api/{endpoint}/{id}

    修改一个或多个实例.
    当实例不存在的时候会创建实例。

具有相同作用的api:

* PUT /api/{endpoint}
* PUT /api/{endpoint}/{key_field}
* PATCH /api/{endpoint}
* PATCH /api/{endpoint}/{id}
* PATCH /api/{endpoint}/{key_field}

例子：修改用户的年龄

```
PUT /api/users/1 HTTP/1.1
{
  "age": 26
}

HTTP/1.1 200 OK
{
  "id": 1,
  "name": "windpro",
  "age": 26
}
```


## PUT /api/users/{id}/{sub_field}

    替换子资源，原有的关系将被清空

具有相同作用的api:

* PUT /api/users/{key_field}/{sub_field}
* PATCH /api/users/{id}/{sub_field}
* PATCH /api/users/{key_field}/{sub_field}

例子：替换windpro用户的所有组

```
PUT /api/users/@windpro/groups HTTP/1.1
[
  {
    "name": "admin"
  },
  {
    "name": "normal"
  }
]

HTTP/1.1 200 OK
[
  {
    "id": 1,
    "name": "admin"
  },
  {
    "id": 2,
    "name": "normal"
  }
]
```


# 删除资源

## DELETE /api/{endpoint}/{id}

删除单个实例

具有相同作用的api:

* DELETE /api/{endpoint}/{key_field}
* DELETE /api/{endpoint}：可批量操作，查找规则为 id 或 unique key。

例子：删除windpro用户
```
DELETE /api/users/@windpro

HTTP/1.1 204 No Content
```

## DELETE /api/users/{id}/{sub_field}

    删除关系。查找规则为 id 或 unique key

具有相同作用的api

* DELETE /api/users/{key_field}/{sub_field}

例子：删除 windpro 用户的 admin 组

```
DELETE /api/users/1/groups HTTP/1.1
[
  {
    "name": "admin"
  }
]

HTTP/1.1 204 No Content
```


