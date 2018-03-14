## 发布

    cat ~/.pypirc
    python setup.py sdist upload -r share
    python setup.py sdist upload -r pypi
    mkdocs gh-deploy

## 安装

    virtualenv env
    source env/bin/activate
    pip install -i http://10.213.144.145:8080/root/all/+simple/ --trusted-host 10.213.144.145 rest-utils
    cd example
    bash init.sh
    python api.py runserver
    
## 测试

    curl http://localhost:4488/api/post
