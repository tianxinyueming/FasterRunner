import os

from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework import mixins
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import DjangoModelPermissions

from fastrunner import models, serializers
from FasterRunner import pagination
from fastrunner.utils import response
from fastrunner.utils import prepare
from fastrunner.utils.decorator import request_log
from fastrunner.utils.runner import DebugCode
from fastrunner.utils.tree import get_tree_max_id
from FasterRunner.settings import MEDIA_ROOT


class ProjectView(ModelViewSet):
    """
    项目增删改查
    """
    queryset = models.Project.objects.all().order_by('-update_time')
    serializer_class = serializers.ProjectSerializer
    pagination_class = pagination.MyCursorPagination
    permission_classes = (DjangoModelPermissions,)

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


class TreeView(GenericViewSet):
    """
    树形结构操作
    """
    permission_classes = (DjangoModelPermissions,)

    def get_queryset(self):
        project_id = self.kwargs.get('pk')
        queryset = models.Relation.objects.filter(project__id=project_id).order_by('-update_time')
        return queryset

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
    permission_classes = (DjangoModelPermissions,)

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
            self.kwargs['pk'] = self.get_queryset()[0].id
            instance = self.get_object()

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
            filepath = os.path.join(MEDIA_ROOT, str(instance.file))
            if os.path.exists(filepath):
                os.remove(filepath)
            self.perform_destroy(instance)
        elif request.data:
            for content in request.data:
                self.kwargs['pk'] = content['id']
                instance = self.get_object()
                filepath = os.path.join(MEDIA_ROOT, str(instance.file))
                if os.path.exists(filepath):
                    os.remove(filepath)
                self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PycodeRunView(GenericViewSet, mixins.RetrieveModelMixin):
    """
    驱动代码调试运行
    """
    serializer_class = serializers.PycodeSerializer

    def get_queryset(self):
        project = self.request.query_params["project"]
        queryset = models.Pycode.objects.filter(project_id=project).order_by('-update_time')
        return queryset

    @method_decorator(request_log(level='INFO'))
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        debug = DebugCode(serializer.data["code"], serializer.data["project"], serializer.data["name"])
        debug.run()

        debug_rsp = {
            "msg": debug.resp
        }
        return Response(data=debug_rsp)


class PycodeView(ModelViewSet):
    """
    驱动代码模块
    """
    serializer_class = serializers.PycodeSerializer
    pagination_class = pagination.MyPageNumberPagination
    permission_classes = (DjangoModelPermissions,)

    def get_queryset(self):
        project = self.request.query_params["project"]
        queryset = models.Pycode.objects.filter(project_id=project).order_by('-update_time')
        if self.action == 'list':
            queryset = queryset.filter(name__contains=self.request.query_params["search"])
        return queryset

    @method_decorator(request_log(level='INFO'))
    def destroy(self, request, *args, **kwargs):
        if kwargs.get('pk') and int(kwargs['pk']) != -1:
            instance = self.get_object()
            if instance.name == 'debugtalk.py':
                Response(status=status.HTTP_423_LOCKED)
            else:
                self.perform_destroy(instance)
        elif request.data:
            for content in request.data:
                self.kwargs['pk'] = content['id']
                instance = self.get_object()
                if instance.name != 'debugtalk.py':
                    self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
