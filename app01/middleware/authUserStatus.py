from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.conf import settings
from app01 import models
import datetime


class UserInfo(object):
    def __init__(self):
        """封装一个对象，便于取值理解"""
        self.user = None
        self.price_policy = None
        self.project = None


class AuthUserStatusMiddleware(MiddlewareMixin):

    def process_request(self, request):
        """用户已登录，保存用户的信息"""
        request.userInfo = UserInfo()
        user_id = request.session.get('user_id', 0)
        user_obj = models.UserInfo.objects.filter(id=user_id).first()
        request.userInfo.user = user_obj

        """获取用户当前url,检查当前url是否在网址白名单之中，再校验用户是否登录"""
        if request.path_info in settings.WHITE_REGEX_URL_LIST:
            return
        if not request.userInfo.user:
            return redirect('app01:login')

        """登录成功后,获取用户当前的额度"""
        # 获取用户最近一次的交易记录 没有交易取得就是免费的额度
        _obj = models.Transaction.objects.filter(user=user_obj, status=2).order_by('-id').first()
        # 判断用户会员是否过期
        currrnt_date = datetime.datetime.now()
        # 用户会员过期
        if _obj.end_time and _obj.end_time < currrnt_date:
            _obj = models.Transaction.objects.filter(user=user_obj, status=2, price_policy=1).first()

        request.userInfo.price_policy = _obj.price_policy

    def process_view(self, request, view, args, kwargs):
        if not request.path_info.startswith('/manage/'):
            return
        project_id = kwargs.get('project_id')
        project_obj = models.Project.objects.filter(creator=request.userInfo.user, id=project_id).first()
        if project_obj:
            request.userInfo.project = project_obj
            return
        project_user_obj = models.ProjectUser.objects.filter(user=request.userInfo.user, project_id=project_id).first()
        if project_user_obj:
            request.userInfo.project = project_user_obj.obj
            return
        return redirect('app01:project_list')
