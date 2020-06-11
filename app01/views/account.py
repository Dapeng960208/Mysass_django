from django.shortcuts import render, HttpResponse, redirect
from app01.forms.account import RegisterModelForm, AuthPhoneForm, LoginSmsForm, LoginForm
from utils.tencent.sms import send_sms_single
from django.db.models import Q
from django.http import JsonResponse
from app01 import models
import uuid
import datetime


def register(request):
    """注册"""

    if request.method == 'GET':
        form = RegisterModelForm()
        return render(request, 'register.html', {'form': form})
    else:
        form = RegisterModelForm(data=request.POST)
        if form.is_valid():
            """注册成功，创建用户交易记录，默认创建免费版用户交易"""
            user_obj = form.save()
            price_policy = models.PricePolicy.objects.filter(category=1, title='免费版').first()
            models.Transaction.objects.create(
                status=2,
                order=str(uuid.uuid4()),
                user=user_obj,
                price_policy=price_policy,
                count=0,
                price=0,
                start_time=datetime.datetime.now(),
            )
            return JsonResponse({'status': True, 'data': '/login/'})
        else:
            # print(form.errors.as_json())
            return JsonResponse({'status': False, 'error': form.errors})


def send_sms(request):
    """发送短信"""
    auth_telphone = AuthPhoneForm(request, data=request.GET)
    if auth_telphone.is_valid():
        return JsonResponse({'status': True})
    else:
        return JsonResponse({'status': False, 'error': auth_telphone.errors})


def login_sms(request):
    if request.method == 'GET':
        form = LoginSmsForm()
        return render(request, 'login_sms.html', {'form': form})
    form = LoginSmsForm(data=request.POST)
    if form.is_valid():
        # 登陆成功 用session保存用户信息
        telephone_obj = form.cleaned_data['telephone']
        user_obj = models.UserInfo.objects.filter(telephone=telephone_obj.telephone).first()
        request.session['user_id'] = user_obj.id
        request.session.set_expiry(60 * 60 * 24)
        return JsonResponse({"status": True, 'data': "/index/"})

    return JsonResponse({"status": False, 'error': form.errors})


def login(request):
    if request.method == 'GET':
        form = LoginForm(request)
        return render(request, 'login.html', {'form': form})
    form = LoginForm(request, data=request.POST)
    if form.is_valid():
        telephone_or_email = form.cleaned_data['telephone_or_email']
        password = form.cleaned_data['password']
        telephone_or_email_obj = models.UserInfo.objects.filter(
            Q(telephone=telephone_or_email) | Q(email=telephone_or_email)).filter(password=password).first()
        if telephone_or_email_obj:
            # 登陆成功 用session保存用户信息
            request.session['user_id'] = telephone_or_email_obj.id
            request.session.set_expiry(60 * 60 * 24)
            return redirect('app01:index')
        else:
            form.add_error('telephone_or_email', '用户名或密码错误')
    return render(request, 'login.html', {'form': form})


def index(request):
    return render(request, 'index.html')


def image_code(request):
    from io import BytesIO
    from utils.imageCode import check_code
    img, code = check_code()
    print(code)

    # 将图片对应的验证码，保存在session中
    # session 默认失效时间两周,set_expiry(60)修改session过期时间为60s
    request.session['image_code'] = code
    request.session.set_expiry(60)
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())


def logout(request):
    request.session.flush()
    return redirect('app01:index')
