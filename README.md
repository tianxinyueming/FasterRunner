# FasterRunner

[![LICENSE](https://img.shields.io/github/license/HttpRunner/FasterRunner.svg)](https://github.com/HttpRunner/FasterRunner/blob/master/LICENSE) [![travis-ci](https://travis-ci.org/HttpRunner/FasterRunner.svg?branch=master)](https://travis-ci.org/HttpRunner/FasterRunner) ![pyversions](https://img.shields.io/pypi/pyversions/Django.svg)

> FasterRunner that depends FasterWeb

###
- 增加新功能：文件上传与下载，上传的文件可直接在py文件里引用
- 增加了自己的配置文件，在setting.py中引用，便于管理开发与本地调试，模板见文件：config.conf
- 驱动代码页面支持多py文件在线编辑
- 批量api模板上传（ 支持httprunner -V 1.X/2.X），根据自己本地情况更改db_tools/import_api_data.py中 “MY_API_FILEPATH PROJECT_ID” 后，在根目录下执行命令 python db_tools\import_api_data.py, 重启后台即可
- 支持skipIf机制。testcase中多用例执行时，可编辑api中skipIf一栏
- 支持testcase运行时failfast。 可在配置信息中控制failfast开关。
- 重构了域名管理功能，用于配置环境信息，可在api/配置/testcase中直接以$引用
- 重构了用户认证，使用了drf-jwt应用，移除了注册功能，直接从后台分配账号（出于安全考虑）

```

## Docker 部署 uwsgi+nginx模式
1. docker pull docker.io/mysql:5.7 # 拉取mysql5.7镜像
2. sudo docker run --name mysql -p3306:3306 -d --restart always -v /home/ebao/fastRunner/mysql:/var/lib/mysql
-e  MYSQL_ROOT_PASSWORD=xhb123456 docker.io/mysql:5.7 --character-set-server=utf8 --collation-server=utf8_general_ci  # 运行mysql容器
3. docker exec -it (container_id) bash / mysql -P3306 -h127.0.0.1 -uroot -pxhb123456 连接数据库, 新建一个db，与setting中数据库信息保持一致。
4. 修改settings.py 中使用的配置环境信息dev/prod，复制或者重命名config.conf为myconfig.conf，更新信息
5. 启动rabbitmq docker run -d --name --net=host --restart always rabbitmq -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=password rabbitmq:3-management
6. 修改settings.py BROKER_URL(配置rabbittmq的IP，username,password)
7. 切换到FasterRunner目录，修改uwsgi.ini/Dockerfile/nginx.conf 的配置信息， Linux环境执行下 sh start.sh # 因为windos编写的bash有编码问题
8. docker build -t fastrunner:latest .    # 构建docker镜像
9. docker run -d --name fastrunner -p8000:5000 --restart always fastrunner:latest  # 后台运行docker容器,默认后台端口5000
10. docker exec -it fastrunner /bin/sh  #进入容器内部
    python3 manage.py makemigrations 
    python3 manage.py migrate 
11. 直接访问后台接口查看是否部署成功
``` 

```

## 本地开发环境部署
##### 命令均在FastRunner根目录下执行
``` bash
1. pip install -r requirements.txt 安装依赖库
2. 建立自己所需的myconfig.conf文件，参数见FasterRunner/setting.py文件
3. 若在本地用mysql，则需要安装mysql server，并创建NAME指定的database
4. python manage.py makemigrations 生成数据库迁移文件
5. python manage.py migrate 应用生成的库文件
6. python manage.py runserver 开发环境启动服务
``` 

##### windows安装uwsgi
1. https://pypi.org/project/uWSGI/#files 下载uwsgi文件
2. 在对应python版本的Lib\site-packages下解压
3. 找到uwsgiconfig.py配置文件然后打开
4. 导入模块 import platform，将全部os.uname替换为 platform.uname

##### 其他注意点
- Windows环境安装mysqlclient可能需要先安装Microsoft Visual c++ 14.0
- Settings.py DEBUG=True默认生成sqlite数据库，DEBUG=False使用mysql数据库配置
- 如果提示：No module named 'djcelery' ，再执行一遍 pip install django-celery==3.2.2
- 最好在根目录下新建空文件夹tempWorkDir,media,logs
- 如果提示： ValueError: Unable to configure handler 'default': [Errno 2] No such file or directory: 'mypath\\FasterRunner\\logs\\debug.log' , 手动创建FasterRunner\\logs\\debug.log

