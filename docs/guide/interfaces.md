## GET /api/users

    返回所有的Person instances. 


    GET /api/users
    
    HTTP/1.1 200 OK
    {
      "total": 3,
      "items": [{"id": 1, "name": "windpro"}, ...]
    }


详细查询参数可以参看[GET Params](/guide/specification.md#params).
例如：

    GET /api/users?name=windpro HTTP/1.1
    
    HTTP/1.1 200 OK
    {
      "total": 1,
      "items": [{"id": 1, "name": "windpro"}]
    }


## GET /api/person/(int: id)

使用id查询并返回单个实例。同样支持[GET Params](/guide/specification.md#params).

    HTTP/1.1 200 OK
    
    {
      "id": 1,
      "name": "windpro"
    }

## GET /api/person/(string: key_field)

使用配置中的keyfield查询并返回单个实例。

```python
apimanager.add(User, methods=['GET', 'POST', 'DELETE'], key_field="name")
# request
requests.get("/api/users/@windpro")
```

## POST /api/person

    创建一个或者多个实例

### Sample Request

创建一个实例。

    POST /api/users HTTP/1.1
    
    {
      "name": "windpro"
    }

创建多个实例。

    POST /api/users HTTP/1.1
    
    [
      {
        "name": "windpro"
      },
      {
        "name": "alex"
      }
    ]

### Sample Response

    HTTP/1.1 201 Created
    
    {
      "id": 1,
      "name": "windpro"
    }

## POST /api/person/(id or key_field)

创建实例。请求和返回类似于[POST /api/person](#post-apiperson)

## PUT or PATCH /api/person

    修改一个或多个实例.当实例不存在的时候会创建实例。

### Sample Request
    PUT /api/users HTTP/1.1
    
    {
      "id": 1,
      "age": 26
    }

### Sample Response

    HTTP/1.1 200 OK
    
    {
      "id": 1,
      "name": "windpro",
      "age": 26
    }

## PUT or PATCH /api/person/(id or key_field)

修改实例。请求和返回类似于[PUT /api/person](#put-or-patch-apiperson)

## DELETE /api/person/(id or key_field)

删除实例

### Sample response:

    HTTP/1.1 204 No Content

## GET /api/users/(id or key_field)/groups

返回所有的Person下的groups关系

    GET /api/users/1/grups
    
    HTTP/1.1 200 OK
    {
      "total": 2,
      "items": [{"id": 1, "name": "admin"}, ...]
    }


详细查询参数可以参看[GET Params](/guide/specification.md#params).
例如：

    GET /api/users/1/grups?name=admin HTTP/1.1
    
    HTTP/1.1 200 OK
    {
      "total": 1,
      "items": [{"id": 1, "name": "admin"}]
    }

## POST /api/users/(id or key_field)/groups

    新增一个或多个Person.groups关系

### Sample Request

添加一个子资源。

    POST /api/users/1/groups HTTP/1.1
    
    {
      "name": "admin"
    }

添加多个子资源。

    POST /api/users/1/groups HTTP/1.1
    
    [
      {
        "name": "admin"
      },
      {
        "name": "normal"
      }
    ]

### Sample Response

    HTTP/1.1 200 OK
    
    {
      "id": 1,
      "name": "windpro"
    }

## PUT or PATCH /api/users/(id or key_field)/groups

    替换Person.groups关系，原有的groups将被清空

### Sample Request

替换多个子资源。

    PUT /api/users/1/groups HTTP/1.1
    
    [
      {
        "name": "admin"
      },
      {
        "name": "normal"
      }
    ]

### Sample Response

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

## DELETE /api/users/(id or key_field)/groups

    删除Person.groups关系。查找规则为 id 或 unique key

### Sample Request

替换多个子资源。

    DELETE /api/users/1/groups HTTP/1.1
    
    [
      {
        "name": "admin"
      }
    ]

### Sample Response

    HTTP/1.1 204 No Content
