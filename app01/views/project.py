from django.shortcuts import render, HttpResponse, redirect
from app01.forms.project import ProjectModelForm
from django.http import JsonResponse
from app01 import models
from utils.tencent.cos import create_bucket
import time


def project_list(request):
    """项目列表"""
    if request.method == "GET":
        """
        GET请求查看项目
        1.我创建的项目
        2.我参与的项目
        3.提取星标的项目
        """
        project_dic = {'star': [], 'my': [], 'join': []}
        # 查询我创建的项目
        my_project_list = models.Project.objects.filter(creator=request.userInfo.user)
        for item in my_project_list:
            if item.star:
                project_dic['star'].append(item)
            else:
                project_dic['my'].append(item)
        # 查询我参与的项目 注意列表里存储的是项目对象
        # 所以 item = pro_user.project （project对象）
        join_project_list = models.ProjectUser.objects.filter(user=request.userInfo.user)
        for pro_user in join_project_list:
            if pro_user.star:
                project_dic['star'].append(pro_user.project)
            else:
                project_dic['join'].append(pro_user.project)
        form = ProjectModelForm(request)
        return render(request, 'project_list.html', {'form': form, 'project_dic': project_dic})
    form = ProjectModelForm(request, data=request.POST)
    if form.is_valid():
        user_telephone = request.userInfo.user.telephone
        timestamp = str(int(time.time()))
        # 验证通过 项目名，颜色 ，描述 创建者 并给每个用于创建一个桶来存储文件照片
        bucket_name = '{}-{}-1301997034'.format(user_telephone, timestamp)
        bucket_region = 'ap-beijing'
        create_bucket(bucket_name=bucket_name, bucket_region=bucket_region)
        form.instance.bucket = bucket_name
        form.instance.region = bucket_region
        form.instance.creator = request.userInfo.user
        form.save()
        return JsonResponse({'status': True, 'data': '/project/list/'})
    return JsonResponse({'status': False, 'error': form.errors})


def project_star(request):
    project_type = request.GET["project_type"]
    project_id = request.GET["project_id"]
    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.userInfo.user).update(star=True)
    if project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.userInfo.user).update(star=True)
    if project_type == 'star':
        if models.Project.objects.filter(id=project_id, creator=request.userInfo.user).exists():
            models.Project.objects.filter(id=project_id, creator=request.userInfo.user).update(star=False)
        else:
            models.ProjectUser.objects.filter(project_id=project_id, user=request.userInfo.user).update(star=False)
    return JsonResponse({'status': True})
