#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/3/13
Desc    :   
"""
import requests


def ensure_data():
    res = requests.put("http://127.0.0.1:5001/api/users", json={
        "name": "windpro",
        "email": "windprog@gmail.com",
        "phone": "18900000000",
        "validation": {
            "passed_email": True,
            "passed_phone": False,
        },
        "groups": [
            {
                "name": "admin",
            },
            {
                "name": "normal",
            }
        ],
        "posts": [
            {
                "title": "Hello Python!",
                "body": "Python is pretty cool",
            },
            {
                "title": "Snakes",
                "body": "Ssssssss",
            },
        ]
    })
    assert res.status_code in [200, 201]


if __name__ == '__main__':
    ensure_data()
