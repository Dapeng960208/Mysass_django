from django.shortcuts import render, redirect
from utils.tencent.cos import delete_bucket
from app01 import models


def settings(request, project_id):
    return render(request, 'settings.html')


def settings_delete(request, project_id):
    if request.method == "GET":
        return render(request, 'settings_delete.html')
    project_name = request.POST.get('project_name').strip('')
    if not project_name or project_name != request.userInfo.project.name:
        return render(request, 'settings_delete.html', {"error": '项目不存在'})
    if request.userInfo.user != request.userInfo.project.creator:
        return render(request, 'settings_delete.html', {'error': "只有项目创建者可删除项目"})
    # 删除项目
    # 1.先删除桶（先删除桶所有的文件和文件碎片，再删除桶）
    # 2.再删除数据库
    delete_bucket(bucket_name=request.userInfo.project.bucket, bucket_region=request.userInfo.project.region)
    models.Project.objects.filter(id=project_id).delete()
    return redirect("app01:project_list")
