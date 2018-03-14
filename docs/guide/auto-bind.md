## 自动绑定数据库模式

    本框架支持直接从已有数据库中导入字段和关系，生成api。实现无编码情况下的restful api 操作数据库。
    
```python
# wget https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite_AutoIncrementPKs.sqlite
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

## 测试

    curl http://127.0.0.1:5000/api/Track?_num=20&_expand=1
