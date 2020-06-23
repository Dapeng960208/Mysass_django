from django import forms
from app01 import models
from app01.forms.bootstrap import BootstrapForm
from django.core.exceptions import ValidationError
from utils.tencent.cos import check_file
from qcloud_cos.cos_exception import CosServiceError


class FolderModelFOrm(BootstrapForm, forms.ModelForm):
    class Meta:
        model = models.FileRepository
        fields = ['name']

    def __init__(self, request, parent_obj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_obj = parent_obj

    def clean_name(self):
        """验证同一目录下文件夹是否重名"""
        name = self.cleaned_data['name']
        queryset = models.FileRepository.objects.filter(file_type=2, name=name,
                                                        project=self.request.userInfo.project)
        if self.parent_obj:
            exists = queryset.filter(parent_file=self.parent_obj).exists()
        else:
            exists = queryset.filter(parent_file__isnull=True).exists()
        if exists:
            raise ValidationError('文件夹已存在')
        return name


class FileModelFOrm(BootstrapForm, forms.ModelForm):
    etag = forms.CharField(label='Etag')

    class Meta:
        model = models.FileRepository
        exclude = ['project', 'file_type', 'update_user', 'update_time']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_file_path(self):
        return "https://{}".format(self.cleaned_data['file_path'])

    def clean(self):
        key = self.cleaned_data['key']
        etag = self.cleaned_data['etag']
        size = self.cleaned_data['file_size']
        print('parent_file', self.cleaned_data['parent_file'])
        # 向cos校验文件是否合法
        if not key or not etag:
            return self.cleaned_data
        try:
            data = check_file(
                bucket_name=self.request.userInfo.project.bucket,
                bucket_region=self.request.userInfo.project.region,
                key=key
            )
            print(data)
        except CosServiceError as e:
            self.add_error('key', '文件未上传成功')
            return self.cleaned_data
        cos_etag = data['ETag']
        cos_size = int(data['Content-Length'])
        if etag != cos_etag:
            self.add_error('etag', 'ETag错误')
            print('1')
        if size != cos_size:
            self.add_error('file_size', '文件大小错误')
            print('2')
        return self.cleaned_data
