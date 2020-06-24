from django.shortcuts import render, reverse,HttpResponse
from app01 import models
from django.http import JsonResponse
from app01.forms.file import FileModelFOrm, FolderModelFOrm
from utils.tencent.cos import delete_file, delete_file_list, get_cos_credential
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.encoding import escape_uri_path



def file(request, project_id):
    """文件列表"""
    parent_obj = None
    folder_id = request.GET.get('folder', '')
    if folder_id.isdecimal():
        parent_obj = models.FileRepository.objects.filter(id=int(folder_id), file_type=2,
                                                          project=request.userInfo.project).first()
    if request.method == "GET":
        # 文件导航条目录列表
        breadcrumb_list = []
        parent = parent_obj
        while parent:
            breadcrumb_list.insert(0, {'id': parent.id, 'name': parent.name})
            parent = parent.parent_file

        queryset = models.FileRepository.objects.filter(project=request.userInfo.project)
        if parent_obj:
            # 存在父目录 找到该目录所有子目录
            file_obj_list = queryset.filter(parent_file=parent_obj).order_by('-file_type')
        else:
            # 不存在父目录（根目录） 找到根目录所有的子目录
            file_obj_list = queryset.filter(parent_file__isnull=True).order_by('-file_type')

        form = FolderModelFOrm(request, parent_obj)
        return render(request, 'file.html',
                      {'form': form, 'file_obj_list': file_obj_list, 'breadcrumb_list': breadcrumb_list,
                       'folder_obj': parent_obj})

    # 新建文件夹 && 修改文件夹
    fid = request.POST.get('fid', '')
    edit_obj = None
    if fid.isdecimal():
        edit_obj = models.FileRepository.objects.filter(id=int(fid), file_type=2,
                                                        project=request.userInfo.project).first()
    if edit_obj:
        # 修改文件夹
        form = FolderModelFOrm(request, parent_obj, data=request.POST, instance=edit_obj)
    else:
        # 新建文件夹
        form = FolderModelFOrm(request, parent_obj, data=request.POST)
    if form.is_valid():
        form.instance.project = request.userInfo.project
        form.instance.file_type = 2
        form.instance.update_user = request.userInfo.user
        form.instance.parent_file = parent_obj
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def file_delete(request, project_id):
    fid = request.GET.get('fid')
    # 删除数据库中的文件及文件夹 级联删除
    del_obj = models.FileRepository.objects.filter(id=fid, project_id=project_id).first()
    if del_obj.file_type == 1:
        # 删除文件 并将存储空间进行更新
        request.userInfo.project.use_space -= del_obj.file_size
        request.userInfo.project.save()
        # 删除cos文件
        delete_file(bucket_name=request.userInfo.project.bucket,
                    bucket_region=request.userInfo.project.region,
                    key=del_obj.key)
    else:
        # 删除文件夹 total_size统计文件下子文件的大小 key_list 保存文件下所有子文件的cos文件名
        total_size = 0
        key_list = []
        folder_obj_list = [del_obj, ]
        for folder_obj in folder_obj_list:
            child_list = models.FileRepository.objects.filter(project=request.userInfo.project, parent_file=folder_obj)
            for child in child_list:
                if child.file_type == 2:
                    # 文件夹
                    folder_obj_list.append(child)
                else:
                    # 文件
                    total_size += child.file_size
                    key_list.append({'Key': child.key})
        # 删除cos中 文件夹下所有的文件
        if key_list:
            delete_file_list(bucket_name=request.userInfo.project.bucket,
                             bucket_region=request.userInfo.project.region,
                             key_list=key_list)
        if total_size:
            request.userInfo.project.use_space -= total_size
            request.userInfo.project.save()
    # 删除数据库所有的文件信息
    del_obj.delete()
    return JsonResponse({'status': True})


@csrf_exempt
def cos_credential(request, project_id):
    """
    1.验证文件大小限制（单文件大小(5M)限制，总文件大小(2G)限制）
    2.获取cos临时秘钥
    """
    per_file_size_limit = request.userInfo.price_policy.per_file_size * 1024 * 1024
    project_space_limit = request.userInfo.price_policy.project_space * 1024 * 1024 * 1024
    use_space = request.userInfo.project.use_space
    file_list = json.loads(request.body.decode('utf-8'))
    total_size = 0

    for file in file_list:
        if file['size'] > per_file_size_limit:
            err_msg = '单文件超出限制（{}M）\n 文件{}'.format(request.userInfo.price_policy.per_file_size, file['name'])
            return JsonResponse({'status': False, 'error': err_msg})
        total_size += file['size']
    if use_space + total_size > project_space_limit:
        err_msg = "项目空间超出限制（{}G）".format(request.userInfo.price_policy.project_space)
        return JsonResponse({'status': False, 'error': err_msg})
    result_dict = get_cos_credential(bucket_name=request.userInfo.project.bucket,
                                     bucket_region=request.userInfo.project.region)
    return JsonResponse({'status': True, 'data': result_dict})


@csrf_exempt
def file_post(request, project_id):
    """
    校验前端上传的数据
   'name' , 'size': , 'key', 'parent', 'etag' , 'file_path'
    """
    print(request.POST)
    form = FileModelFOrm(request, data=request.POST)
    if form.is_valid():
        data_dict = form.cleaned_data
        data_dict.pop('etag')
        data_dict.update({'project': request.userInfo.project, 'file_type': 1, 'update_user': request.userInfo.user})
        instance = models.FileRepository.objects.create(**data_dict)
        # 更新文件空间
        request.userInfo.project.use_space += data_dict['file_size']
        result = {
            'id': instance.id,
            'name': instance.name,
            'file_size': instance.file_size,
            'username': instance.update_user.username,
            'datetime': instance.update_time,
            'url': reverse('app01:file_download', kwargs={"project_id": project_id, 'file_id': instance.id})
        }
        return JsonResponse({'status': True, 'data': result})

    return JsonResponse({'status': False})


def file_download(request, project_id, file_id):
    import requests
    file_obj = models.FileRepository.objects.filter(project_id=project_id, id=file_id,
                                                    update_user=request.userInfo.user).first()

    print(file_obj.file_path)
    data = requests.get(file_obj.file_path).content
    response = HttpResponse(data)
    response['Content-Type'] = 'application/octet-stream'
    print(file_obj.name)

    response['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(file_obj.name))
    return response
