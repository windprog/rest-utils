# 例子

## 发布

    cat ~/.pypirc
    python setup.py sdist upload -r pypi

## 安装

    virtualenv env
    source env/bin/activate
    pip install git+http://ao:ao123456@10.213.144.145/share/rest-utils.git
    cd example
    bash init.sh
    python api.py runserver
    
## 使用

    curl http://localhost:4488/api/post
