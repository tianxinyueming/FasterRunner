from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from fastrunner import models, serializers
from FasterRunner import pagination
from rest_framework.response import Response
from fastrunner.utils import response
from fastrunner.utils import prepare
from fastrunner.utils.decorator import request_log
from fastrunner.utils.runner import DebugCode
from fastrunner.utils.tree import get_tree_max_id
from FasterRunner.settings import MEDIA_ROOT
import os


class ProjectView(GenericViewSet):
    """
    项目增删改查
    """
    queryset = models.Project.objects.all().order_by('-update_time')
    serializer_class = serializers.ProjectSerializer
    pagination_class = pagination.MyCursorPagination

    @method_decorator(request_log(level='DEBUG'))
    def list(self, request):
        """
        查询项目信息
        """
        projects = self.get_queryset()
        page_projects = self.paginate_queryset(projects)
        serializer = self.get_serializer(page_projects, many=True)
        return self.get_paginated_response(serializer.data)

    @method_decorator(request_log(level='INFO'))
    def add(self, request):
        """添加项目 {
            name: str
        }
        """

        name = request.data["name"]

        if models.Project.objects.filter(name=name).first():
            response.PROJECT_EXISTS["name"] = name
            return Response(response.PROJECT_EXISTS)
        # 反序列化
        serializer = serializers.ProjectSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            project = models.Project.objects.get(name=name)
            project.filePath = MEDIA_ROOT + '/' + str(project.id) + '/'
            project.save()
            prepare.project_init(project)
            return Response(response.PROJECT_ADD_SUCCESS)

        return Response(response.SYSTEM_ERROR)

    @method_decorator(request_log(level='INFO'))
    def update(self, request):
        """
        编辑项目
        """

        try:
            project = models.Project.objects.get(id=request.data['id'])
        except (KeyError, ObjectDoesNotExist):
            return Response(response.SYSTEM_ERROR)

        if request.data['name'] != project.name:
            if models.Project.objects.filter(name=request.data['name']).first():
                return Response(response.PROJECT_EXISTS)

        # 调用save方法update_time字段才会自动更新
        project.name = request.data['name']
        project.desc = request.data['desc']
        project.save()

        return Response(response.PROJECT_UPDATE_SUCCESS)

    @method_decorator(request_log(level='INFO'))
    def delete(self, request):
        """
        删除项目
        """
        try:
            project = models.Project.objects.get(id=request.data['id'])

            project.delete()
            prepare.project_end(project)

            return Response(response.PROJECT_DELETE_SUCCESS)
        except ObjectDoesNotExist:
            return Response(response.SYSTEM_ERROR)

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


class FileView(GenericViewSet):
    """
    文件上传 下载
    """
    queryset = models.ModelWithFileField.objects
    serializer_class = serializers.FileSerializer

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
    def upload(self, request):
        """
        接收文件并更新保存
        """
        try:
            # 打开特定的文件进行二进制的写操作
            myFile = request.FILES['file']
            project_id = request.POST["project_id"]
            if not os.path.exists(MEDIA_ROOT + '/' + str(project_id)):
                os.makedirs(MEDIA_ROOT + '/' + str(project_id))
            filePath = MEDIA_ROOT + '/' + str(project_id) + '/' + myFile.name

            if models.ModelWithFileField.objects.filter(filePath=filePath).first():
                FileObject = models.ModelWithFileField.objects.get(filePath=filePath)
            else:
                FileObject = models.ModelWithFileField()
                FileObject.name = myFile.name
                FileObject.project_id = project_id
                FileObject.filePath = filePath

            with open(filePath, 'wb+') as f:
                # 分块写入文件
                for chunk in myFile.chunks():
                    f.write(chunk)

            FileObject.save()
            return Response(response.FILE_UPLOAD_SUCCESS)
        except ObjectDoesNotExist:
            return Response(response.FILE_FAIL)

    @method_decorator(request_log(level='INFO'))
    def delete(self, request, **kwargs):
        try:
            if kwargs.get('pk'):  # 单个删除
                models.ModelWithFileField.objects.get(id=kwargs['pk']).delete()
            else:
                for content in request.data:
                    models.ModelWithFileField.objects.get(id=content['id']).delete()

        except ObjectDoesNotExist:
            return Response(response.FILE_NOT_EXISTS)

        return Response(response.FILE_DEL_SUCCESS)

    @method_decorator(request_log(level='DEBUG'))
    def download(self, request, **kwargs):
        """下载文件"""
        try:
            if kwargs.get('pk'):
                fileObject = models.ModelWithFileField.objects.get(id=kwargs['pk'])
                filename = fileObject.name
                filepath = MEDIA_ROOT + '/' + str(fileObject.project_id) + '/' + filename
                if not os.path.exists(filepath):
                    return Response( response.FILE_NOT_EXISTS )
                else:
                    fileresponse = FileResponse(open(filepath, 'rb'))
                    fileresponse["Content-Type"] = "application/octet-stream"
                    fileresponse["Content-Disposition"] = "attachment;filename={}".format(filename)
                    return fileresponse
            else:
                return Response(response.KEY_MISS)
        except ObjectDoesNotExist:
            return Response(response.FILE_DOWNLOAD_FAIL)


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
            return Response(response.PROJECT_EXISTS)
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
        resp = {
            "msg": debug.resp,
            "success": True,
            "code": "0001"
        }
        return Response(resp)

    @method_decorator(request_log(level='INFO'))
    def delete(self, request, **kwargs):
        try:
            if kwargs.get('pk'):  # 单个删除
                models.Pycode.objects.get(id=kwargs['pk']).delete()
            else:
                for content in request.data:
                    models.Pycode.objects.get(id=content['id']).delete()

        except ObjectDoesNotExist:
            return Response(response.FILE_NOT_EXISTS)

        return Response(response.FILE_DEL_SUCCESS)