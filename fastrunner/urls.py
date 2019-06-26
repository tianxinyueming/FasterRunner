"""FasterRunner URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from fastrunner.views import project, api, config, schedule, run, suite, report, download

router = DefaultRouter()
# 项目信息
router.register(r'project', project.ProjectView, base_name='project')
# 配置host_ip
router.register(r'host_ip', config.HostIPView, base_name='host_ip')
router.register(r'copyhost', config.HostIPCopyView, base_name="copyhost")
# 文件管理
router.register(r'file', project.FileView, base_name='file')
# dashboard
# router.register(r'dashboard', project.DashboardView, base_name='dashboard')
# 测试用例
router.register(r'testcase', suite.TestCaseView, base_name='testcase')
router.register(r'testcasecopy', suite.TestCaseCopyView, base_name='testcasecopy')
# 驱动代码
router.register(r'pycode', project.PycodeView, base_name='pycode')
router.register(r'runpycode', project.PycodeRunView, base_name="runpycode")

urlpatterns = [
    url(r'^', include(router.urls)),
    # 文件下载接口
    url('download/', download.DownloadView.as_view()),
    # dashboard
    path('project/<int:pk>/', project.ProjectView.as_view({"get": "single"})),

    path('dashboard/<int:pk>/', project.DashboardView.as_view({
        "get": "get"
    })),

    # 定时任务相关接口
    path('schedule/', schedule.ScheduleView.as_view({
        "get": "list",
        "post": "add"
    })),

    path('schedule/<int:pk>/', schedule.ScheduleView.as_view({
        "delete": "delete"
    })),

    # 二叉树接口地址
    path('tree/<int:pk>/', project.TreeView.as_view()),

    # api接口模板地址
    path('api/', api.APITemplateView.as_view({
        "post": "add",
        "get": "list"
    })),

    path('api/<int:pk>/', api.APITemplateView.as_view({
        "delete": "delete",
        "get": "single",
        "patch": "update",
        "post": "copy"
    })),

    path('teststep/<int:pk>/', suite.CaseStepView.as_view()),

    # config接口地址
    path('config/', config.ConfigView.as_view({
        "post": "add",
        "get": "list",
        "delete": "delete"
    })),

    path('config/<int:pk>/', config.ConfigView.as_view({
        "post": "copy",
        "delete": "delete",
        "patch": "update",
        "get": "all"
    })),

    path('variables/', config.VariablesView.as_view({
        "post": "add",
        "get": "list",
        "delete": "delete"
    })),

    path('variables/<int:pk>/', config.VariablesView.as_view({
        "delete": "delete",
        "patch": "update"
    })),

    # run api
    path('run_api_pk/<int:pk>/', run.run_api_pk),
    path('run_api_tree/', run.run_api_tree),
    path('run_api/', run.run_api),

    # run testsuite
    path('run_testsuite/', run.run_testsuite),
    path('run_test/', run.run_test),
    path('run_testsuite_pk/<int:pk>/', run.run_testsuite_pk),
    path('run_suite_tree/', run.run_suite_tree),
    path('automation_test/', run.automation_test),

    # 报告地址
    path('reports/', report.ReportView.as_view({
        "get": "list"
    })),

    path('reports/<int:pk>/', report.ReportView.as_view({
        "delete": "delete",
        "get": "look"
    }))
]
