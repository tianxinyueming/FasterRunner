from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework import mixins
from rest_framework import status
from fastrunner import models, serializers
from FasterRunner import pagination
from rest_framework.response import Response
from fastrunner.utils import response
from fastrunner.utils import prepare
from fastrunner.utils.decorator import request_log
from fastrunner.utils.runner import DebugCode
from fastrunner.utils.tree import get_tree_max_id


class ProjectView(ModelViewSet):
    """
    项目增删改查
    """
    queryset = models.Project.objects.all().order_by('-update_time')
    serializer_class = serializers.ProjectSerializer
    pagination_class = pagination.MyCursorPagination

    @method_decorator(request_log(level='INFO'))
    def single(self, request, **kwargs):
        """
        得到单个项目相关统计信息
        """
        pk = kwargs.pop('pk')

        try:
            queryset = models.Project.objects.get(id=pk)
        except ObjectDoesNotExist:
            return Response(response.PROJECT_NOT_EXISTS)

        serializer = self.get_serializer(queryset, many=False)

        project_info = prepare.get_project_detail(pk)
        project_info.update(serializer.data)

        return Response(project_info)

    def perform_create(self, serializer):
        instance = serializer.save()
        prepare.project_init(instance)

    def perform_destroy(self, instance):
        project_id = instance.id
        prepare.project_end(project_id)
        instance.delete()


class DashboardView(GenericViewSet):
    """
    dashboard信息
    """

    @method_decorator(request_log(level='INFO'))
    def get(self, request, **kwargs):
        return Response(prepare.get_project_detail(kwargs['pk']))


class TreeView(APIView):
    """
    树形结构操作
    """

    @method_decorator(request_log(level='INFO'))
    def get(self, request, **kwargs):
        """
        返回树形结构
        当前最带节点ID
        """

        try:
            tree_type = request.query_params['type']
            tree = models.Relation.objects.get(project__id=kwargs['pk'], type=tree_type)
        except KeyError:
            return Response(response.KEY_MISS)

        except ObjectDoesNotExist:
            return Response(response.SYSTEM_ERROR)

        body = eval(tree.tree)  # list
        tree = {
            "tree": body,
            "id": tree.id,
            "success": True,
            "max": get_tree_max_id(body)
        }
        return Response(tree)

    @method_decorator(request_log(level='INFO'))
    def patch(self, request, **kwargs):
        """
        修改树形结构，ID不能重复
        """
        try:
            body = request.data['body']
            mode = request.data['mode']

            relation = models.Relation.objects.get(id=kwargs['pk'])
            relation.tree = body
            relation.save()

        except KeyError:
            return Response(response.KEY_MISS)

        except ObjectDoesNotExist:
            return Response(response.SYSTEM_ERROR)

        #  mode -> True remove node
        if mode:
            prepare.tree_end(request.data, relation.project)

        response.TREE_UPDATE_SUCCESS['tree'] = body
        response.TREE_UPDATE_SUCCESS['max'] = get_tree_max_id(body)

        return Response(response.TREE_UPDATE_SUCCESS)


class FileView(ModelViewSet):
    """
    list:当前项目文件列表
    create:上传与更新文件
    destroy:删除文件
    """
    serializer_class = serializers.FileSerializer
    pagination_class = pagination.MyPageNumberPagination

    def get_queryset(self):
        if self.action == 'create':
            project = self.request.data['project']
            name = self.request.data['name']
            return models.ModelWithFileField.objects.filter(project__id=project, name=name).order_by('-update_time')
        else:
            project = self.request.query_params['project']
            return models.ModelWithFileField.objects.filter(project__id=project).order_by('-update_time')

    def create(self, request, *args, **kwargs):
        if not self.get_queryset():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            pk = self.get_queryset()[0].id
            # instance = self.get_object()
            instance = models.ModelWithFileField.objects.get(pk=pk)

            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if kwargs.get('pk') and int(kwargs['pk']) != -1:
            instance = self.get_object()
            self.perform_destroy(instance)
        elif request.data:
            for content in request.data:
                self.kwargs['pk'] = content['id']
                instance = self.get_object()
                self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PycodeView(GenericViewSet):
    """
    驱动代码 查询 编辑 添加
    """
    queryset = models.Pycode.objects
    serializer_class = serializers.PycodeSerializer

    @method_decorator(request_log(level='DEBUG'))
    def list(self, request):
        """
        查询文件列表
        """
        project = request.query_params['project']
        search = request.query_params["search"]

        files = self.get_queryset().filter(project_id=project).order_by('-update_time')
        if search != '':
            files = files.filter(key__contains=search)
        pagination_queryset = self.paginate_queryset(files)
        serializer = self.get_serializer(pagination_queryset, many=True)

        return self.get_paginated_response(serializer.data)

    @method_decorator(request_log(level='INFO'))
    def add(self, request):
        """添加文件 {
            name: str
        }
        """

        name = request.data["name"]
        if models.Pycode.objects.filter(name=name).first():
            response.PYCODE_EXISTS["name"] = name
            return Response(response.PYCODE_EXISTS)
        # 反序列化
        serializer = serializers.PycodeSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(response.PYCODE_ADD_SUCCESS)

        return Response(response.SYSTEM_ERROR)

    @method_decorator(request_log(level='INFO'))
    def pycodeDebug(self, request, **kwargs):
        """
        得到debugtalk code
        """
        pk = kwargs.pop('pk')
        try:
            queryset = models.Pycode.objects.get(id=pk)
        except ObjectDoesNotExist:
            return Response(response.DEBUGTALK_NOT_EXISTS)

        serializer = self.get_serializer(queryset, many=False)

        return Response(serializer.data)

    @method_decorator(request_log(level='INFO'))
    def update(self, request, **kwargs):
        """
        编辑debugtalk.py 代码并保存
        """

        try:
            pk = kwargs.pop('pk')
            if 'code' in request.data.keys():
                models.Pycode.objects.filter(id=pk).update(code=request.data['code'])
            else:
                models.Pycode.objects.filter(id=pk).update(name=request.data['name'],desc=request.data['desc'])
        except ObjectDoesNotExist:
            return Response(response.SYSTEM_ERROR)

        return Response(response.PYCODE_UPDATE_SUCCESS)

    @method_decorator(request_log(level='INFO'))
    def run(self, request, **kwargs):
        try:
            code = request.data["code"]
            project = request.data["project"]
            filename = request.data["name"]
        except KeyError:
            return Response(response.KEY_MISS)
        debug = DebugCode(code, project, filename)
        debug.run()
        resp = response.PYCODE_RUN_SUCCESS
        resp["msg"] = debug.resp
        return Response(resp)

    @method_decorator(request_log(level='INFO'))
    def delete(self, request, **kwargs):
        try:
            if kwargs.get('pk'):  # 单个删除
                file = models.Pycode.objects.get(id=kwargs['pk'])
                if file.name != 'debugtalk.py':
                    file.delete()
                else:
                    return Response(response.DEBUGTALK_CANNOT_DELETE)
            else:
                isdebugtalk = False
                for content in request.data:
                    file = models.Pycode.objects.get(id=content['id'])
                    if file.name != 'debugtalk.py':
                        file.delete()
                    else:
                        isdebugtalk = True
                if isdebugtalk:
                    return Response(response.DEBUGTALK_CANNOT_DELETE)

        except ObjectDoesNotExist:
            return Response(response.FILE_NOT_EXISTS)

        return Response(response.FILE_DEL_SUCCESS)