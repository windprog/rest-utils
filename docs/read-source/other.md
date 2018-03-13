## 用户自定义异常

### 抛出自定义异常
定义异常:

```python
from rest_utils import RestException
class MeException(RestException):
    """
    自定义错误信息
    """
    status = 403  # HTTP 错误码
```

抛出异常

```python
raise MeException({"info":"test"})
```

前端输出:

```
status_code:403
{
    "type": "MeException",  # 异常类型
    "msg": "自定义错误信息",  # 错误描述（内部)
    "detail": {"info":"test"},  # 用户自定义数据
}
```

# 模型 schema 参数说明

    该参数作用于APIManager.add 或 ModelSchema.Meta:


## 多数据库

### 定义方式
  可参考 [flask-sqlalchemy官方文档](http://flask-sqlalchemy.pocoo.org/2.1/binds/#referring-to-binds)


## QA solution

### OperationalError: (OperationalError) unable to open database file None None

    Based on sqlalchemy documentation:

    sqlite:////db_absolute_path
    
    sqlite:///db_relative_path
    (notice that the second line above has only 3 slashes) In my case providing relative path helped.
