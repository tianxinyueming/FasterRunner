# FasterRunner

[![LICENSE](https://img.shields.io/github/license/HttpRunner/FasterRunner.svg)](https://github.com/HttpRunner/FasterRunner/blob/master/LICENSE) [![travis-ci](https://travis-ci.org/HttpRunner/FasterRunner.svg?branch=master)](https://travis-ci.org/HttpRunner/FasterRunner) ![pyversions](https://img.shields.io/pypi/pyversions/Django.svg)

> FasterRunner that depends FasterWeb

###
- 增加新功能：文件上传与下载，上传的文件可直接在py文件里引用
- 增加了自己的配置文件，在setting.py中引用，便于管理开发与本地调试，模板见文件：config.conf
- 驱动代码页面支持多py文件在线编辑
- 批量api模板上传（ 支持httprunner -V 1.X/2.X），根据自己本地情况更改db_tools/import_api_data.py中 “MY_API_FILEPATH PROJECT_ID” 后，在根目录下执行命令 python db_tools\import_api_data.py, 然后刷新即可
- 支持skipIf机制。编辑testcase时可编辑api中skipIf一栏。
- 支持testcase运行时failfast。 可在配置信息中控制failfast开关。
- 重构了域名管理功能，用于配置环境相关信息，相当于配置管理的一个拆分，便于单个调试api以及快速切换环境，更好的组合配置信息与环境信息。而对于base_url字段，域名管理的权限高于配置管理，若域名管理里base_url不为空，则会覆盖配置管理的base_url。例如可以只将登录所需信息放在域名管理里。
- 重构了用户认证，使用了drf-jwt应用，移除了注册功能，直接从后台分配账号（出于安全考虑）
- api/testcase运行时可以指定excel测试数据，在后台运行时会生成系统环境变量“excelName”/“excelsheet”，在驱动代码里可以os.environ["excelsheet"]方式获取，并进一步做自己的处理
- 增加了简易的excel报告，提取了简要的报错信息，便于大批量运行测试用例时查看
- 抓取httprunner错误返回到前端
- 配置管理里新加了output参数，output将写入报告里，output参数来自于整个用例运行时variables/extract等。
- 更新了api与testcase的关系。沿用httprunner作者的思想，测试用例中的request/headers/method/url内容直接调用相应api中的内容；并且更新api的request/header/method/url时，会自动改变测试用例中的request/headers/method/url
- 单个testcase执行时选择是否异步，默认异步，并且可以指定报告名称
- 增加了xadmin后台管理系统，通过后台管理系统可以方便的完成分配账号以及简单的api权限控制
```

## Docker 部署 uwsgi+nginx模式
1. docker pull docker.io/mysql:5.7 # 拉取mysql5.7镜像
2. sudo docker run --name mysql -p3306:3306 -d --restart always -v /home/ebao/fastRunner/mysql:/var/lib/mysql
-e  MYSQL_ROOT_PASSWORD=xhb123456 docker.io/mysql:5.7 --character-set-server=utf8 --collation-server=utf8_general_ci  # 运行mysql容器
3. docker exec -it (container_id) bash / mysql -P3306 -h127.0.0.1 -uroot -pxhb123456 连接数据库, 新建一个db，与setting中数据库信息保持一致。
4. 修改settings.py 中使用的配置环境信息dev/prod，复制或者重命名config.conf为myconfig.conf，更新信息
5. 启动rabbitmq docker run -d --name --net=host --restart always rabbitmq -e RABBITMQ_DEFAULT_USER=user -e RABBITMQ_DEFAULT_PASS=password rabbitmq:3-management
6. 修改settings.py BROKER_URL(配置rabbittmq的IP，username,password)
7. 切换到FasterRunner目录，修改uwsgi.ini/Dockerfile/nginx.conf的配置信息
8. 根目录下新建空文件夹tempWorkDir,media,logs 
9. docker build -t fastrunner:latest .    # 构建docker镜像
10. docker run -d --name fastrunner -p8000:5000 --restart always fastrunner:latest  # 后台运行docker容器,默认后台端口5000
11. docker exec -it fastrunner /bin/sh  #进入容器内部
    python3 manage.py makemigrations 
    python3 manage.py migrate 
12. 直接访问后台接口查看是否部署成功
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
7. 安装rabbmitMQ中间件，并配置setting中的BROKER_URL（默认一般不用修改）
7. celery -A FasterRunner worker -l info 启动异步worker
``` 

##### 其他注意点
- Windows环境安装mysqlclient可能需要先安装Microsoft Visual c++ 14.0,然后在 https://www.lfd.uci.edu/~gohlke/pythonlibs/ 此链接下找自己需要的windows安装包
- 如果提示：No module named 'djcelery' ，再执行一遍 pip install django-celery==3.2.2
- 如果提示： ValueError: Unable to configure handler 'default': [Errno 2] No such file or directory: 'mypath\\FasterRunner\\logs\\debug.log' , 手动创建FasterRunner\\logs\\debug.log
- 下载rabbmitMQ所需的erlang时，在官网下载很慢，可以访问 https://www.erlang-solutions.com/resources/download.html，windows配置参考：https://blog.csdn.net/qq_31634461/article/details/79377256
- ubuntu 安装py3.6缺少包参考：https://blog.csdn.net/kunagisatomo_i/article/details/81177558
- xadmin后台添加小组件报错：注释掉/usr/local/lib/pyon3.7/site-packages/django/forms/boundfield.py中的大概93行  ```#renderer=self.form.renderer```
- 如果运行结果数据比较大的话，mysql内运行：set global max_allowed_packet=1073741824; 这是1G的大小。