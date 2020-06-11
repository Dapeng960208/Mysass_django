from django.shortcuts import render, redirect, reverse, HttpResponse
from app01.forms.wiki import WikiModelForm
from app01 import models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.tencent.cos import upload_file
from utils.encrypt import uid


def wiki(request, project_id):
    """wiki首页展示"""
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, 'wiki.html')
    wiki_obj = models.Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
    return render(request, 'wiki.html', {'wiki_obj': wiki_obj})


def wiki_add(request, project_id):
    if request.method == "GET":
        form = WikiModelForm(request)
        return render(request, 'wiki_form.html', {'form': form})
    form = WikiModelForm(request, data=request.POST)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth += 1
        else:
            form.instance.depth = 1
        form.instance.project = request.userInfo.project
        form.save()
        url = reverse('app01:wiki', kwargs={'project_id': project_id})
        return redirect(url)
    return render(request, 'wiki_form.html', {'form': form})


def wiki_catalog(request, project_id):
    data = models.Wiki.objects.filter(project_id=project_id).values('id', 'title', 'parent_id').order_by('depth', 'id')
    # return JsonResponse({'data': data, 'status': True})
    # 上面的代码会报错 TypeError: Object of type 'QuerySet' is not JSON serializable
    # 查询的结果为QuerySet类型，无法json.dumps(),需要转为python常见格式list
    return JsonResponse({'data': list(data), 'status': True})


def wiki_delete(request, project_id, wiki_id):
    models.Wiki.objects.filter(id=wiki_id, project_id=project_id).delete()
    url = reverse('app01:wiki', kwargs={'project_id': project_id})
    return redirect(url)


def wiki_edit(request, project_id, wiki_id):
    edit_wiki_obj = models.Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
    if not edit_wiki_obj:
        url = reverse('app01:wiki', kwargs={'project_id': project_id})
        return redirect(url)
    form = WikiModelForm(request, instance=edit_wiki_obj)
    return render(request, 'wiki_form.html', {'form': form})


@csrf_exempt
def wiki_upload(request, project_id):
    result = {
        'success': 0,
        'message': None,
        'url': None
    }
    #print(request.FILES)
    #<MultiValueDict: {'editormd-image-file': [<InMemoryUploadedFile: x战警二.jpeg (image/jpeg)>]}>
    image_obj = request.FILES.get('editormd-image-file')
    if not image_obj:
        result['message'] = "文件不存在"
        return JsonResponse(result)
    # key文件名 ext文件后缀名
    ext = image_obj.name.rsplit('.')[-1]
    key = "{}.{}".format(uid(request.userInfo.user.telephone), ext)
    image_url = upload_file(
        request.userInfo.project.bucket,
        request.userInfo.project.region,
        image_obj,
        key
    )
    print(image_url)
    result['success'] = 1
    result['url'] = image_url
    return JsonResponse(result)
