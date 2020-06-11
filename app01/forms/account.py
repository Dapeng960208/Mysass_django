from django import forms
from app01 import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from utils.tencent.sms import send_sms_single
from django_redis import get_redis_connection
from utils.encrypt import md5
from app01.forms.bootstrap import BootstrapForm
import random


class RegisterModelForm(BootstrapForm, forms.ModelForm):
    telephone = forms.CharField(label='手机号', validators=[RegexValidator(r'(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    password = forms.CharField(label='密码',
                               min_length=8,
                               max_length=64,
                               error_messages={
                                   'min_length': '密码最小长度为8',
                                   'max_length': '密码最大长度为64'},
                               widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='确认密码',
                                       min_length=8,
                                       max_length=64,
                                       error_messages={
                                           'min_length': '密码最小长度为8',
                                           'max_length': '密码最大长度为64'},
                                       widget=forms.PasswordInput())
    code = forms.CharField(label='验证码', widget=forms.TextInput())

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'password', 'confirm_password', 'telephone']

    def clean_username(self):
        username = self.cleaned_data['username']
        if models.UserInfo.objects.filter(username=username).exists():
            raise ValidationError('用户名已存在')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if models.UserInfo.objects.filter(email=email).exists():
            raise ValidationError('邮箱已存在')
        return email

    def clean_password(self):
        pwd = self.cleaned_data['password']
        return md5(pwd)

    def clean_confirm_password(self):
        pwd = self.cleaned_data['password']
        confirm_password = md5(self.cleaned_data['confirm_password'])
        if pwd != confirm_password:
            raise ValidationError('两次密码不一致')
        return confirm_password

    def clean_telephone(self):
        telephone = self.cleaned_data['telephone']
        if models.UserInfo.objects.filter(telephone=telephone).exists():
            raise ValidationError('手机号已存在')
        return telephone

    def clean_code(self):
        code = self.cleaned_data['code']
        telephone = self.cleaned_data.get('telephone')
        if not telephone:
            return code
        conn = get_redis_connection()
        redis_code = conn.get(telephone)
        if not redis_code:
            raise ValidationError('验证码失效或未发送，请重新发送')
        # 存在redis的数据为bytes，需要解码为’utf-8'再进行验证
        str_redis_code = redis_code.decode('utf-8')
        if code.strip('') != str_redis_code:
            raise ValidationError('验证码错误或失效，请重新输入')
        return code


class AuthPhoneForm(forms.Form):
    telephone = forms.CharField(label='手机号', validators=[RegexValidator(r'(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_telephone(self):
        """
        手机号码校验的钩子
        验证手机号的的合法性：11位不为空字符串
        并将验证码写入redis中
        """
        telephone = self.cleaned_data['telephone']
        exists = models.UserInfo.objects.filter(telephone=telephone).exists()
        tpl = self.request.GET['tpl']
        template_id = settings.TENCENT_TEMPLATES.get(tpl)
        code = random.randrange(100000, 999999)

        sms = {}

        if not template_id:
            raise ValidationError('短信模板错误')
        if tpl == 'login':
            if not exists:
                raise ValidationError('手机号不存在')

            # sms = send_sms_single(telephone, template_id, [code,])
            sms['result'] = 0
        elif tpl == 'register':
            if exists:
                raise ValidationError('手机号已存在')
            # sms = send_sms_single(telephone, template_id, [code, 1])
            # print(code, sms['result'], sms['errmsg'])
            sms['result'] = 0
        if sms['result'] != 0:
            raise ValidationError('短信发送失败,{}'.format(sms['errmsg']))
        # 将短信验证码写入redis，超时时间60s
        conn = get_redis_connection()
        conn.set(telephone, code, ex=60)
        print(code)
        return telephone


class LoginSmsForm(BootstrapForm, forms.Form):
    telephone = forms.CharField(label='手机号',
                                validators=[RegexValidator(r'(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    code = forms.CharField(label='验证码', widget=forms.TextInput())

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        telephone_obj = models.UserInfo.objects.filter(telephone=telephone).first()
        if not telephone_obj:
            raise ValidationError('手机号未注册')
        return telephone_obj

    def clean_code(self):
        code = self.cleaned_data['code']
        telephone_obj = self.cleaned_data.get('telephone')
        if not telephone_obj:
            return code
        conn = get_redis_connection()
        redis_code = conn.get(telephone_obj.telephone)

        if not redis_code:
            raise ValidationError('验证码失效或未发送，请重新发送')
        # 存在redis的数据为bytes，需要解码为’utf-8'再进行验证
        str_redis_code = redis_code.decode('utf-8')
        if code.strip('') != str_redis_code:
            raise ValidationError('验证码错误或失效，请重新输入')
        return code


class LoginForm(BootstrapForm, forms.Form):
    telephone_or_email = forms.CharField(label='手机号或者邮箱',
                                         validators=[RegexValidator(r'(1[3|4|5|6|7|8|9])\d{9}|^(\w)+(.\w+)*@('
                                                                    r'\w)+((.\w+)+)$', '手机号或者邮箱格式错误'), ])
    password = forms.CharField(label='密码',
                               widget=forms.PasswordInput(render_value=True))
    code = forms.CharField(label='图片验证码')

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_telephone_or_email(self):
        telephone_or_email = self.cleaned_data['telephone_or_email'].strip()
        return telephone_or_email

    def clean_password(self):
        pwd = self.cleaned_data['password']
        return md5(pwd)

    def clean_code(self):
        code = self.cleaned_data['code']
        session_code = self.request.session.get('image_code')
        if not session_code:
            raise ValidationError('验证码已过期，请重新获取')

        if code.strip().upper() != session_code.strip().upper():
            raise ValidationError('验证码输入错误')
        return code
