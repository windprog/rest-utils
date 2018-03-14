## Introduction ##

Rest-Utils 为使用 SQLAlchemy (or Flask-SQLAlchemy) 定义的数据库模型提供简单的Restful APIs生成。
生成的API以JSON格式发送和接收消息。
使用 marshmallow 使得转换非常便捷。

For more information, see the

  * [documentation](http://localhost:8000),
  * [Python Package Index listing](https://pypi.python.org/pypi/rest-utils),
  * [source code repository](https://github.com/windprog/rest-utils).

## Install

    # 可以从GitHub的页面下载。 不过推荐使用pip，virtualenv安装。
    pip install Rest-Utils

## Quick Start

[快速开始](/guide/quickstart.md)


## 发布

    cat ~/.pypirc
    python setup.py sdist upload -r share

## 安装

    virtualenv env
    source env/bin/activate
    pip install -i http://10.213.144.145:8080/root/all/+simple/ --trusted-host 10.213.144.145 rest-utils
    cd example
    bash init.sh
    python api.py runserver
    
## 测试

    curl http://localhost:4488/api/post


## example

    查看exmaple/api.py


# Change Log

* 0.4.1 添加 RESTful marshmallow support
* 0.4.2 添加 RESTful api doc
* 0.4.3 添加 auto bind database
