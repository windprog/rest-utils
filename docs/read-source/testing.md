### 测试

### 编写测试
test_api.py：测试wsgi
```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
from json import dumps, loads
from quick_start import app

client = app.test_client()


def test_func():
    """
    创建用户
    :param req: 跟requests库的用法一致
    :return:
    """
    res = client.put('/api/users', headers={
        "Content-Type": 'application/json'
    }, data=dumps({
        "name": "windprozhao",
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
    assert res.status_code in [201, 200]  # 创建分类成功
    assert loads(res.data)['name'] == 'windprozhao'

    # 检查创建分类
    addr = client.get('/api/users/@windprozhao')
    assert 'name' in loads(addr.data)

    # 检查文章创建
    posts = client.get('/api/posts?title=Snakes')
    assert len(loads(posts.data)["items"]) == 1
```

#### 运行测试

    py.test

结果

    platform darwin -- Python 2.7.10, pytest-2.9.1, py-1.4.31, pluggy-0.3.1
    rootdir: /Users/windpro/code/github/rest-utils, inifile: 
    collected 1 items 
    
    test_api.py .
