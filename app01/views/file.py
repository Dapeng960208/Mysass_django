from django.shortcuts import render, redirect, reverse, HttpResponse
from app01 import models
from django.http import JsonResponse
from app01.forms.file import FileModelFOrm


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
