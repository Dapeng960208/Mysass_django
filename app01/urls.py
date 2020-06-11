"""app01 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from app01.views import account, project, manage, wiki

urlpatterns = [
    url(r'^register/$', account.register, name='register'),
    url(r'^send/sms/$', account.send_sms, name='send_sms'),
    url(r'^login/sms/$', account.login_sms, name='login_sms'),
    url(r'^login/$', account.login, name='login'),
    url(r'^logout/$', account.logout, name='logout'),
    url(r'^index/', account.index, name='index'),
    url(r'^image/code/$', account.image_code, name='image_code'),

    # 项目列表路由
    url(r'^project/list/', project.project_list, name='project_list'),
    url(r'^project/star/', project.project_star, name='project_star'),

    # 项目管理路由
    url(r'^manage/(?P<project_id>\d+)/dashboard/$', manage.dashboard, name='dashboard'),

    url(r'^manage/(?P<project_id>\d+)/issues/$', manage.issues, name='issues'),

    url(r'^manage/(?P<project_id>\d+)/statistics/$', manage.statistics, name='statistics'),

    url(r'^manage/(?P<project_id>\d+)/file/$', manage.file, name='file'),

    url(r'^manage/(?P<project_id>\d+)/wiki/$', wiki.wiki, name='wiki'),
    url(r'^manage/(?P<project_id>\d+)/wiki/add/$', wiki.wiki_add, name='wiki_add'),
    url(r'^manage/(?P<project_id>\d+)/wiki/delete//(?P<wiki_id>\d+)/$', wiki.wiki_delete, name='wiki_delete'),
    url(r'^manage/(?P<project_id>\d+)/wiki/edit//(?P<wiki_id>\d+)/$', wiki.wiki_edit, name='wiki_edit'),
    url(r'^manage/(?P<project_id>\d+)/wiki/catalog/$', wiki.wiki_catalog, name='wiki_catalog'),
    url(r'^manage/(?P<project_id>\d+)/wiki/upload/$', wiki.wiki_upload, name='wiki_upload'),
    url(r'^manage/(?P<project_id>\d+)/settings/$', manage.settings, name='settings'),
]
