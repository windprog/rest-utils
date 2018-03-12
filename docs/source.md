# 目录结构及作用

    ├── rest_utils
    │   ├── utils                            # 工具方法集合
    │   ├── date.py
    │   ├── decorators.py
    │   ├── error_route.py
    │   ├── exception.py                     # 异常类
    │   ├── exp_format.py
    │   ├── flask_engine.py
    │   ├── flask_trace.py
    │   ├── libs                             # 第三方源码
    │   ├── log.py                           # 日志相关
    │   ├── params.py
    │   ├── py3to2.py
    │   ├── sa_util.py
    │   ├── schema.py                        # marshmallow scheme基类，用于sqlalchemy model 和 dict相互转换。
    │   ├── fields.py                        # marshmallow fields。用于字段定义，和原生的用法一致。
    │   ├── static.py                        # 框架定义的常量
    │   ├── manager.py                       # rest api 模块
    └── tests                                # 测试用例
    ├── example                              # 使用例子
    │   ├── api.py
    │   ├── demo_app.py
    │   ├── demo_data.py
    │   ├── init.sh
    ├── docs                                 # 文档目录
    │   ├── api.md                           # API文档
    │   └── getting_started.md               # 快速开始
    ├── README.MD                            # 项目简介
    ├── setup.py

