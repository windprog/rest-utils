#!/usr/bin/env bash

# 初始化数据库
python api.py db init
# 初次对比
python api.py db migrate -m "initial migration"
# 执行创表
python api.py db upgrade

# 添加测试数据
python demo_data.py
