import json
from rest_framework import serializers
from fastrunner import models
from fastrunner.utils.parser import Parse, parser_variables
from djcelery import models as celery_models


class ProjectSerializer(serializers.ModelSerializer):
    """
    项目信息序列化
    """

    class Meta:
        model = models.Project
        fields = '__all__'


class RelationSerializer(serializers.ModelSerializer):
    """
    树形结构序列化
    """

    class Meta:
        model = models.Relation
        fields = '__all__'


class APISerializer(serializers.ModelSerializer):
    """
    接口信息序列化
    """
    body = serializers.SerializerMethodField()

    class Meta:
        model = models.API
        fields = ['id', 'name', 'url', 'method', 'project', 'relation', 'body']

    def get_body(self, obj):
        parse = Parse(eval(obj.body))
        parse.parse_http()
        return parse.testcase


class CaseSerializer(serializers.ModelSerializer):
    """
    用例信息序列化
    """

    class Meta:
        model = models.Case
        fields = '__all__'


class CaseStepSerializer(serializers.ModelSerializer):
    """
    用例步骤序列化
    """
    body = serializers.SerializerMethodField()

    class Meta:
        model = models.CaseStep
        fields = ['id', 'name', 'url', 'method', 'body', 'case']
        depth = 1

    def get_body(self, obj):
        body = eval(obj.body)
        if "base_url" in body["request"].keys():
            return {
                "name": body["name"],
                "method": "config"
            }
        else:
            parse = Parse(eval(obj.body))
            parse.parse_http()
            return parse.testcase


class ConfigSerializer(serializers.ModelSerializer):
    """
    配置信息序列化
    """
    body = serializers.SerializerMethodField()

    class Meta:
        model = models.Config
        fields = ['id', 'base_url', 'body', 'name', 'update_time']
        depth = 1

    def get_body(self, obj):
        parse = Parse(eval(obj.body), level='config')
        parse.parse_http()
        return parse.testcase


class ReportSerializer(serializers.ModelSerializer):
    """
    报告信息序列化
    """
    type = serializers.CharField(source="get_type_display")
    time = serializers.SerializerMethodField()
    stat = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    success = serializers.SerializerMethodField()

    class Meta:
        model = models.Report
        fields = ["id", "name", "type", "time", "stat", "platform", "success"]

    def get_time(self, obj):
        return json.loads(obj.summary)["time"]

    def get_stat(self, obj):
        return json.loads(obj.summary)["stat"]

    def get_platform(self, obj):
        return json.loads(obj.summary)["platform"]

    def get_success(self, obj):
        return json.loads(obj.summary)["success"]


class VariablesSerializer(serializers.ModelSerializer):
    """
    变量信息序列化
    """

    class Meta:
        model = models.Variables
        fields = '__all__'


class HostIPSerializerPost(serializers.ModelSerializer):
    """
    环境配置信息序列化
    """
    hostInfo = serializers.JSONField(required=True, help_text="环境配置参数")

    class Meta:
        model = models.HostIP
        fields = '__all__'

    def validate(self, attrs):
        attrs["hostInfo"] = json.dumps(attrs["hostInfo"])
        return attrs


class HostIPSerializerList(serializers.ModelSerializer):
    """
    环境配置信息序列化
    """
    hostInfo = serializers.SerializerMethodField()

    class Meta:
        model = models.HostIP
        fields = '__all__'

    def get_hostInfo(self, obj):
        temp_hostinfo = json.loads(obj.hostInfo)
        hostinfo = parser_variables(temp_hostinfo["variables"], temp_hostinfo["desc"])
        return hostinfo


class PeriodicTaskSerializer(serializers.ModelSerializer):
    """
    定时任务信列表序列化
    """
    kwargs = serializers.SerializerMethodField()
    args = serializers.SerializerMethodField()

    class Meta:
        model = celery_models.PeriodicTask
        fields = ['id', 'name', 'args', 'kwargs', 'enabled', 'date_changed', 'enabled', 'description']

    def get_kwargs(self, obj):
        return json.loads(obj.kwargs)

    def get_args(self, obj):
        return json.loads(obj.args)


class FileSerializer(serializers.ModelSerializer):
    """
    文件信息序列化
    """
    file = serializers.FileField(required=True, write_only=True, allow_empty_file=False, use_url='testdatas', label="文件",
                                 help_text="文件", error_messages={"blank": "请上传文件", "required": "请上传文件"})

    class Meta:
        model = models.ModelWithFileField
        fields = '__all__'


class PycodeSerializer(serializers.ModelSerializer):
    """
    驱动代码序列化
    """

    class Meta:
        model = models.Pycode
        fields = '__all__'
        # fields = ['id', 'update_time', 'code', 'project', 'desc', 'name']
