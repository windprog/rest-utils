## methods

    注册的HTTP方法。有：'GET': 查询, "POST": 新增, "PUT": 修改, "DELETE": 删除。
    默认情况下，APIManager.create_api() 会创建只读接口; 其他的method会被拒绝访问。
    
apimanager.add(User, methods=['GET', 'POST', 'DELETE'])

具体添加的内容和使用方法可[详情](/guide/interfaces.md).

## endpoint

默认情况下，APIManager.create_api()添加的模型或schema使用的interface名称为模型表名。可以手动指定名称

```python
person_blueprint = api.add(User, endpoint="peoples")
```

##  include_fk

    展示外键. 默认:True

## key_field

    查找字段。
    如：/users/@windpro

## endpoint

    资源名称。默认为tablename
    
## match_fields

    搜索的字段。默认：[]. 

## 字段例子

```python
from models import Users
from rest_utils import ModelSchema

class UsersSchema(ModelSchema):
    class Meta:
        model = Users
        methods = ['GET', "POST", "PUT", "DELETE"]
        include_fk = True
        key_field = "name"
        endpoint = "users"
        match_fields = ["name"]
        
api.add(UsersSchema)
```

## filters

    查询资源时使用的filters。如def get_users(): return [Users.name=="windpro"]

## create

    创建实例回调方法。(model, data)

## update

    修改实例回调方法。(instance, data)

## delete

    删除实例回调方法。(instance)

## created

    commit数据库之后的创建实例回调方法。(instance)

## updated

    commit数据库之后的修改实例回调方法。(instance)

## deleted

    commit数据库之后的删除实例回调方法。(instance)
    
## 回调方法例子

```python
from models import Users
from rest_utils import ModelSchema

class UsersSchema(ModelSchema):
    class Meta:
        model = Users
        methods = ['GET', "POST", "PUT", "DELETE"]
        
        @staticmethod
        def filters():
            return [Users.name=="windprozhao"]
        
        @staticmethod
        def create(model, data):
            return model(**data)

        @staticmethod
        def update(instance, data):
            for key, value in data.items():
                setattr(instance, key, value)
            return instance
        @staticmethod
        def delete(instance):
            return instance

        @staticmethod
        def created(instance):
            return instance
        @staticmethod
        def updated(instance):
            return instance
        @staticmethod
        def deleted(instance):
            return instance

api.add(UsersSchema)
```
