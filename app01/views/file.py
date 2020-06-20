from django.shortcuts import render, redirect, reverse, HttpResponse
from app01 import models
from django.http import JsonResponse
from app01.forms.file import FileModelFOrm
from utils.tencent.cos import delete_file, delete_file_list


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

        form = FileModelFOrm(request, parent_obj)
        return render(request, 'file.html',
                      {'form': form, 'file_obj_list': file_obj_list, 'breadcrumb_list': breadcrumb_list})

    # 新建文件夹 && 修改文件夹
    fid = request.POST.get('fid', '')
    edit_obj = None
    if fid.isdecimal():
        edit_obj = models.FileRepository.objects.filter(id=int(fid), file_type=2,
                                                        project=request.userInfo.project).first()
    if edit_obj:
        # 修改文件夹
        form = FileModelFOrm(request, parent_obj, data=request.POST, instance=edit_obj)
    else:
        # 新建文件夹
        form = FileModelFOrm(request, parent_obj, data=request.POST)
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
                    key_list.appen({'Key': child.key})
        # 删除cos中 文件夹下所有的文件
        if key_list:
            delete_file_list(bucket_name=request.userInfo.project.bucket,
                             bucket_region=request.userInfo.project.region,
                             key_list=key_list)
        if total_size:
            request.userInfo.project.use_space -= total_size
            request.userInfo.project.save()
    #删除数据库所有的文件信息
    del_obj.delete()
    return JsonResponse({'status': True})
